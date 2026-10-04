FROM python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml constraints.txt README.md ./
COPY brain_gateway ./brain_gateway

FROM base AS runtime

RUN pip install --no-cache-dir --constraint constraints.txt .
COPY brain ./brain
RUN groupadd --system brain \
    && useradd --system --gid brain --home-dir /nonexistent --shell /usr/sbin/nologin brain \
    && mkdir -p /app/data \
    && chown -R brain:brain /app/data /app/brain/proposals

USER brain:brain

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)" || exit 1

CMD ["uvicorn", "brain_gateway.main:app", "--host", "0.0.0.0", "--port", "8080", "--limit-concurrency", "64", "--no-access-log"]

FROM runtime AS test

USER root
RUN pip install --no-cache-dir --constraint constraints.txt ".[dev]"
COPY Dockerfile compose.yaml ./
COPY tests ./tests
RUN mkdir -p /app/.pytest_cache && chown brain:brain /app/.pytest_cache
USER brain:brain
