FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir flask openpyxl pytz requests cryptography

EXPOSE 5003

CMD ["python", "app.py"]
