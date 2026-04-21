FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY . .
