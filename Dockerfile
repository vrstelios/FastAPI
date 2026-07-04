# ========== Builder Stage ==========
FROM python:3.14-slim AS builder

# Εγκατάσταση του uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Αντιγραφή μόνο των αρχείων εξαρτήσεων για καλύτερο caching
COPY pyproject.toml uv.lock ./

# Τώρα το uv θα βρει την Python 3.14 έτοιμη στο σύστημα
RUN uv sync --frozen --no-dev --no-install-project --python-preference only-system

# ========== Runtime Stage ==========
FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Σωστό configuration για το .venv και το PYTHONPATH
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Αντιγραφή του έτοιμου .venv από τον builder stage
COPY --from=builder /app/.venv $VIRTUAL_ENV

# Αντιγραφή του κώδικα της εφαρμογής
COPY . .

# Ασφάλεια: non-root χρήστης
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]