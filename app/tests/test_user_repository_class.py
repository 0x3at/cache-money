import pytest


from app import create_app
from app.repolayer import UserRepository
from app.datalayer import User
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


def test_add_user_success(db_session):
    # Given
    user_repo = UserRepository()
    username = "test_user"
    password = "secure_password"
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"
    mobile = "1234567890"
    address = "123 Test St"

    result = user_repo.add_user(
        username, password, email, first_name, last_name, mobile, address
    )

    assert result is not False
    assert db_session.query(User).filter_by(username=username).first() is not None


def test_add_user_failure_due_to_duplicate_username(db_session):
    user_repo = UserRepository()
    username = "test_user"
    password = "secure_password"
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"
    mobile = "1234567890"
    address = "123 Test St"

    first_result = user_repo.add_user(
        username, password, email, first_name, last_name, mobile, address
    )

    assert first_result is not False
    assert db_session.query(User).filter_by(username=username).first() is not None

    user_repo = UserRepository()
    username = "test_user"
    password = "secure_password"
    email = "test@example.com"
    first_name = "Test"
    last_name = "User"
    mobile = "1234567890"
    address = "123 Test St"

    result = user_repo.add_user(
        username, password, email, first_name, last_name, mobile, address
    )

    assert result is False
    assert db_session.query(User).filter_by(username=username).count() == 1


def test_authenticate_user_success(db_session):
    user_repo = quick_add_test_user()

    authentication_successful = user_repo.authenticate_user(
        "test_user", "secure_password"
    )

    assert authentication_successful is not False


def test_authenticate_user_failure(db_session):
    user_repo = quick_add_test_user()

    username_correct = user_repo.authenticate_user("test_userr", "secure_password")
    password_correct = user_repo.authenticate_user("test_user", "secure_passwordd")

    assert username_correct is False
    assert password_correct is False


def test_get_user_id_by_username_success(db_session):
    user_repo = quick_add_test_user()

    user_id = user_repo.get_user_id_by_username("test_user")

    assert user_id is not None
    assert user_id == 1


def test_get_user_id_by_username_failure(db_session):
    user_repo = quick_add_test_user()

    user_id = user_repo.get_user_id_by_username("test_useer")

    assert user_id is None


def test_update_basic_user_info_all_args_success(db_session):
    user_repo = quick_add_test_user()

    updated = user_repo.update_basic_user_info(
        "test_user",
        address="1010 test update st",
        email="datesting@gmail.com",
        mobile="0987654321",
    )

    user = db_session.query(User).filter_by(username="test_user").first()
    assert updated is not False
    assert user.address == "1010 test update st"
    assert user.email == "datesting@gmail.com"
    assert user.mobile == "0987654321"


def test_update_basic_user_info_some_args_success(db_session):
    user_repo = quick_add_test_user()
    pre_manipulated_user_data = (
        db_session.query(User).filter_by(username="test_user").first()
    )

    updated = user_repo.update_basic_user_info(
        "test_user", address="1010 test update st", email="datesting@gmail.com"
    )

    user = db_session.query(User).filter_by(username="test_user").first()
    assert updated is not False
    assert user.address == "1010 test update st"
    assert user.email == "datesting@gmail.com"
    assert user.mobile == pre_manipulated_user_data.mobile


def test_update_basic_user_info_all_args_failure(db_session):
    user_repo = quick_add_test_user()

    updated = user_repo.update_basic_user_info(
        "test_userr", "1010 test update st", "datesting@gmail.com", "0987654321"
    )

    assert updated is False


def test_update_basic_user_info_no_args_failure(db_session):
    user_repo = quick_add_test_user()

    updated = user_repo.update_basic_user_info("test_user")

    assert updated is False


def test_change_user_password_success(db_session):
    user_repo = quick_add_test_user()

    assert user_repo.change_user_password("test_user", "new_password") is True
    assert user_repo.authenticate_user("test_user", "new_password") is not False


def test_change_user_password_failure(db_session):
    user_repo = quick_add_test_user()

    assert user_repo.change_user_password("test_userr", "new_password") is False
    assert user_repo.authenticate_user("test_user", "new_password") is False


def test_change_username_success_with_username(db_session):
    user_repo = quick_add_test_user()

    assert (
        user_repo.change_username(new_username="new_username", old_username="test_user")
        is True
    )
    assert (db.session.query(User).filter_by(username="new_username").first()).username == "new_username"  # type: ignore


def test_change_username_success_with_id(db_session):
    user_repo = quick_add_test_user()

    assert user_repo.change_username(id=1, new_username="new_username") is True
    assert db.session.query(User).get(1).username == "new_username"  # type: ignore


def test_disable_user_success(db_session):
    user_repo = quick_add_test_user()

    assert user_repo.disable_user("test_user") is True
    assert db.session.query(User).filter_by(username="test_user").first().disabled == True  # type: ignore


def test_disable_user_failure(db_session):
    user_repo = quick_add_test_user()

    assert user_repo.disable_user("test_userr") is False
    assert db.session.query(User).filter_by(username="test_user").first().disabled == False  # type: ignore


def test_enable_user_success(db_session):
    user_repo = quick_add_test_user()

    user_repo.disable_user("test_user")

    assert user_repo.enable_user("test_user") is True
    assert db.session.query(User).filter_by(username="test_user").first().disabled == False  # type: ignore


def test_enable_user_failure(db_session):
    user_repo = quick_add_test_user()

    user_repo.disable_user("test_user")

    assert user_repo.enable_user("test_userr") is False
    assert db.session.query(User).filter_by(username="test_user").first().disabled == True  # type: ignore
