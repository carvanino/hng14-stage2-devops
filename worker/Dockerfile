FROM python:3.12-alpine3.21 AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-alpine3.21

# Create the non-root user first
RUN adduser -D appuser

WORKDIR /app

# Copy the packages and the code, ensuring appuser owns them
COPY --chown=appuser:appuser --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser worker.py .

ENV PATH="/home/appuser/.local/bin:$PATH"

# Switch to the user AFTER they have been created and given ownership of the files
USER appuser

# Use a Python script to verify connection to Redis as the healthcheck
HEALTHCHECK CMD python -c "import redis, os; r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)), password=os.getenv('REDIS_PASSWORD')); r.ping()" || exit 1

CMD ["python", "worker.py"]