FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy only requirements file first for better caching
COPY pyproject.toml requirements.lock README.md ./

# Install dependencies with UV
RUN uv pip install --no-cache --system -r requirements.lock

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create logs directory
RUN mkdir -p /app/logs

# Copy the application code with proper ownership
COPY --chown=appuser:appuser . /app

# Set permissions for the logs directory
RUN chown -R appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check for Streamlit
# HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
#   CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.headless=true", "--server.port=8501", "--server.address=0.0.0.0"]