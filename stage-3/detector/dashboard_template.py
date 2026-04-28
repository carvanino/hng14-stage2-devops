HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HNG Anomaly Detector</title>
    <style>
        body {
            font-family: monospace;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        h1 { color: #58a6ff; }
        h2 { color: #8b949e; border-bottom: 1px solid #21262d; padding-bottom: 5px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 15px;
        }
        .card .value {
            font-size: 2em;
            color: #58a6ff;
            font-weight: bold;
        }
        .card .label { color: #8b949e; font-size: 0.85em; }
        .banned { color: #f85149; }
        .normal { color: #3fb950; }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        td, th {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }
        th { color: #8b949e; }
        .last-updated { color: #8b949e; font-size: 0.8em; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🛡️ HNG Anomaly Detection Engine</h1>

    <div class="grid">
        <div class="card">
            <div class="value" id="global-rate">-</div>
            <div class="label">Global req/s</div>
        </div>
        <div class="card">
            <div class="value" id="banned-count">-</div>
            <div class="label">Banned IPs</div>
        </div>
        <div class="card">
            <div class="value" id="uptime">-</div>
            <div class="label">Uptime</div>
        </div>
        <div class="card">
            <div class="value" id="cpu">-</div>
            <div class="label">CPU Usage</div>
        </div>
        <div class="card">
            <div class="value" id="memory">-</div>
            <div class="label">Memory Usage</div>
        </div>
        <div class="card">
            <div class="value" id="baseline">-</div>
            <div class="label">Baseline mean / stddev</div>
        </div>
    </div>

    <h2>Banned IPs</h2>
    <table>
        <tr>
            <th>IP</th>
            <th>Duration</th>
            <th>Level</th>
            <th>Time Remaining</th>
        </tr>
        <tbody id="banned-table"></tbody>
    </table>

    <h2>Top 10 Source IPs</h2>
    <table>
        <tr><th>IP</th><th>Rate (req/s)</th></tr>
        <tbody id="top-ips-table"></tbody>
    </table>

    <div class="last-updated">Last updated: <span id="last-updated">-</span></div>

    <script>
        function update() {
            fetch('/metrics')
                .then(r => r.json())
                .then(data => {
                    // Stat cards
                    document.getElementById('global-rate').textContent =
                        data.global_rate + ' req/s';
                    document.getElementById('banned-count').textContent =
                        data.banned_count;
                    document.getElementById('uptime').textContent =
                        data.uptime_human;
                    document.getElementById('cpu').textContent =
                        data.cpu_percent + '%';
                    document.getElementById('memory').textContent =
                        data.memory_percent + '%';
                    document.getElementById('baseline').textContent =
                        data.baseline_mean + ' / ' + data.baseline_stddev;

                    // Banned IPs table
                    const bannedTable = document.getElementById('banned-table');
                    bannedTable.innerHTML = '';
                    Object.entries(data.banned_ips).forEach(([ip, info]) => {
                        const remaining = info.remaining === 'permanent'
                            ? 'permanent'
                            : Math.round(info.remaining) + 's remaining';
                        bannedTable.innerHTML +=
                            `<tr class="banned">
                                <td>${ip}</td>
                                <td>${info.duration} min</td>
                                <td>${info.level}</td>
                                <td>${remaining}</td>
                            </tr>`;
                    });
                    if (Object.keys(data.banned_ips).length === 0) {
                        bannedTable.innerHTML =
                            '<tr><td colspan="4" class="normal">No banned IPs</td></tr>';
                    }

                    // Top IPs table
                    const topTable = document.getElementById('top-ips-table');
                    topTable.innerHTML = '';
                    data.top_ips.forEach(entry => {
                        topTable.innerHTML +=
                            `<tr>
                                <td>${entry.ip}</td>
                                <td>${entry.rate.toFixed(2)}</td>
                            </tr>`;
                    });

                    document.getElementById('last-updated').textContent =
                        new Date().toLocaleTimeString();
                });
        }

        // Update immediately then every 3 seconds
        update();
        setInterval(update, 3000);
    </script>
</body>
</html>
"""