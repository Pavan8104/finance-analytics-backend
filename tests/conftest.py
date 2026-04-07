"""
Pytest fixtures for the Finance Analytics API test suite.

Strategy:
  - Use an in-memory SQLite database for complete test isolation.
  - Override the `get_db` dependency so tests never touch the real database.
  - Provide ready-to-use authenticated HTTP clients for each role.
  - Each test function gets a fresh database state via function-scoped fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set TEST environment BEFORE importing app modules to skip file logging
import os
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.core.database import Base, get_db          # noqa: E402
from app.main import create_app                      # noqa: E402
from app.core.security import get_password_hash      # noqa: E402
from app.models.user import User, RoleEnum           # noqa: E402
from app.models.transaction import Transaction, TransactionType  # noqa: E402


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"   # in-memory, fastest possible

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """Provide a transactional test database session."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Application client with DB override
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db):
    """Return a TestClient with the DB dependency overridden."""
    app = create_app()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db) -> User:
    user = User(
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("Admin1234!"),
        role=RoleEnum.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def analyst_user(db) -> User:
    user = User(
        email="analyst@test.com",
        full_name="Test Analyst",
        hashed_password=get_password_hash("Analyst1234!"),
        role=RoleEnum.analyst,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def viewer_user(db) -> User:
    user = User(
        email="viewer@test.com",
        full_name="Test Viewer",
        hashed_password=get_password_hash("Viewer1234!"),
        role=RoleEnum.viewer,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db) -> User:
    user = User(
        email="inactive@test.com",
        hashed_password=get_password_hash("Inactive1234!"),
        role=RoleEnum.viewer,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Authenticated client fixtures
# ---------------------------------------------------------------------------

def _get_token(client: TestClient, email: str, password: str) -> str:
    """Helper to log in and extract the access token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def admin_client(client, admin_user):
    """TestClient authenticated as admin."""
    token = _get_token(client, "admin@test.com", "Admin1234!")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def analyst_client(client, analyst_user):
    """TestClient authenticated as analyst."""
    token = _get_token(client, "analyst@test.com", "Analyst1234!")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def viewer_client(client, viewer_user):
    """TestClient authenticated as viewer."""
    token = _get_token(client, "viewer@test.com", "Viewer1234!")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ---------------------------------------------------------------------------
# Transaction fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_transaction(db, viewer_user) -> Transaction:
    tx = Transaction(
        amount=500.00,
        type=TransactionType.income,
        category="Salary",
        notes="Monthly salary",
        owner_id=viewer_user.id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
