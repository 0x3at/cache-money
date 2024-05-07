from flask_sqlalchemy import (
    SQLAlchemy,
)  # ? https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/

DB = _db = SQLAlchemy()


def register_extension(app):
    DB.init_app(app)

    from ..datalayer import User, Account, Transaction

    with app.app_context():
        DB.create_all()

    app.logger.info("Database extension registered.")

    return DB
