# ---------- builder stage ----------
FROM python:3.11-slim-bullseye AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libffi-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# copy requirements and build wheels for deterministic installs
COPY requirements.txt /src/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
  && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r /src/requirements.txt

# copy source
COPY . /src

# ---------- final stage ----------
FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/home/app/web \
    HOME=/home/app

# runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 libmagic1 netcat ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# create non-root user and app dir
RUN groupadd -r app && useradd -r -g app -d ${APP_HOME} -s /sbin/nologin app \
  && mkdir -p ${APP_HOME} && chown -R app:app ${APP_HOME}

WORKDIR ${APP_HOME}

# install wheels produced in builder stage (faster, deterministic)
COPY --from=builder /wheels /wheels
COPY --from=builder /src/requirements.txt ${APP_HOME}/requirements.txt

RUN pip install --upgrade pip \
  && pip install --no-cache-dir /wheels/* \
  || pip install --no-cache-dir -r ${APP_HOME}/requirements.txt

# copy app source
COPY --chown=app:app . ${APP_HOME}
RUN chmod +x ${APP_HOME}/entrypoint.sh

# use non-root user
USER app

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
