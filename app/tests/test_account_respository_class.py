import pytest


from app import create_app
from app.repolayer import UserRepository, AccountRepository
from app.datalayer import User, Account
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


def test_create_bank_account_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    user_id = 1
    account_type = "savings"
    interest_rate = 1.5

    result = account_repo.create_bank_account(user_id, account_type, interest_rate)

    assert result is True
    assert db_session.query(Account).filter_by(user_id=user_id).first() is not None


def test_create_bank_account_failure(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    user_id = 99
    account_type = "savings"
    interest_rate = 1.5

    result = account_repo.create_bank_account(user_id, account_type, interest_rate)

    assert result is False
    assert db_session.query(Account).filter_by(user_id=user_id).first() is None


def test_get_account_by_id_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)

    account = db_session.query(Account).first()
    account_id = account.id

    retrieved_account = account_repo.get_account_by_id(account_id)
    assert retrieved_account is not False
    assert retrieved_account.id == account_id


def test_get_account_by_id_failure(db_session):
    user_repo = quick_add_test_user()
    account = AccountRepository.get_account_by_id(99)
    assert account is False


def test_get_accounts_by_user_id_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)

    accounts = AccountRepository.get_accounts_by_user_id(1)

    assert accounts != []


def test_get_accounts_by_user_id_failure(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)

    accounts = AccountRepository.get_accounts_by_user_id(99)

    assert accounts is False


def test_update_account_balance_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)
    account = db_session.query(Account).first()
    account_id = account.id

    result = account_repo.update_account_balance(account_id, 100.0)
    assert result is True
    assert db_session.query(Account).get(account_id).balance == 100.0


def test_update_account_balance_failure(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)
    account = db_session.query(Account).first()
    account_id = account.id

    result = account_repo.update_account_balance(99, 100.0)
    assert result is False
    assert db_session.query(Account).get(account_id).balance == 0.0


def test_disable_account_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)
    account = db_session.query(Account).first()
    account_id = account.id

    result = account_repo.disable_account(account_id)
    assert result is True
    assert db_session.query(Account).get(account_id).status == "disabled"


def test_disable_account_failure(db_session):
    user_repo = quick_add_test_user()
    result = AccountRepository.disable_account(999)
    assert result is False


def test_enable_account_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)
    account = db_session.query(Account).first()
    account_id = account.id

    result = account_repo.enable_account(account_id)
    assert result is True
    assert db_session.query(Account).get(account_id).status == "active"


def test_enable_account_failure(db_session):
    user_repo = quick_add_test_user()
    result = AccountRepository.enable_account(999)
    assert result is False


def test_flag_account_success(db_session):
    user_repo = quick_add_test_user()
    account_repo = AccountRepository()
    account_repo.create_bank_account(1, "checking", 0.5)
    account = db_session.query(Account).first()
    account_id = account.id

    result = account_repo.flag_account(account_id)
    assert result is True

    assert db_session.query(Account).get(account_id).status == "flagged"


def test_flag_account_failure(db_session):
    user_repo = quick_add_test_user()
    result = AccountRepository.flag_account(999)
    assert result is False
