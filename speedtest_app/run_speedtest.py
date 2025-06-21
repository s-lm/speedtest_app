import speedtest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from .database import db, SpeedTest


def run_speedtest():
    """Run a speedtest and log the results."""
    probe = speedtest.Speedtest()
    probe.get_servers()
    probe.get_best_server()
    probe.download()
    probe.upload()
    result = probe.results.dict()
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"An error occurred while committing the speedtest results: {e}")
    else:
        current_app.logger.info("Speedtest completed successfully.")
