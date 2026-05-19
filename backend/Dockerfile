FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install --yes --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    gcc \
    git \
    libpq-dev \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libharfbuzz0b \
    libjpeg62-turbo \
    libopenjp2-7 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libwebp7 \
    libxml2 \
    libxslt1.1 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

COPY . /app

RUN mkdir -p /app/generated/artifacts && \
    useradd --system --create-home --home-dir /home/appuser --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import sys, urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3); sys.exit(0 if response.status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
