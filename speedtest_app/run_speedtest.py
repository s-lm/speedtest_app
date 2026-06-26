import threading
import speedtest
from sqlalchemy.exc import IntegrityError
from flask import current_app
from .database import db, SpeedTest, SpeedTestFailure

# Prevent overlapping runs (the scheduler and a manual trigger could collide).
_run_lock = threading.Lock()


def run_speedtest() -> bool:
    """Run a speedtest and store the result.

    Returns True on success. If a run is already in progress the trigger is
    skipped and False is returned. Measurement or commit errors are recorded
    as a failure row and also return False.
    """
    if not _run_lock.acquire(blocking=False):
        current_app.logger.warning("Speedtest already running; skipping this trigger.")
        return False
    try:
        return _run_and_store()
    finally:
        _run_lock.release()


def _run_and_store() -> bool:
    try:
        server_ids = current_app.config.get("SPEEDTEST_SERVER_IDS", []) or None
        probe = speedtest.Speedtest()
        probe.get_servers(server_ids)
        probe.get_best_server()
        probe.download()
        probe.upload()
        result = probe.results.dict()
    except Exception as e:
        current_app.logger.error(f"Speedtest measurement failed: {e}")
        _record_failure(str(e))
        return False

    current_app.logger.debug(result)
    db.session.add(SpeedTest(
            server_id       = result["server"]["id"],
            sponsor         = result["server"]["sponsor"],
            server_name     = result["server"]["name"],
            server_host     = result["server"]["host"],
            timestamp       = result["timestamp"],
            distance        = result["server"]["d"],
            ping            = result["ping"],
            download        = result["download"],
            upload          = result["upload"],
            share           = result["share"],
            client_ip       = result["client"]["ip"],
            client_isp      = result["client"]["isp"],
            client_country  = result["client"]["country"]))

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError: {e}")
        _record_failure(f"IntegrityError: {e}")
        return False
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"An error occurred while committing the speedtest results: {e}")
        _record_failure(str(e))
        return False
    else:
        current_app.logger.info("Speedtest completed successfully.")
        return True


def _record_failure(message: str) -> None:
    """Persist a failure so outages are visible in the dashboard."""
    try:
        db.session.add(SpeedTestFailure(error=message[:1000]))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record speedtest failure: {e}")
