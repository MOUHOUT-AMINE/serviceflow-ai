import os


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://serviceflow:serviceflow@localhost:5432/serviceflow"
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")
    return secret


def get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def get_access_token_expire_minutes() -> int:
    value = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    if value <= 0:
        raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
    return value
