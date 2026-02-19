# Use uv's official image as base — it includes Python and uv pre-installed
# Pin to a specific Python version that matches your pyproject.toml
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen = use exact versions from lockfile)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

# Sync again to install the project itself (fast since deps are cached)
RUN uv sync --frozen

# Create directory for SQLite database (will be mounted as a volume)
RUN mkdir -p /app/data

EXPOSE 8000

# Run with uv so it uses the correct virtual environment
# Host 0.0.0.0 is critical — without it, uvicorn only listens on
# localhost inside the container and is unreachable from outside
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
