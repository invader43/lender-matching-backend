FROM python:3.9-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies directly without building package
RUN uv pip install --system fastapi uvicorn[standard] sqlalchemy psycopg[binary] pydantic-settings asyncpg python-dotenv

# Copy application code
COPY . .

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
