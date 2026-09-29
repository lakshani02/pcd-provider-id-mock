FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY pyproject.toml ./
COPY pcd_provider_mock ./pcd_provider_mock
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ['PORT'], timeout=4)"

CMD ["sh", "-c", "uvicorn pcd_provider_mock.main:app --host 0.0.0.0 --port ${PORT}"]
