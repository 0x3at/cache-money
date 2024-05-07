from secrets import token_hex

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import (
    current_app as app,
)  # ? https://flask.palletsprojects.com/en/2.3.x/appcontext/
from flask_bcrypt import Bcrypt  # ? https://flask-bcrypt.readthedocs.io/en/latest/

from app.ext.database import DB as db
from app.datalayer import User, Account, Transaction


class UserRepository:
    @staticmethod
    def add_user(
        username: str,
        password: str,
        email: str,
        first_name: str,
        last_name: str,
        mobile: str,
        address: str,
    )-> bool:
        unique_args = {"username": username, "email": email, "mobile": mobile}

        for key, values in unique_args.items():
            if User.query.filter(getattr(User, key) == values).first():
                app.logger.error(
                    f"User attempted to be created with {key}: {values}, however User already exists!"
                )
                return False

        password_hash = Bcrypt().generate_password_hash(password).decode("utf-8")

        # ? Known issue with db.Model and pylint - https://github.com/pallets-eco/flask-sqlalchemy/issues/1312#issue-2127942077
        new_user = User(username=username, password_hash=password_hash, email=email, first_name=first_name, last_name=last_name, mobile=mobile, address=address)  # type: ignore
        try:
            db.session.add(new_user)
            db.session.commit()
            app.logger.info(
                f"User {username} created successfully with ID: {new_user.id}!"
            )
        except SQLAlchemyError as e:
            app.logger.error(f"Error creating User: {username} with error: {e}")
            db.session.rollback()
            return False

        return True
    
    @staticmethod
    def authenticate_user(username: str, password: str):
        user = User.query.filter_by(username=username).first()
        if not user:
            app.logger.info(
                f"User: {username} attempted to authenticate, but does not exist!"
            )
            return False

        if not Bcrypt().check_password_hash(user.password_hash, password):
            app.logger.info(
                f"User: {username} attempted to authenticate, but password was incorrect!"
            )
            return False
        else:
            app.logger.info(f"User: {username} authenticated successfully!")
            return True

    @staticmethod
    def get_user_id_by_username(username: str):
        user = User.query.filter_by(username=username).first()
        if not user:
            app.logger.error(
                f"User: {username} was attempted to be retrieved but does not exist!"
            )
            return None

        return user.id

    @staticmethod
    def update_basic_user_info(username: str, address=None, email=None, mobile=None):
        user = User.query.filter_by(username=username).first()
        if address is None and email is None and mobile is None:
            return False
        
        if not user:
            app.logger.error(
                f"User: {username} was attempted to be updated but does not exist!"
            )
            return False

        update_args = {"address": address, "email": email, "mobile": mobile}
        try:
            for key, value in update_args.items():
                if value:
                    setattr(user, key, value)
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(f"Error updating User: {username} with error: {e}")
            db.session.rollback()
            return False

        app.logger.info(f"User: {username} updated successfully!")

        return True

    @staticmethod
    def change_user_password(username: str, new_password: str):
        user = User.query.filter_by(username=username).first()
        if not user:
            app.logger.error(
                f"User: {username} was attempted to be updated but does not exist!"
            )
            return False

        password_hash = Bcrypt().generate_password_hash(new_password).decode("utf-8")
        try:
            user.password_hash = password_hash
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(f"Error updating User: {username} with error: {e}")
            db.session.rollback()
            return False

        app.logger.info(f"User: {username} updated successfully!")

        return True

    @staticmethod
    def change_username(new_username: str, old_username: str|None=None, id: int|None=None):
        if old_username == None and id == None:
            app.logger.error(f"Username Change Failed: User {id} attempted to change username to {new_username} but no ID or Username was provided!")
            return False
        if User.query.filter_by(username=new_username).first():
            app.logger.error(
                f"Username Change Failed: User {id} attempted to change username to {new_username} but it already exists!"
            )
            return False
        
        if old_username == None:
            user = User.query.get(id)
        else:
            user = User.query.filter_by(username=old_username).first()
            
        if not user:
            app.logger.error(f"Username Change Failed: User {id} does not exist!")
            return False

        user.username = new_username

        try:
            db.session.commit()
            app.logger.info(f"User: {id} updated successfully!")
        except SQLAlchemyError as e:
            app.logger.error(f"Error updating User: {id} with error: {e}")
            db.session.rollback()
            return False
        
        return True

    @staticmethod
    def disable_user(username: str | None = None, id: str | None = None):
        if username == None and id == None:
            app.logger.error(f"User: {id} was attempted to be disabled but no ID or Username was provided!")
            return False
        
        if username:
            user = User.query.filter_by(username=username).first()
        else:
            user = User.query.get(id)
        
        if not user:
            app.logger.error(
                f"User: {username} was attempted to be disabled but does not exist!"
            )
            return False
        else:
            user.disabled = True
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(f"Error disabling User: {username} with error: {e}")
            db.session.rollback()
            return False
        
        return True

    @staticmethod
    def enable_user(username: str | None = None, id: str | None = None):
        if username == None and id == None:
            app.logger.error(f"User: {id} was attempted to be enabled but no ID or Username was provided!")
            return False
        
        if username:
            user = User.query.filter_by(username=username).first()
        else:
            user = User.query.get(id)
        
        if not user:
            app.logger.error(
                f"User: {username} was attempted to be enabled but does not exist!"
            )
            return False
        else:
            user.disabled = False
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            app.logger.error(f"Error enabling User: {username} with error: {e}")
            db.session.rollback()
            return False
            
        return True


class AccountRepository:
    @staticmethod
    def create_bank_account(user_id: int, account_type: str, interest_rate: float):
        account_number = token_hex(16)
        if Account.query.filter_by(account_number=account_number).first():
            app.logger.error(
                f"Account attempted to be created with account number: {account_number}, however Account already exists! Retrying..."
            )
            AccountRepository.create_bank_account(user_id, account_type, interest_rate)

        # ? Known issue with db.Model and pylint - https://github.com/pallets-eco/flask-sqlalchemy/issues/1312#issue-2127942077
        new_account = Account(
            user_id=user_id,
            account_number=account_number,
            balance=0,
            account_type=account_type,
            interest_rate=interest_rate,
        )  # type:ignore
        try:
            db.session.add(new_account)
            db.session.commit()
            app.logger.info(
                f"Account {account_number} created successfully with ID: {new_account.id}!"
            )
        except SQLAlchemyError as e:
            app.logger.error(
                f"Error creating Account: {account_number} with error: {e}"
            )
            db.session.rollback()
            return None

        return True

    @staticmethod
    def get_account_by_id(account_id: int):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be retrieved but does not exist!"
            )
            return None

        return account

    @staticmethod
    def get_accounts_by_user_id(user_id: int):
        accounts = Account.query.filter_by(user_id=user_id).all()
        if not accounts:
            app.logger.error(f"User: {user_id} does not have any accounts!")
            return None

        return accounts

    @staticmethod
    def update_account_balance(account_id: int, amount: float):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be updated but does not exist!"
            )
            return None

        previous_balance = account.balance
        account.balance += amount
        try:
            db.session.commit()
            app.logger.info(
                f"Account: {account_id} balance updated from {previous_balance} to {account.balance}!"
            )
        except SQLAlchemyError as e:
            app.logger.error(f"Error updating Account: {account_id} with error: {e}")
            db.session.rollback()
            return None

        return True

    @staticmethod
    def update_account_interest(account_id: int, new_interest_rate: float):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be updated but does not exist!"
            )
            return None

        previous_interest = account.interest_rate
        account.interest_rate = new_interest_rate

        try:
            db.session.commit()
            app.logger.info(
                f"Account: {account_id} interest rate updated from {previous_interest} to {account.interest_rate}!"
            )
        except SQLAlchemyError as e:
            app.logger.error(f"Error updating Account: {account_id} with error: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def disable_account(account_id: int):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be disabled but does not exist!"
            )
            return None
        else:
            account.status = "disabled"
        try:
            db.session.commit()
            app.logger.info(f"Account: {account_id} disabled successfully!")
        except SQLAlchemyError as e:
            app.logger.error(f"Error disabling Account: {account_id} with error: {e}")
            db.session.rollback()
            return None

        return True

    @staticmethod
    def enable_account(account_id: int):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be enabled but does not exist!"
            )
            return None
        else:
            account.status = "active"
        try:
            db.session.commit()
            app.logger.info(f"Account: {account_id} enabled successfully!")
        except SQLAlchemyError as e:
            app.logger.error(f"Error enabling Account: {account_id} with error: {e}")
            db.session.rollback()
            return None

        return True

    @staticmethod
    def flag_account(account_id: int):
        account = Account.query.get(account_id)
        if not account:
            app.logger.error(
                f"Account: {account_id} was attempted to be flagged but does not exist!"
            )
            return None
        else:
            account.status = "flagged"
        try:
            db.session.commit()
            app.logger.info(f"Account: {account_id} flagged successfully!")
        except SQLAlchemyError as e:
            app.logger.error(f"Error flagging Account: {account_id} with error: {e}")
            db.session.rollback()
            return None

        return True


class TransactionRepository:
    @staticmethod
    def create_transaction(
        account_id: int,
        amount: float,
        description: str,
        status: str,
        transaction_type: str,
    ):
        # ? Known issue with db.Model and pylint - https://github.com/pallets-eco/flask-sqlalchemy/issues/1312#issue-2127942077
        post_tx_balance: float = float(
            Account.query.get(account_id).balance + amount # type:ignore
        )  # type:ignore
        try:
            transaction = Transaction(
                account_id=account_id,
                transaction_id=f"{account_id}_{token_hex(4)}",
                amount=amount,
                description=description,
                transaction_type=transaction_type,
                post_tx_balance=post_tx_balance,
            )  # type:ignore
        except SQLAlchemyError as e:
            app.logger.error(f"Error creating Transaction: {e}")
            db.session.rollback()
            return None

        return True

    @staticmethod
    def get_transaction_by_id(transaction_id: int):
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            app.logger.error(
                f"Transaction: {transaction_id} was attempted to be retrieved but does not exist!"
            )
            return None

        return transaction

    @staticmethod
    def get_transactions_by_account_id(account_id: int):
        transactions = Transaction.query.filter_by(account_id=account_id).all()
        if not transactions:
            app.logger.error(f"Account: {account_id} does not have any transactions!")
            return None

        return transactions

    @staticmethod
    def update_transaction_status(transaction_id: str, status: int):
        status_list = [
            "processing",
            "processed",
            "declined",
            "disputed",
            "refunded",
            "flagged",
        ]
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            app.logger.error(
                f"Transaction: {transaction_id} was attempted to be updated but does not exist!"
            )
            return None

        transaction.status = status_list[status]
        try:
            db.session.commit()
            app.logger.info(
                f"Transaction: {transaction_id} status updated to completed!"
            )
        except SQLAlchemyError as e:
            app.logger.error(
                f"Error updating Transaction: {transaction_id} with error: {e}"
            )
            db.session.rollback()
            return None

        return True

    @staticmethod
    def get_recent_transactions(account_id: int, limit: int = 10):
        transactions = (
            Transaction.query.filter_by(account_id=account_id).limit(limit).all()
        )
        if not transactions:
            app.logger.error(f"Account: {account_id} does not have any transactions!")
            return None

        return transactions

    @staticmethod
    def get_transaction_by_type(account_id: int, transaction_type: str):
        transactions = Transaction.query.filter_by(
            account_id=account_id, transaction_type=transaction_type
        ).all()
        if not transactions:
            app.logger.error(
                f"Account: {account_id} does not have any transactions of type {transaction_type}!"
            )
            return None

        return transactions
