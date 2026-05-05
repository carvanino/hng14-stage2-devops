FROM python:3.11-slim

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

WORKDIR /app

# Build context is the root — reference app/ explicitly
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/main.py .

USER appuser

ENV MODE=stable
ENV APP_VERSION=1.0.0
ENV APP_PORT=3000

EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "main:app"]
