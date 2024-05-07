import time

from app.ext.database import DB as db


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_number = db.Column(db.String(80), unique=True, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    account_type = db.Column(db.String(80), nullable=False)
    created_date = db.Column(db.Integer, nullable=False, default=time.time())
    status = db.Column(db.String(80), nullable=False, default="active")
    interest_rate = db.Column(db.Float, nullable=False)
    transactions = db.relationship("Transaction", backref="accounts", lazy=True)
