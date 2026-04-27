# Application Fixes

This document details the bugs found in the source code and how they were resolved to make the application production-ready.

| File | Line(s) | Problem | Fix |
|---|---|---|---|
| `api/main.py` | 8 | The Redis connection hardcoded `host="localhost"` and `port=6379`, and did not accept a password, meaning it would fail to connect to a Redis container. | Replaced the hardcoded values with environment variables (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`) using `os.getenv`. |
| `worker/worker.py` | 6 | The Redis connection had the same hardcoded configuration issues as the API service. | Replaced the hardcoded values with environment variables using `os.getenv`, matching the API's setup. |
| `frontend/app.js` | 6 | The `API_URL` was hardcoded to `http://localhost:8000`. In a Docker environment, `localhost` refers to the container itself, not the API container. | Updated `API_URL` to be constructed from `process.env.API_HOST` and `process.env.API_PORT` with fallbacks. |
| `frontend/app.js` | 32 | The server port was hardcoded to `3000` inside the `app.listen()` block. | Updated it to use `process.env.PORT || 3000`. |
| `api/.env` | All | The `.env` file containing sensitive credentials was committed to the repository, violating security best practices. | Removed `.env` from git history using `git rm --cached`, created `.env.example` with placeholder values, and rewrote the initial commit. |
