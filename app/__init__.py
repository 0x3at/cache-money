from flask import Flask
from .ext import database
from .ext import logger


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    app.config["DEBUG"] = True

    database.register_extension(app)
    logger.register_extension(app)

    app.logger.info("App pipeline finished building!")
    return app
