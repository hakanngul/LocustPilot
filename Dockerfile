FROM python:3.10-slim

LABEL maintainer="Locust App Contributors <https://github.com/your-username/locust_app>"
LABEL description="Locust Load Testing Container"

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Locust için gerekli ortam değişkenlerini ayarla
ENV PYTHONPATH=/app
ENV LOCUST_HOST=https://localhost:8080
ENV TEST_ENV=dev

# Locust'u çalıştır
ENTRYPOINT ["locust"]
CMD ["-f", "locustfiles/main.py", "--host", "${LOCUST_HOST}"]