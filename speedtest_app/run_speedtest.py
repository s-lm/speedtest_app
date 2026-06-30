import threading
import speedtest
from sqlalchemy.exc import IntegrityError
from flask import current_app
from .database import db, SpeedTest, SpeedTestFailure

# Prevent overlapping runs (the scheduler and a manual trigger could collide).
_run_lock = threading.Lock()


def run_speedtest() -> bool:
    """Run a speedtest and store the result.

    Returns True on success, False otherwise. Kept for the scheduler; callers
    that need the reason should use :func:`run_speedtest_status`.
    """
    ok, _ = run_speedtest_status()
    return ok


def run_speedtest_status() -> tuple[bool, str | None]:
    """Run a speedtest and report (ok, reason).

    On success returns ``(True, None)``. If a run is already in progress the
    trigger is skipped and ``(False, "busy")`` is returned. Measurement or
    commit errors are recorded as a failure row and returned as the reason.
    """
    if not _run_lock.acquire(blocking=False):
        current_app.logger.warning("Speedtest already running; skipping this trigger.")
        return False, "busy"
    try:
        return _run_and_store()
    finally:
        _run_lock.release()


def _measure(server_ids):
    """Run download/upload against the given server IDs (None = auto-select)."""
    probe = speedtest.Speedtest()
    probe.get_servers(server_ids)
    probe.get_best_server()
    probe.download()
    probe.upload()
    return probe.results.dict()


def _run_and_store() -> tuple[bool, str | None]:
    server_ids = current_app.config.get("SPEEDTEST_SERVER_IDS", []) or None
    try:
        result = _measure(server_ids)
    except speedtest.NoMatchedServers:
        if server_ids:
            # The pinned IDs aren't in the server list reachable from this host
            # (Ookla's list is location-dependent and sometimes incomplete).
            # Don't fail the run — fall back to auto-selecting the best server.
            current_app.logger.warning(
                f"Pinned SPEEDTEST_SERVER_IDS={server_ids} matched no server reachable "
                "from this host; falling back to auto-selecting the best server.")
            try:
                result = _measure(None)
            except Exception as e:
                msg = f"Speedtest failed even after auto-select fallback: {e}"
                current_app.logger.error(msg)
                _record_failure(msg)
                return False, msg
        else:
            msg = "No speedtest servers reachable from this host."
            current_app.logger.error(msg)
            _record_failure(msg)
            return False, msg
    except Exception as e:
        current_app.logger.error(f"Speedtest measurement failed: {e}")
        _record_failure(str(e))
        return False, str(e)

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
        return False, f"IntegrityError: {e}"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"An error occurred while committing the speedtest results: {e}")
        _record_failure(str(e))
        return False, str(e)
    else:
        current_app.logger.info("Speedtest completed successfully.")
        return True, None


def _record_failure(message: str) -> None:
    """Persist a failure so outages are visible in the dashboard."""
    try:
        db.session.add(SpeedTestFailure(error=message[:1000]))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record speedtest failure: {e}")
