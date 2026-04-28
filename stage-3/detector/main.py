import time
import threading
import yaml


from monitor import tail_log
from baseline import BaselineEngine
from detector import AnamolyDetector
from blocker import Blocker
from unbanner import Unbanner
from notifier import Notifier
from audit import AuditLogger
from dashboard import Dashboard


def main():
    """

    """
    #  Load config ────────────────────────────────────────────
    with open('detector/config.yaml') as f:
        config = yaml.safe_load(f)
    

    notifier = Notifier(config.get('slack_webhook'))
    audit = AuditLogger(config)
    baseline = BaselineEngine()
    detector = AnamolyDetector(baseline=baseline, config=config)
    blocker = Blocker(config=config, audit_logger=audit, notifier=notifier)
    unbanner = Unbanner(banned_ips=blocker.banned_ips, lock=blocker.lock, config=config, audit_logger=audit, notifier=notifier)

    start_time = time.time()
    dashboard = Dashboard(blocker, detector, baseline, start_time)
    dashboard.run(port=config['dashboard_port'])

    # Baseline ticker — records global req/s every second
    def baseline_ticker():
        while True:
            time.sleep(1)
            with detector.lock:
                count = detector.global_window.count()
            baseline.record(count)
            # Notify Slack when baseline recalculates
            # baseline.record() updates last_recalc internally
            # we check if a recalc just happened
            if abs(time.time() - baseline.last_recalc) < 1:
                audit.log(
                    'BASELINE_RECALC', '-', '',
                    0, baseline.effective_mean, '-'
                )

    threading.Thread(target=baseline_ticker, daemon=True).start()

    #  Main loop ──────────────────────────────────────────────
    print(f"[*] Detector started. Tailing {config['log_path']}")
    print(f"[*] Dashboard running at http://0.0.0.0:{config['dashboard_port']}")

    for entry in tail_log(config['log_path']):

        # Feed entry into detector
        alerts = detector.record(entry)

        # Handle whatever came back
        for alert in alerts:
            if alert['type'] == 'ip':
                blocker.block_ip(alert['ip'], alert['condition'], alert['rate'], baseline.effective_mean)
            elif alert['type'] == 'global':
                notifier.send_global_alert(alert['rate'], baseline.effective_mean)


if __name__ == "__main__":
    main()