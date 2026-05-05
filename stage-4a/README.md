# SwiftDeploy

A declarative deployment CLI that generates all infrastructure configuration from a single `manifest.yaml` and manages the full container lifecycle.

---

## How It Works

```
manifest.yaml  (single source of truth)
      │
      ▼
swiftdeploy init  →  generates nginx.conf + docker-compose.yml
      │
      ▼
swiftdeploy deploy  →  builds image, starts stack, waits for health
      │
      ▼
swiftdeploy promote canary  →  switches mode, restarts app, confirms
      │
      ▼
swiftdeploy teardown  →  removes everything
```

Nothing is handwritten. The manifest drives everything.

---

## Project Structure

```
stage-4a/
├── manifest.yaml          # single source of truth — edit this only
├── swiftdeploy            # CLI executable
├── Dockerfile             # builds the API service image
├── requirements.txt       # CLI dependencies
├── app/
│   ├── main.py            # Flask API service
│   └── requirements.txt   # app dependencies
└── templates/
    ├── nginx.conf.j2      # nginx config template
    └── docker-compose.yml.j2  # compose template
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/stage-4a
```

### 2. Install CLI dependencies

```bash
pip install -r requirements.txt
```

### 3. Make the CLI executable

```bash
chmod +x swiftdeploy
```

### 4. Review the manifest

Open `manifest.yaml` and confirm the settings match your environment:

```yaml
services:
  image: swift-deploy-1-node:latest
  port: 3000
  mode: stable
  version: "1.0.0"

nginx:
  image: nginx:latest
  port: 8080
  proxy_timeout: 30

network:
  name: swiftdeploy-net
  driver_type: bridge
```

---

## Subcommand Walkthrough

### `init`

Parses `manifest.yaml` and generates `nginx.conf` and `docker-compose.yml` from templates.

```bash
./swiftdeploy init
```

Output:
```
[swiftdeploy] init
  ✔  Generated nginx.conf
  ✔  Generated docker-compose.yml
```

The generated files are derived entirely from the manifest. Delete them and re-run `init` to regenerate.

---

### `validate`

Runs 5 pre-flight checks before deployment. Exits non-zero if any check fails.

```bash
./swiftdeploy validate
```

Checks:
1. `manifest.yaml` exists and is valid YAML
2. All required fields are present and non-empty
3. The Docker image referenced in the manifest exists locally
4. The Nginx port is not already bound on the host
5. The generated `nginx.conf` is syntactically valid

Output:
```
[swiftdeploy] validate

  ✔  manifest.yaml exists and is valid YAML
  ✔  All required fields present and non-empty
  ✔  Docker image 'swift-deploy-1-node:latest' exists locally
  ✔  Port 8080 is available
  ✔  nginx.conf is syntactically valid
```

---

### `deploy`

Runs `init`, builds the Docker image, brings up the stack, and blocks until health checks pass or 60 seconds elapses.

```bash
./swiftdeploy deploy
```

Output:
```
[swiftdeploy] deploy

[swiftdeploy] init
  ✔  Generated nginx.conf
  ✔  Generated docker-compose.yml

  →  Starting stack...
  →  Waiting for health checks (timeout: 60s)...
  ✔  Stack is healthy

  Dashboard → http://localhost:8080
  Health    → http://localhost:8080/healthz
```

---

### `promote`

Switches the deployment mode between `stable` and `canary`. Updates `manifest.yaml` in place, regenerates `docker-compose.yml` with the new `MODE` env var, and restarts only the app container.

```bash
./swiftdeploy promote canary
./swiftdeploy promote stable
```

Output:
```
[swiftdeploy] promote → canary

  ✔  manifest.yaml updated: mode = canary
  ✔  docker-compose.yml regenerated
  →  Restarting app container...
  →  Confirming new mode via /healthz...
  ✔  Service confirmed healthy in canary mode
```

In canary mode, every response includes the header `X-Mode: canary` and the `/chaos` endpoint becomes active.

---

### `teardown`

Removes all containers, networks, and volumes.

```bash
./swiftdeploy teardown
```

With `--clean`, also deletes the generated config files:

```bash
./swiftdeploy teardown --clean
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome message with mode, version, and timestamp |
| GET | `/healthz` | Health check with process uptime |
| POST | `/chaos` | Simulate degraded behaviour (canary mode only) |

### Chaos Endpoint

```bash
# Slow mode — sleep N seconds before every response
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "slow", "duration": 3}'

# Error mode — return 500 on ~50% of requests
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "error", "rate": 0.5}'

# Recover — cancel all chaos
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "recover"}'
```

---

## GitHub Repository

[https://github.com/YOUR_USERNAME/YOUR_REPO](https://github.com/YOUR_USERNAME/YOUR_REPO)
