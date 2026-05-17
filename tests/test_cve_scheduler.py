import pytest
import time
import os
from pathlib import Path
from core.cve_scheduler import CVEScheduler, SCHEDULER_STATE_FILE


class TestCVEScheduler:
    def setup_method(self):
        """Clean state before each test."""
        if SCHEDULER_STATE_FILE.exists():
            SCHEDULER_STATE_FILE.unlink()

    def teardown_method(self):
        """Clean state after each test."""
        if SCHEDULER_STATE_FILE.exists():
            SCHEDULER_STATE_FILE.unlink()

    def test_initial_state(self):
        scheduler = CVEScheduler(interval_hours=24)
        status = scheduler.get_status()
        assert status['running'] is False
        assert status['interval_hours'] == 24
        assert status['last_run'] is None
        assert status['run_count'] == 0

    def test_start_stop(self):
        scheduler = CVEScheduler(interval_hours=1)
        started = scheduler.start()
        assert started is True
        status = scheduler.get_status()
        assert status['running'] is True
        scheduler.stop()
        status = scheduler.get_status()
        assert status['running'] is False

    def test_double_start(self):
        scheduler = CVEScheduler(interval_hours=1)
        scheduler.start()
        result = scheduler.start()
        assert result is False
        scheduler.stop()

    def test_run_once(self):
        scheduler = CVEScheduler(interval_hours=1)
        result = scheduler.run_once()
        assert 'success' in result
        assert scheduler._run_count == 1
        assert scheduler._last_run is not None

    def test_run_once_error_handling(self):
        scheduler = CVEScheduler(interval_hours=1)
        result = scheduler.run_once()
        assert isinstance(result, dict)
        assert 'success' in result

    def test_status_after_run(self):
        scheduler = CVEScheduler(interval_hours=12)
        scheduler.run_once()
        status = scheduler.get_status()
        assert status['run_count'] == 1
        assert status['interval_hours'] == 12

    def test_multiple_runs(self):
        scheduler = CVEScheduler(interval_hours=1)
        scheduler.run_once()
        scheduler.run_once()
        scheduler.run_once()
        assert scheduler._run_count == 3

    def test_errors_tracked(self):
        scheduler = CVEScheduler(interval_hours=1)
        scheduler._errors.append({"error": "test error", "timestamp": "2025-01-01T00:00:00"})
        status = scheduler.get_status()
        assert len(status['recent_errors']) == 1

    def test_persistence(self):
        scheduler = CVEScheduler(interval_hours=6)
        scheduler.run_once()
        scheduler.stop()

        new_scheduler = CVEScheduler()
        assert new_scheduler._run_count == 1
        assert new_scheduler.interval_hours == 6
