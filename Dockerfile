# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    DATABASE_PATH=/data/site.db \
    UPLOAD_DIR=/data/uploads

WORKDIR /srv/app

RUN adduser --system --group --no-create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# SQLite file + uploaded images live here; mount a volume over it.
RUN mkdir -p /data/uploads && chown -R appuser:appuser /data /srv/app
VOLUME ["/data"]

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=4s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/robots.txt', timeout=3).status==200 else 1)"

# Threads, not processes: SQLite writes are serialised and the workload is tiny.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", \
     "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
