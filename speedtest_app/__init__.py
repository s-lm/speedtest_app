#!/usr/bin/env python3

import logging
import atexit
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .database import db
from . import routing
from . import database_init
from .authlib_client import init_oauth
from .run_speedtest import run_speedtest


def create_app(base_config = None):
    if base_config is None:
        base_config = {}
    base_config.update(
        # SESSION_COOKIE_SECURE   = True,
        # SESSION_COOKIE_HTTPONLY = True,
        # SESSION_COOKIE_SAMESITE = "Lax",
    )

    app = Flask(__name__)
    app.config.from_object(__name__)
    app.config.update(base_config)
    app.config.from_envvar("SPEEDTEST_SETTINGS", silent=True)


    @app.context_processor
    def inject_config():
        return dict(ENABLE_OIDC=app.config.get("ENABLE_OIDC", False))

    # init oidc
    init_oauth(app)

    # init logging
    logging.basicConfig(
        level = app.config["LOGLEVEL"].upper(),
        format = app.config["LOGFORMAT"],
        handlers = [logging.StreamHandler()])

    # init database
    db.init_app(app)
    if app.config.get("DB_CREATE_DB", False):
        with app.app_context():
            db.create_all()

    # register routes
    app.register_blueprint(routing.blueprint)

    # register dabase init
    app.register_blueprint(database_init.blueprint)

    # init scheduler and function to run speedtest
    def run_speedtest_with_context():
        with app.app_context():
            run_speedtest()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_speedtest_with_context, trigger="cron", hour="*/6", minute="15",)
    scheduler.start()

    # clean shutdown
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app