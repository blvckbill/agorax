import os
import asyncio
import logging
import re
from typing import Optional

import redis.asyncio as aioredis
import google.generativeai as genai

from src.todolist.config import (
    REDIS_HOST,
    REDIS_PORT,
    GOOGLE_API_KEY
)

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# -------------------- Config --------------------
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CACHE_TTL = 300
RATE_LIMIT_PER_MIN = 30
CONCURRENCY_LIMIT = 8

_MAX_WORDS = 8
_redis: Optional[aioredis.Redis] = None
_semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

    _model = genai.GenerativeModel(
        model_name="gemini-pro-latest"
    )

else:
    _model = None
    log.warning("⚠️ No GOOGLE_API_KEY found. AI service will run in Offline Mode.")

# -------------------- 🧠 Local Fallback Engine --------------------
LOCAL_KNOWLEDGE = {
    "buy": ["groceries", "milk", "laptop", "tickets"],
    "go": ["to the gym", "to the market", "to work", "home"],
    "call": ["mom", "dad", "the boss", "support"],
    "write": ["report", "code", "email", "essay"],
    "fix": ["bug", "car", "sink", "wifi"],
    "clean": ["room", "house", "car", "kitchen"],
    "pay": ["bills", "rent", "debt"],
}

def _get_local_suggestion(prefix: str) -> str:
    p = prefix.lower()
    for key, options in LOCAL_KNOWLEDGE.items():
        if key in p:
            idx = len(p) % len(options)
            return options[idx]
    
    generics = ["this task", "it later", "asap"]
    return generics[len(p) % len(generics)]

# -------------------- Redis Helpers --------------------
async def _get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis

def _cache_key(prefix: str, context: Optional[str]) -> str:
    # Context (List Title) is now part of the cache key
    base = prefix.strip().lower()
    if context:
        base += f":{context.strip().lower()}"
    return "ai:suggest:" + str(abs(hash(base)))

async def _get_cached(prefix: str, context: Optional[str]) -> Optional[str]:
    try:
        redis = await _get_redis()
        return await redis.get(_cache_key(prefix, context))
    except Exception:
        return None

async def _set_cache(prefix: str, context: Optional[str], value: str):
    try:
        redis = await _get_redis()
        await redis.setex(_cache_key(prefix, context), CACHE_TTL, value)
    except Exception:
        pass

async def _rate_limit_ok(user_id: Optional[str]) -> bool:
    if not user_id:
        return True
    try:
        redis = await _get_redis()
        key = f"ai:rl:{user_id}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        return count <= RATE_LIMIT_PER_MIN
    except Exception:
        return True

# -------------------- Inference Engine (Gemini) --------------------
def _build_smart_prompt(prefix: str, context: Optional[str]) -> str:
    """
    Constructs a context-aware prompt using the List Title.
    """
    list_title = context if context else "General Tasks"
    
    return f"""You are a predictive text assistant for a Todo List App.
Context: User is adding a task to a list named "{list_title}".
Goal: Complete the input text concisely (1-5 words).
Rules:
- Do not repeat the input.
- Be relevant to the list title "{list_title}".
- Output ONLY the completion text.

Examples:
List: Groceries | Input: Buy | Output: milk
List: Work | Input: Email | Output: the manager
List: Gym | Input: Do 10 | Output: pushups
List: {list_title} | Input: {prefix} | Output:"""

async def _generate(prefix: str, context: Optional[str]) -> str:
    # Fallback immediately if no API key is configured
    if not _model:
        return _get_local_suggestion(prefix)

    try:
        loop = asyncio.get_running_loop()
        
        # Build the prompt with context
        prompt = _build_smart_prompt(prefix, context)
        
        # Run blocking API call in executor to keep async loop unblocked
        response = await loop.run_in_executor(
            None, 
            lambda: _model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,
                    temperature=0.3
                )
            )
        )
        
        if response and response.text:
            return response.text.rstrip()
            
    except Exception as e:
        log.warning(f"⚠️ Gemini API failed: {e}")

    # Fallback to Local Engine if Gemini fails
    log.info(f"⚡ Using Local Fallback for: '{prefix}'")
    return _get_local_suggestion(prefix)

# -------------------- Post Processing --------------------
def _postprocess(prefix: str, text: str) -> str:
    if not text:
        return ""
    
    # 1. Basic cleanup
    s = text.replace(prefix, "").strip() # Clean everything first
    s = re.sub(r'[\n\r]', ' ', s)
    s = re.sub(r'^[\-\:\,\.\u2014]+', '', s) # Note: \s is removed from regex
    
    # 2. Limit word count
    words = s.split()
    if len(words) > _MAX_WORDS:
        words = words[:_MAX_WORDS]
    
    final_suggestion = " ".join(words).rstrip(" .,:;!?")

    if not final_suggestion:
        return ""

    # 3. 🧠 Smart Spacing Logic
    # If the user's input (prefix) DOES NOT end in a space...
    # ...and our suggestion DOES NOT start with a space...
    # -> WE MUST ADD A SPACE.
    if not prefix.endswith(" ") and not final_suggestion.startswith(" "):
        return " " + final_suggestion

    return final_suggestion

# -------------------- Public API --------------------
async def suggest_completion(
    prefix: str,
    user_id: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    prefix = (prefix or "").strip()
    # Ignore very short inputs
    if not prefix or len(prefix) < 2:
        return ""

    # Check Rate Limit
    if not await _rate_limit_ok(str(user_id) if user_id else None):
        return ""

    # Check Cache (Cache key includes context!)
    cached = await _get_cached(prefix, context)
    if cached:
        log.info(f"⚡ [CACHE] Hit: '{cached}'")
        return cached

    # Limit concurrency
    async with _semaphore:
        try:
            # Generate suggestion (Context aware)
            text = await _generate(prefix, context)
            
            if not text:
                return ""

            suggestion = _postprocess(prefix, text)
            
            if suggestion:
                # Cache the result
                await _set_cache(prefix, context, suggestion)
            
            return suggestion

        except Exception:
            return ""