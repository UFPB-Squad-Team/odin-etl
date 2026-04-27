# =============================================================
# ODIN-ETL — Dockerfile (multi-stage)
#
# Stage 1 (builder): instala dependências com uv
# Stage 2 (runtime): imagem enxuta, só o necessário para rodar
#
# =============================================================

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock readme.md ./

RUN uv sync --no-dev --frozen

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal36 \
    libgeos-c1v5 \
    libproj25 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

COPY src/     ./src/
COPY config/  ./config/
COPY scripts/ ./scripts/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=America/Recife

RUN useradd --no-create-home --shell /bin/false odin
USER odin

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.jobs.education_jobs" || exit 1
