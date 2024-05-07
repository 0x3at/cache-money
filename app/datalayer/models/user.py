from app.ext.database import DB as db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disabled = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    mobile = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(128), nullable=False)
    accounts = db.relationship("Account", backref="user", lazy=True)
