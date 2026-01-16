FROM python:3.11-slim

LABEL maintainer="Locust App Contributors <https://github.com/your-username/locust_app>"
LABEL description="Streamlit UI for managing Locust load tests"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENTRYPOINT ["streamlit"]
CMD ["run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

