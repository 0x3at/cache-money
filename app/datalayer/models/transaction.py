import time

from app.ext.database import DB as db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    transaction_id = db.Column(db.String(80), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False, default=time.time())
    description = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(80), nullable=False, default="processing")
    transaction_type = db.Column(db.String(80), nullable=False)
    post_tx_balance = db.Column(db.Float, nullable=False)
