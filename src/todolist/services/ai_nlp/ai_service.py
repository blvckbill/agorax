# src/todolist/services/ai_service.py
import os
import json
import time
import asyncio
import logging
from typing import Optional

import httpx
import redis.asyncio as aioredis
from src.todolist.config import HF_API_TOKEN, HF_API_URL, HF_MODEL, REDIS_HOST, REDIS_PORT

# local model fallback
try:
    from transformers import pipeline
    _HAS_TRANSFORMERS = True
except Exception:
    _HAS_TRANSFORMERS = False

log = logging.getLogger(__name__)


REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CACHE_TTL = 30      # seconds
RATE_LIMIT_PER_MIN = 30  # requests per user/min
CONCURRENCY_LIMIT = 8     # concurrent inferences
REQUEST_TIMEOUT = 3.0      # seconds for external call
RETRY_ATTEMPTS = 2
RETRY_BACKOFF = 0.5        # base seconds


_redis: Optional[aioredis.Redis] = None
_http_client: Optional[httpx.AsyncClient] = None
_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

# ---------- Prompt template ----------
PROMPT_SYSTEM = (
    "You are a helpful autocomplete assistant that suggests a short, single-line completion "
    "for partially typed task titles. Return only the suggested completion text (no explanation). "
    "Keep it concise (2-8 words), actionable, and in the same language as the input. "
    "If the input is empty or nonsense, return an empty string."
)

PROMPT_EXAMPLES = """
EXAMPLE
Partial: "Buy gro"
Context: "Shopping"
=> "ceries for the week"

EXAMPLE
Partial: "Write unit"
Context: "Backend"
=> "tests for login API"
"""

def _build_full_prompt(prefix: str, context: Optional[str] = None) -> str:
    parts = [PROMPT_SYSTEM.strip(), "", PROMPT_EXAMPLES.strip(), ""]
    if context:
        parts.append(f'Context: "{context.strip()}"')
    parts.append(f'Partial: "{prefix.strip()}"')
    parts.append("Return only the completion.")
    return "\n".join(parts)

# local pipeline (blocking) - only initialized if transformers available
_local_pipeline = None
if _HAS_TRANSFORMERS:
    try:
        _local_pipeline = pipeline("text-generation", model=HF_MODEL, device=-1)
    except Exception:
        _local_pipeline = None


async def _get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

def _cache_key(prefix: str, context: Optional[str] = None) -> str:
    # include context in key if provided
    key = f"{prefix.strip().lower()}"
    if context:
        key += f":{context.strip().lower()}"
    # keep key compact
    return "ai:suggest:" + str(abs(hash(key)))

async def _init_http_client():
    global _http_client
    if _http_client is None:
        headers = {}
        if HF_API_TOKEN:
            headers["Authorization"] = f"Bearer {HF_API_TOKEN}"
        # set short timeout per request; top-level wait_for will also apply
        _http_client = httpx.AsyncClient(headers=headers, timeout=REQUEST_TIMEOUT)
    return _http_client

async def _rate_limit_ok(user_id: Optional[str]) -> bool:
    """Simple per-user rate limiting using Redis counter in a 60s window."""
    if user_id is None:
        return True
    redis = await _get_redis()
    key = f"ai:rl:{user_id}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)
    if current > RATE_LIMIT_PER_MIN:
        return False
    return True

async def _get_cached(prefix: str, context: Optional[str]) -> Optional[str]:
    redis = await _get_redis()
    return await redis.get(_cache_key(prefix, context))

async def _set_cache(prefix: str, context: Optional[str], suggestion: str):
    redis = await _get_redis()
    await redis.setex(_cache_key(prefix, context), CACHE_TTL, suggestion)

# ---------- external inference call ----------
async def _call_hf_inference(prompt: str) -> str:
    """
    Call Hugging Face Inference API (or custom HF_API_URL) and return the generated completion string.
    The prompt already contains SYSTEM+EXAMPLES+Partial.
    """
    client = await _init_http_client()

    # If HF_API_URL is provided, assume it's a full inference endpoint accepting {"inputs": prompt, ...}
    if HF_API_URL:
        url = HF_API_URL
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 12, "temperature": 0.6}}
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    else:
        # standard HF Inference endpoint for model name
        model_url = f"https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 12, "temperature": 0.6}}
        resp = await client.post(model_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # parse common HF formats
    text = ""
    try:
        if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
            text = data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            text = data["generated_text"]
        elif isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"HF inference error: {data['error']}")
        else:
            # fallback: try to stringify
            text = str(data)
    except Exception:
        text = str(data)

    # If returned text contains the prompt prefix, strip it.
    if text.startswith(prompt):
        return text[len(prompt):].strip()
    return text.strip()

# local fallback (blocking)
def _local_generate(prompt: str) -> str:
    if _local_pipeline is None:
        raise RuntimeError("Local pipeline not available")
    out = _local_pipeline(prompt, max_new_tokens=12, do_sample=True, top_p=0.9, temperature=0.6)
    text = out[0]["generated_text"]
    if text.startswith(prompt):
        return text[len(prompt):].strip()
    return text.strip()

# public API
async def suggest_completion(prefix: str, user_id: Optional[str] = None, context: Optional[str] = None) -> str:
    """
    Robust suggestion:
      - rate limit per user
      - cache lookup
      - concurrency limit
      - call HF inference with retries + backoff
      - fallback to local pipeline if external fails
      - cache and return suggestion
    """
    prefix = (prefix or "").strip()
    if not prefix:
        return ""

    # rate-limit
    ok = await _rate_limit_ok(str(user_id) if user_id else None)
    if not ok:
        log.warning("rate limit exceeded for user=%s", user_id)
        return ""  # endpoint can react with 429 if desired

    # cache
    cached = await _get_cached(prefix, context)
    if cached:
        return cached

    # concurrency limit
    async with _semaphore:
        # build prompt (includes examples and optional context)
        full_prompt = _build_full_prompt(prefix, context=context)

        last_exc = None
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                suggestion = await asyncio.wait_for(_call_hf_inference(full_prompt), timeout=REQUEST_TIMEOUT)
                # post-process: trim and cache
                suggestion = _postprocess_suggestion(prefix, suggestion)
                await _set_cache(prefix, context, suggestion)
                return suggestion
            except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError) as exc:
                last_exc = exc
                backoff = RETRY_BACKOFF * (2 ** (attempt - 1))
                log.warning("HF attempt %d failed: %s; backing off %.2fs", attempt, exc, backoff)
                await asyncio.sleep(backoff)
            except Exception as exc:
                last_exc = exc
                log.exception("Unexpected error calling HF inference: %s", exc)
                break

        # external failed — fallback to local pipeline if available
        if _local_pipeline:
            try:
                suggestion = await asyncio.get_event_loop().run_in_executor(None, lambda: _local_generate(full_prompt))
                suggestion = _postprocess_suggestion(prefix, suggestion)
                await _set_cache(prefix, context, suggestion)
                return suggestion
            except Exception as exc:
                last_exc = exc
                log.exception("Local model fallback failed: %s", exc)

    log.error("AI suggestion failed for prefix=%r user=%s last_exc=%s", prefix, user_id, last_exc)
    return ""

# post-processing
import re

_MAX_WORDS = 8
def _postprocess_suggestion(prefix: str, raw: str) -> str:
    if not raw:
        return ""
    s = raw.replace("\n", " ").strip()
    lower_raw = s.lower()
    lower_pref = prefix.lower().strip()
    if lower_pref and lower_raw.startswith(lower_pref):
        s = s[len(prefix):].lstrip()
    s = re.sub(r'^[\s\-\:\,\.\u2014]+', '', s)
    parts = s.split()
    if len(parts) > _MAX_WORDS:
        parts = parts[:_MAX_WORDS]
    s = " ".join(parts).strip()
    s = s.rstrip(" .,:;!-?")
    return s
