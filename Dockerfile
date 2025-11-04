FROM python:3.12-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Get system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Creating unprivileged application user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Get application dependencies
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Copy application files
COPY app /app/app
COPY pyproject.toml mypy.ini pylintrc .pre-commit-config.yaml /app/

# Setting appuser rights
RUN chown -R appuser:appuser /app
USER appuser

# By default just start bot
CMD ["python", "bot.py"]