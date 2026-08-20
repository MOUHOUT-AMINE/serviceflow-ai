import os


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://serviceflow:serviceflow@localhost:5432/serviceflow"
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
