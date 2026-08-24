from sqlalchemy import make_url

from app.config import get_database_url


def test_database_url_override_takes_precedence(monkeypatch):
    url = "postgresql+psycopg://user:password@localhost:5432/override"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("POSTGRES_DB", "ignored")

    assert get_database_url() == url


def test_database_url_safely_encodes_environment_credentials(monkeypatch):
    password = "p@ss:w/or?d#100%"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "serviceflow")
    monkeypatch.setenv("POSTGRES_PASSWORD", password)
    monkeypatch.setenv("POSTGRES_DB", "serviceflow")
    monkeypatch.setenv("DATABASE_HOST", "postgres")
    monkeypatch.setenv("DATABASE_PORT", "5432")

    url = get_database_url()

    assert make_url(url).password == password
    assert make_url(url).host == "postgres"
    assert "%40" in url
    assert "%25" in url
