import datetime
from flask import Blueprint, render_template, current_app, request, flash, redirect, session, jsonify
from flask.helpers import send_from_directory, url_for
from .database import SpeedTest

blueprint = Blueprint('routing', __name__)


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


@blueprint.route("/api/data")
def api_data():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=500, type=int)

    pagination = SpeedTest.query.order_by(SpeedTest.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

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
            "ip": r.client_ip,      # renamed for frontend
            "isp": r.client_isp,    # additional field
        })

    return jsonify({
        "data": results,
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    })


# @blueprint.route("/leave")
# def leave():
#     um.reset_session()
#     return render_template(
#             "leave.html",
#             cluster=current_app.config[CONFIG_CLUSTER])


# @blueprint.route("/")
# @um.roles_required(ROLE_ACCESS, not_authorized)
# def show_overview():
#     return render_template(
#             "overview.html"
#             , username=um.get_user_fullname()
#             , cluster=current_app.config[CONFIG_CLUSTER]
#             , tables=queries.get_overview())


@blueprint.route("/", methods=["GET"])
def show():
    return render_template("show.html")
