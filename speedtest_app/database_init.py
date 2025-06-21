import click
from flask import Blueprint
from flask.cli import with_appcontext
from .database import db

blueprint = Blueprint("database_init", __name__, cli_group=None)

@blueprint.cli.command("database_init")
@click.option("-d", "--drop", count=True)
@with_appcontext
def database_init(drop):
    if drop > 0:
        db.drop_all()
    db.create_all()
