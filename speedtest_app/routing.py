import csv
import io
import datetime
from flask import Blueprint, render_template, current_app, request, redirect, session, jsonify, Response
from flask.helpers import url_for
from .database import SpeedTest, SpeedTestFailure
from .authlib_client import oidc_required, do_login, callback, reset_session, get_username
from .run_speedtest import run_speedtest
import sqlalchemy as db


blueprint = Blueprint("routing", __name__)


def _filtered_query(year, month):
    """SpeedTest query (newest first) optionally filtered by year and month."""
    query = SpeedTest.query.order_by(SpeedTest.timestamp.desc())
    if year:
        query = query.filter(db.extract('year', SpeedTest.timestamp) == year)
    if month:
        query = query.filter(db.extract('month', SpeedTest.timestamp) == month)
    return query


def _row_dict(r):
    return {
        "timestamp": r.timestamp.isoformat(),
        "ping": r.ping,
        "download": r.download,
        "upload": r.upload,
        "sponsor": r.sponsor,
        "server": r.server_name,
        "distance": r.distance,
        "ip": r.client_ip,
        "isp": r.client_isp,
    }


@blueprint.app_template_filter("datetime")
def format_datetime(value, format="%d %b %Y %I:%M %p"):
    if value is None:
        return ""
    return datetime.datetime.fromisoformat(str(value)).strftime(format)


@blueprint.before_request
def before_request():
    session.permanent = True
    current_app.permanent_session_lifetime = datetime.timedelta(minutes=30)
    if current_app.config.get("ENABLE_TRACE_REQUEST_HDR", False):
        current_app.logger.debug(request.headers)


@blueprint.after_request
def after_request_logging(response):
    current_app.logger.info(f"User: {get_username()} from {request.remote_addr} accessed url: {request.url}")
    return response


@blueprint.route("/auth/login")
def login():
    if not current_app.config.get("ENABLE_OIDC", False):
        return redirect(url_for(".show"))
    return do_login()


@blueprint.route("/auth/callback")
def auth_callback():
    return callback()


@blueprint.route("/auth/logout")
def logout():
    reset_session()
    return render_template("login.html")


@blueprint.route("/api/data")
@oidc_required
def api_data():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    items = _filtered_query(year, month).all()
    results = [_row_dict(r) for r in items]
    return jsonify({
        "data": results,
        "year": year,
        "month": month,
        "total": len(results),
    })


@blueprint.route("/api/years_months")
@oidc_required
def api_years_months():
    # Returns: {2024: [1,2,3], 2023: [12,11,10], ...}
    from sqlalchemy import extract
    results = (
        SpeedTest.query
        .with_entities(
            db.func.extract('year', SpeedTest.timestamp).label('year'),
            db.func.extract('month', SpeedTest.timestamp).label('month')
        )
        .distinct()
        .order_by(db.desc('year'), db.desc('month'))
        .all()
    )
    data = {}
    for year, month in results:
        year = int(year)
        month = int(month)
        data.setdefault(year, []).append(month)
    return jsonify(data)


@blueprint.route("/api/status")
@oidc_required
def api_status():
    """Freshness and reliability summary for the dashboard badge."""
    last = SpeedTest.query.order_by(SpeedTest.timestamp.desc()).first()
    last_failure = SpeedTestFailure.query.order_by(SpeedTestFailure.timestamp.desc()).first()
    return jsonify({
        "last_test": last.timestamp.isoformat() if last else None,
        "last_failure": last_failure.timestamp.isoformat() if last_failure else None,
        "last_error": last_failure.error if last_failure else None,
        "total_tests": SpeedTest.query.count(),
        "total_failures": SpeedTestFailure.query.count(),
    })


@blueprint.route("/api/run", methods=["POST"])
@oidc_required
def api_run():
    """Trigger a speedtest immediately. Runs synchronously (~30s)."""
    ok = run_speedtest()
    if ok:
        return jsonify({"status": "ok"})
    return jsonify({"status": "busy_or_failed"}), 409


@blueprint.route("/api/export")
@oidc_required
def api_export():
    """Download the selected period as CSV or JSON."""
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    fmt = request.args.get("format", "csv").lower()
    items = _filtered_query(year, month).all()
    suffix = "-".join(str(p) for p in (year, month) if p) or "all"

    if fmt == "json":
        return Response(
            jsonify([_row_dict(r) for r in items]).get_data(),
            mimetype="application/json",
            headers={"Content-Disposition": f'attachment; filename="speedtest-{suffix}.json"'},
        )

    fields = ["timestamp", "ping", "download", "upload", "sponsor", "server", "distance", "ip", "isp"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for r in items:
        writer.writerow(_row_dict(r))
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="speedtest-{suffix}.csv"'},
    )


@blueprint.route("/")
@oidc_required
def show():
    return render_template("show.html")
