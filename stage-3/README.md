# HNG Stage 3 — Anomaly Detection Engine

A real-time HTTP traffic anomaly detection and DDoS mitigation daemon built for Nextcloud on Docker. It continuously monitors Nginx access logs, learns normal traffic patterns, and automatically blocks suspicious IPs using iptables.

---

## Live Deployment

| Resource | URL |
|---|---|
| Server IP | 157.180.45.114 |
| Metrics Dashboard | http://hng-akinola.duckdns.org |

---

## Language Choice

**Python** — chosen for its readability and the standard library's strong support for threading, deque-based data structures, and subprocess management. The `collections.deque` type is ideal for the sliding window implementation since it supports O(1) appends and popleft operations. Python's threading module handles the concurrent requirements (log tailing, baseline ticking, unban loop, dashboard) cleanly without external dependencies.

---

## Repository Structure

```
stage-3/
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
├── detector/
│   ├── main.py
│   ├── monitor.py
│   ├── baseline.py
│   ├── detector.py
│   ├── blocker.py
│   ├── unbanner.py
│   ├── notifier.py
│   ├── dashboard.py
│   ├── config.yaml
│   └── requirements.txt
├── docs/
│   └── architecture.png
├── screenshots/
└── README.md
```

---

## How the Sliding Window Works

The sliding window tracks request timestamps using a `collections.deque` — a double-ended queue that supports O(1) insertions and removals from both ends.

Two windows run in parallel:
- **Per-IP window** — one deque per unique source IP
- **Global window** — one deque tracking all traffic

**How entries are added and evicted:**

Every time a request arrives, its Unix timestamp is appended to the right of the deque. Simultaneously, any timestamps older than 60 seconds are removed from the left:

```python
def add(self, timestamp):
    self.timestamps.append(timestamp)          # add to right
    cutoff = timestamp - self.window_seconds
    while self.timestamps and self.timestamps[0] < cutoff:
        self.timestamps.popleft()              # evict from left
```

The length of the deque at any moment is the request count for the last 60 seconds. Dividing by 60 gives the per-second rate. The window "slides" because it always represents the most recent 60 seconds — old entries fall off the left as new ones come in on the right.

A separate `count_last_n_seconds(1)` method counts only timestamps from the last 1 second, used by the baseline ticker to record true per-second counts.

---

## How the Baseline Works

The baseline engine maintains a 30-minute rolling window of per-second request counts. Every second, the baseline ticker records how many requests arrived in that specific second. Every 60 seconds the engine recalculates the effective mean and standard deviation.

**Window size:** 1800 seconds (30 minutes) of per-second counts

**Recalculation interval:** Every 60 seconds

**Hourly slots:** Counts are also stored in per-hour buckets. When the current hour has at least 300 data points (5 minutes), the hourly data is preferred over the full 30-minute window. This prevents quiet night-time traffic from distorting the baseline during a busy morning.

**Floor values:** The effective mean is floored at `1.0` and stddev at `0.5` to prevent division by zero during quiet periods:

```python
self.effective_mean = max(mean, 1.0)
self.effective_stddev = max(stddev, 0.5)
```

---

## How Detection Works

The anomaly detector runs three checks on every incoming request:

**Check 1 — Z-score:** How many standard deviations above normal is the current rate?

```
z = (current_rate - effective_mean) / effective_stddev
```

If `z > 3.0`, the rate is statistically anomalous. A z-score above 3.0 means the probability of this occurring naturally is less than 0.3%.

**Check 2 — Rate multiplier:** Is the current rate more than 5x the baseline mean? This catches attacks during the early minutes when the baseline is still building and stddev is low.

**Check 3 — Error surge:** If an IP's 4xx/5xx error rate exceeds 3x the baseline error rate, the z-score threshold is automatically tightened from 3.0 to 2.1 for that IP. This catches probing and scanning behaviour that may not produce a high request rate but generates unusual error patterns.

Both the per-IP and global rates are checked independently. A per-IP anomaly triggers a ban. A global anomaly (distributed attack) triggers a Slack alert only.

---

## How iptables Blocking Works

When an IP is flagged as anomalous, the blocker adds a DROP rule to the host's INPUT chain:

```bash
iptables -A INPUT -s <IP> -j DROP
```

This rule tells the Linux kernel to silently discard all incoming packets from that IP before they reach Nginx or any other service. The detector container runs with `network_mode: host` and `cap_add: NET_ADMIN` so its iptables commands affect the host's firewall directly.

**Auto-unban backoff schedule:**

| Offence | Ban Duration |
|---|---|
| 1st | 10 minutes |
| 2nd | 30 minutes |
| 3rd | 2 hours |
| 4th+ | Permanent |

The unbanner runs in a background thread, checking every 30 seconds whether any bans have expired. On expiry it removes the iptables rule and sends a Slack notification.

---

## Setup Instructions (Fresh VPS)

### 1. Provision a VPS

Minimum specs: 2 vCPU, 2 GB RAM. Ubuntu 22.04 LTS recommended.

### 2. Install Docker

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/stage-3
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Set your Slack webhook URL:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 5. Create the Audit Log Directory

```bash
sudo mkdir -p /var/log/detector
```

### 6. Find the Docker Bridge Gateway IP

```bash
# Start the stack first, then inspect the network
sudo docker compose up -d
sudo docker network inspect stage-3_hng-network | grep Gateway
```

Update `nginx/nginx.conf` with the correct gateway IP in the dashboard proxy_pass line.

### 7. Open Required Ports

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8081 -j ACCEPT
sudo iptables -I DOCKER-USER -i br-+ -j ACCEPT
```

### 8. Start the Stack

```bash
sudo docker compose build detector
sudo docker compose up -d
```

### 9. Verify Everything is Running

```bash
# All three containers should be running
sudo docker compose ps

# Nginx is writing JSON logs
sudo docker exec hng-nginx tail -1 /var/log/nginx/hng-access.log | python3 -m json.tool

# Detector is reading logs
sudo docker compose logs detector

# Dashboard is accessible
curl http://localhost:8081
```

### 10. Point Your Domain

Update your DuckDNS (or other DNS provider) to point to your VPS IP. Update the `server_name` in `nginx/nginx.conf` to your domain. Restart Nginx:

```bash
sudo docker compose restart nginx
```

---

## Simulating an Attack (Testing)

```bash
# Install Apache Benchmark
sudo apt install apache2-utils -y

# Send sustained high traffic to trigger detection
ab -n 15000 -c 50 -t 30 http://YOUR_VPS_IP/
```

Wait for the Slack ban notification and verify the iptables rule:

```bash
sudo iptables -L INPUT -n
```

---

## GitHub Repository

[https://github.com/carvanino/hng14-stage2-devops](https://github.com/carvanino/hng14-stage2-devops)

---

## Blog Post

[Link to be added]
