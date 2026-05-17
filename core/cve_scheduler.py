import threading
import time
from datetime import datetime
from utils.logger import get_logger
from core.cve_updater import get_cve_updater

log = get_logger("cve_scheduler")


class CVEScheduler:
    """Schedules automatic CVE updates every 24 hours."""

    def __init__(self, interval_hours=24):
        self.interval_hours = interval_hours
        self._thread = None
        self._stop_event = threading.Event()
        self._last_run = None
        self._run_count = 0
        self._errors = []

    def start(self):
        """Start the background scheduler thread."""
        if self._thread and self._thread.is_alive():
            log.info("CVE scheduler already running")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="cve-scheduler")
        self._thread.start()
        log.info(f"CVE scheduler started (interval: {self.interval_hours}h)")
        return True

    def stop(self):
        """Stop the background scheduler thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        log.info("CVE scheduler stopped")

    def run_once(self):
        """Run a single CVE fetch immediately."""
        try:
            updater = get_cve_updater()
            cves = updater.fetch_recent(days=7, max_results=100)
            self._last_run = datetime.now().isoformat()
            self._run_count += 1
            log.info(f"CVE scheduler: fetched {len(cves)} CVEs")
            return {"success": True, "count": len(cves), "timestamp": self._last_run}
        except Exception as e:
            err_msg = str(e)
            self._errors.append({"error": err_msg, "timestamp": datetime.now().isoformat()})
            log.error(f"CVE scheduler error: {err_msg}")
            return {"success": False, "error": err_msg}

    def _run_loop(self):
        """Main loop: fetch CVEs every interval_hours."""
        log.info("CVE scheduler loop started")
        while not self._stop_event.is_set():
            self.run_once()
            self._stop_event.wait(timeout=self.interval_hours * 3600)
        log.info("CVE scheduler loop exited")

    def get_status(self):
        """Return current scheduler status."""
        return {
            "running": self._thread is not None and self._thread.is_alive(),
            "interval_hours": self.interval_hours,
            "last_run": self._last_run,
            "run_count": self._run_count,
            "recent_errors": self._errors[-5:] if self._errors else [],
        }


_global_scheduler = None


def get_cve_scheduler():
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = CVEScheduler()
    return _global_scheduler
