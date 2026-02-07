# AetherPackBot Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

# Install UV
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY aetherpackbot/ aetherpackbot/

# Install dependencies
RUN uv sync --frozen --no-dev

# Create data directory
RUN mkdir -p data plugins

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uv", "run", "python", "main.py"]
