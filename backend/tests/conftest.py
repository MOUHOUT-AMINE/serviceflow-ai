import os
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://serviceflow:serviceflow@localhost:5433/serviceflow_test",
)

if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must target a database ending in '_test'")

# This must be set before the application database module is imported by tests.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("%", "%%"))
    command.upgrade(config, "head")

    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(test_engine: Engine) -> Generator[None, None, None]:
    with test_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE customers RESTART IDENTITY"))
    yield
    with test_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE customers RESTART IDENTITY"))


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def session_factory(test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=test_engine, expire_on_commit=False)
