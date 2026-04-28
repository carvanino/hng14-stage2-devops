import datetime
import threading


class AuditLogger:
    """
    Handles structured logging of all actions (bans, unbans, baseline recalculations).
    Writes one line per event with a consistent format for easy parsing and analysis.
    """

    def __init__(self, config):
        self.log_path = config['audit_log']
        self.lock = threading.Lock()

    def log(self, action, ip, condition, rate, baseline, duration):
        """
        Writes one structured line per event.
        action: BAN | UNBAN | BASELINE_RECALC
        """
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        line = (
            f"[{timestamp}] {action:<15} "
            f"ip={ip} | "
            f"condition={condition} | "
            f"rate={rate:.2f} | "
            f"baseline={baseline:.2f} | "
            f"duration={duration}\n"
        )

        # Lock because multiple threads call this simultaneously
        with self.lock:
            with open(self.log_path, 'a') as f:
                f.write(line)