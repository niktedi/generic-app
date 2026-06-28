# ---- Stage 1: build dependencies ----
# Multi-stage keeps the final image small: build tools stay in the
# builder stage and never ship to production.
FROM python:3.14-slim AS builder

WORKDIR /build

# requirements.txt is exported from uv (runtime deps only):
#   uv export --no-dev --no-hashes -o requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ----
FROM python:3.14-slim

# Non-root user. Running as root in a container is a security anti-pattern;
# k8s securityContext will also enforce this in Phase 4.
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/ ./app/
# Alembic migrations ship in the image so the schema can be applied from a
# container (a k8s Job in Phase 4) via `alembic upgrade head`.
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# APP_VERSION is overridden at build time (CI passes the git sha/tag).
ENV APP_VERSION=dev \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8000

# Container-level healthcheck (independent of k8s probes; useful with plain docker).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
