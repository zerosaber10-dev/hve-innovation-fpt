# Production Dockerfile for Enterprise HR Time and Leave Copilot
FROM python:3.11-slim

# Standard container runtime configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Create dedicated non-root application user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/bash -m appuser

# Copy project specification and install dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source code
COPY src/ /app/src/

# Assign ownership to non-root user
RUN chown -R appuser:appuser /app

# Execute as non-root user
USER appuser:10001

# Expose web service port
EXPOSE 8000

# Container liveness health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

# ASGI server launch command
CMD ["uvicorn", "hr_time_leave.app:app", "--host", "0.0.0.0", "--port", "8000"]
