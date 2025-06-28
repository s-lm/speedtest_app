import datetime
import os
import base64
from flask import Blueprint, render_template, current_app, request, redirect, session, jsonify
from flask.helpers import url_for
from .database import SpeedTest
from .authlib_client import oauth
import sqlalchemy as db


blueprint = Blueprint("routing", __name__)


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


def oidc_required(f):
    """Decorator to require OIDC only if enabled."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get("ENABLE_OIDC", False):
            if "user" not in session:
                return redirect(url_for(".login", next=request.url))
        return f(*args, **kwargs)
    return wrapper


@blueprint.route("/auth/login")
def login():
    if not current_app.config.get("ENABLE_OIDC", False):
        return redirect(url_for(".show"))
    redirect_uri = url_for(".auth_callback", _external=True)
    nonce = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8")
    session["oidc_nonce"] = nonce
    return oauth.oidc.authorize_redirect(redirect_uri, nonce=nonce)


@blueprint.route("/auth/callback")
def auth_callback():
    token = oauth.oidc.authorize_access_token()
    nonce = session.pop("oidc_nonce", None)
    userinfo = oauth.oidc.parse_id_token(token, nonce=nonce)
    session["user"] = userinfo
    next_url = request.args.get("next") or url_for(".show")
    current_app.logger.info(f"User {userinfo['preferred_username']} logged in successfully.")
    return redirect(next_url)


@blueprint.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("routing.login"))

    
@blueprint.route("/api/data")
@oidc_required
def api_data():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    query = SpeedTest.query.order_by(SpeedTest.timestamp.desc())
    if year:
        query = query.filter(db.extract('year', SpeedTest.timestamp) == year)
    if month:
        query = query.filter(db.extract('month', SpeedTest.timestamp) == month)
    items = query.all()
    results = []
    for r in items:
        results.append({
            "timestamp": r.timestamp.isoformat(),
            "ping": r.ping,
            "download": r.download,
            "upload": r.upload,
            "sponsor": r.sponsor,
            "server": r.server_name,
            "distance": r.distance,
            "ip": r.client_ip,
            "isp": r.client_isp,
        })
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


@blueprint.route("/", methods=["GET"])
@oidc_required
def show():
    current_app.logger.info(f"User {session.get('user', {}).
            get('preferred_username', 'unknown')} accessed url: {request.url}")
    return render_template("show.html")
