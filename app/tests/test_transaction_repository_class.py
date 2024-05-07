import pytest


from app import create_app
from app.repolayer import UserRepository, AccountRepository, TransactionRepository
from app.datalayer import User, Account, Transaction
from app.ext.database import DB as db


def quick_add_test_user():
    user_repo = UserRepository()
    user_repo.add_user(
        username="test_user",
        password="secure_password",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        mobile="1234567890",
        address="123 Test St",
    )
    return user_repo


def setup_dependencies(db_session):
    quick_add_test_user()
    account_repo = AccountRepository()
    user_id = 1
    account_type = "savings"
    interest_rate = 1.5
    account_repo.create_bank_account(user_id, account_type, interest_rate)
    account = db_session.query(Account).first()

    return account


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()


def test_create_transaction_success(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    amount = 50.0
    description = "Gas Station"
    transaction_type = "credit"

    result = transaction_repo.create_transaction(
        account.id, amount, description, transaction_type
    )

    assert result is True
    transactions = db_session.query(Transaction).filter_by(account_id=account.id).all()
    assert len(transactions) == 1
    assert transactions[0].amount == amount
    assert transactions[0].description == description
    assert transactions[0].transaction_type == transaction_type


def test_create_transaction_failure(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    amount = 50.0
    description = "Gas Station"
    transaction_type = "credit"

    result = transaction_repo.create_transaction(
        -1, amount, description, transaction_type
    )
    assert result is False


def test_get_transaction_by_id_success(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    transaction_repo.create_transaction(account.id, 100.0, "Initial deposit", "credit")
    transaction = db_session.query(Transaction).first()

    retrieved_transaction = transaction_repo.get_transaction_by_id(
        transaction.transaction_id
    )
    assert retrieved_transaction is not False


def test_get_transaction_by_id_failure(db_session):
    transaction = TransactionRepository.get_transaction_by_id("nonexistent_id")  # type: ignore
    assert transaction is False


def test_get_transactions_by_account_id_success(db_session):
    account = setup_dependencies(db_session)
    TransactionRepository.create_transaction(
        account.id, 100.0, "Initial deposit", "credit"
    )
    transactions = TransactionRepository.get_transactions_by_account_id(account.id)
    assert transactions is not False
    assert len(transactions) == 1


def test_get_transactions_by_account_id_failure(db_session):
    account = setup_dependencies(db_session)

    transactions = TransactionRepository.get_transactions_by_account_id(account.id)
    assert transactions is False


def test_update_transaction_success(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    transaction_repo.create_transaction(account.id, 100.0, "Initial deposit", "credit")
    transaction = db_session.query(Transaction).first()

    result = TransactionRepository.update_transaction_status(
        transaction.transaction_id, 1
    )
    assert result is True
    db.session.refresh(transaction)
    refreshed_transaction = (
        db_session.query(Transaction)
        .filter_by(transaction_id=transaction.transaction_id)
        .first()
    )

    assert refreshed_transaction.status == "processed"


def test_update_transaction_failure(db_session):
    result = TransactionRepository.update_transaction_status("nonexistent_id", 1)
    assert result is False


def test_get_recent_transactions_limit_check(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    for _ in range(15):
        transaction_repo.create_transaction(account.id, 10.0, "Deposit", "credit")

    recent_transactions = TransactionRepository.get_recent_transactions(
        account.id, limit=10
    )
    assert len(recent_transactions) == 10  # type: ignore


def test_get_recent_transactions_success(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    for _ in range(10):
        transaction_repo.create_transaction(account.id, 10.0, "Deposit", "credit")

    recent_transactions = TransactionRepository.get_recent_transactions(account.id)
    assert len(recent_transactions) == 10  # type: ignore


def test_get_recent_transactions_failure(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    for _ in range(10):
        transaction_repo.create_transaction(account.id, 10.0, "Deposit", "credit")

    recent_transactions = TransactionRepository.get_recent_transactions(
        account.id, limit=5
    )
    assert len(recent_transactions) > 1  # type: ignore


def test_get_transactions_by_type_success(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    transaction_repo.create_transaction(account.id, 100.0, "Deposit", "credit")

    transactions = TransactionRepository.get_transaction_by_type(account.id, "credit")
    assert transactions is not False
    assert len(transactions) == 1


def test_get_transaction_by_type_failure(db_session):
    account = setup_dependencies(db_session)
    transaction_repo = TransactionRepository()
    transaction_repo.create_transaction(account.id, 100.0, "Deposit", "credit")

    transactions = TransactionRepository.get_transaction_by_type(account.id, "debit")
    assert transactions is False
