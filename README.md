# Stage 2 DevOps - Containerized Microservices

This repository contains a containerized microservices application as part of the HNG Stage 2 DevOps task. The application consists of three services:
1. **Frontend (Node.js)**: A web dashboard to submit and track jobs.
2. **API (FastAPI/Python)**: A REST API that handles job creation and status updates.
3. **Worker (Python)**: A background worker that pulls jobs from a queue and processes them.

All services are glued together using a shared Redis instance and orchestrated via Docker Compose.

## Prerequisites
To run this application, you must have the following installed on your machine:
* Git
* Docker
* Docker Compose (v2)

## Setup Instructions

**1. Clone the repository**
```bash
git clone <your-fork-url>
cd hng14-stage2-devops
```

**2. Configure Environment Variables**
The application relies on environment variables for configuration. We have provided an example file. Copy the example file and fill out the password:
```bash
cp .env.example .env
```
*(Note: Do not commit the `.env` file to version control. It is ignored by `.gitignore`.)*

**3. Start the Stack**
Bring up the entire stack in detached mode using Docker Compose:
```bash
sudo docker compose up --build -d
```

## Verifying a Successful Startup
Once the command finishes building the images and starting the containers, you can verify the deployment:

1. Check the running containers:
```bash
sudo docker compose ps
```
You should see 4 containers running (`redis`, `api`, `worker`, and `frontend`), and their status should eventually say `(healthy)`.

2. **Check the Frontend**: 
Open your browser and navigate to `http://localhost:3000`. You should see the "Job Processor Dashboard". Click "Submit New Job" and watch the status update from "queued" to "completed".

3. **Check the Logs**:
Run `sudo docker compose logs -f` to see the application running. A successful log stream will look like this:
```text
redis-1     | 1:M 23 Apr 2026 21:30:35.476 * Ready to accept connections tcp
api-1       | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
api-1       | INFO:     127.0.0.1:44860 - "GET /docs HTTP/1.1" 200 OK
frontend-1  | Frontend running on port 3000
worker-1    | Processing job 1b2a...
worker-1    | Done: 1b2a...
```

## CI/CD Pipeline
This repository uses GitHub Actions for a full CI/CD pipeline that runs on every push to `main`. It automatically:
1. Lints the Python, JavaScript, and Dockerfiles.
2. Runs Python unit tests using `pytest` and mocks Redis.
3. Builds the Docker images to a local registry.
4. Scans the images for CRITICAL vulnerabilities using Trivy.
5. Performs a full integration test by spinning up the stack and polling the API.
6. Deploys using a scripted zero-downtime rolling update via `deploy.sh`.
