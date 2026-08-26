from datetime import datetime, timedelta
import logging

from jose import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User


logger = logging.getLogger(__name__)



# ✅ OAuth2 для извлечения токена из заголовка
oauth2_scheme = HTTPBearer()

# Используем Argon2
ph = PasswordHasher()


def normalize_login(login: str) -> str:
    return login.strip().lower()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True

    except VerifyMismatchError:
        return False


def get_user_by_login(
    db: Session,
    login: str
):
    normalized_login = normalize_login(login)

    return (
        db.query(User)
        .filter(User.login == normalized_login)
        .first()
    )


def register_user(
    db: Session,
    login: str,
    username: str,
    password: str
):
    login = normalize_login(login)
    username = username.strip()

    existing_user = get_user_by_login(
        db,
        login
    )

    if existing_user:
        logger.warning(
            "Registration failed: login already exists login=%s",
            login,
        )
        raise ValueError("Login already exists")

    new_user = User(
        login=login,
        username=username,
        password_hash=hash_password(password),
        bio="",
        birthday="",
        avatar=None,
        usernameid="temp",
        accountid="temp"
    )

    db.add(new_user)
    db.flush()

    new_user.usernameid = f"@user_{new_user.id}"
    new_user.accountid = f"acc_{new_user.id}"

    db.commit()
    db.refresh(new_user)

    logger.info(
        "User registered successfully: user_id=%s login=%s",
        new_user.id,
        login,
    )

    return new_user


def authenticate_user(
    db: Session,
    login: str,
    password: str
):
    user = get_user_by_login(
        db,
        login
    )

    if not user:
        logger.warning(
            "Authentication failed: user not found login=%s",
            normalize_login(login),
        )
        return None

    if not verify_password(
        password,
        user.password_hash
    ):
        logger.warning(
            "Authentication failed: invalid password user_id=%s",
            user.id,
        )
        return None

    logger.info(
        "User authenticated successfully: user_id=%s",
        user.id,
    )

    return user


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = (
        datetime.utcnow()
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    logger.debug(
        "Access token created: subject=%s",
        data.get("sub"),
    )

    return token