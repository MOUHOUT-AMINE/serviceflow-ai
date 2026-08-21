from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import (
    get_access_token_expire_minutes,
    get_jwt_algorithm,
    get_jwt_secret_key,
)


password_hash = PasswordHash.recommended()

# A precomputed Argon2 hash used to keep unknown-user login attempts on the
# same password-verification path as attempts for existing users.
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "vIP56hHO1ULCXSiHQm+bmw$H7J/fJZHlszljgl30Tsptao6psEs6JehvsvWJUg6bT8"
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    return password_hash.verify(password, encoded_hash)


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=get_access_token_expire_minutes()),
    }
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=get_jwt_algorithm())


def decode_access_token(token: str) -> dict[str, object]:
    return jwt.decode(
        token, get_jwt_secret_key(), algorithms=[get_jwt_algorithm()]
    )
