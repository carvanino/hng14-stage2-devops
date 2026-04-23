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
COPY --chown=appuser:appuser main.py .

ENV PATH="/home/appuser/.local/bin:$PATH"

# Switch to the user AFTER they have been created and given ownership of the files
USER appuser

EXPOSE 8000

# Use Python's built in urllib instead of wget
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]