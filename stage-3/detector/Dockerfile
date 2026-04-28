FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/log/detector

CMD ["python3", "main.py"]