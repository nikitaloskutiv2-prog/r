from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services import auth_service, rate_limit_service
from app.core.deps import get_current_user
import logging


logger = logging.getLogger(__name__)
router = APIRouter()


class UserRegisterRequest(BaseModel):

    login: str = Field(
        min_length=3,
        max_length=100
    )

    username: str = Field(
        min_length=1,
        max_length=100
    )

    password: str = Field(
        min_length=4,
        max_length=128
    )


class UserLoginRequest(BaseModel):

    login: str = Field(
        min_length=1,
        max_length=100
    )

    password: str = Field(
        min_length=4,
        max_length=128
    )


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"

    user_id: int
    username: str


@router.post(
    "/register",
    response_model=TokenResponse
)
def register(
    request: Request,
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limit_service.check_register_rate_limit(client_ip):
        logger.warning(
            "Registration rate limit exceeded: ip=%s login=%s",
            client_ip,
            user_data.login,
        )

        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток регистрации. Пожалуйста, повторите попытку позже."
        )
    
    try:
        new_user = auth_service.register_user(
            db=db,
            login=user_data.login,
            username=user_data.username,
            password=user_data.password
        )
        rate_limit_service.record_registration(client_ip)
    except ValueError as e:
        logger.warning(
            "Registration failed: login=%s reason=%s",
            user_data.login,
            str(e),
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    logger.info(
        "User registered: user_id=%s username=%s",
        new_user.id,
        new_user.username,
    )

    token = auth_service.create_access_token({
        "sub": new_user.accountid
    })

    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        username=new_user.username
    )


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    request: Request,
    user_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limit_service.check_login_rate_limit(
        client_ip,
        user_data.login
    ):
        logger.warning(
            "Login rate limit exceeded: ip=%s login=%s",
            client_ip,
            user_data.login,
        )

        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток входа. Пожалуйста, повторите попытку позже."
        )
    user = auth_service.authenticate_user(
        db,
        user_data.login,
        user_data.password
    )

    if not user:
        rate_limit_service.record_failed_login(
            client_ip,
            user_data.login
        )
        logger.warning(
            "Login failed: login=%s",
            user_data.login,
        )

        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пороль"
        )
    
    rate_limit_service.reset_login_rate_limit(
        client_ip,
        user_data.login
    )


    token = auth_service.create_access_token({
        "sub": user.accountid
    })

    logger.info(
        "User logged in: user_id=%s username=%s",
        user.id,
        user.username,
    )

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username
    )



@router.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "accountid": current_user.accountid,
        "username": current_user.username,
        "usernameid": current_user.usernameid,
        "bio": current_user.bio,
        "birthday": current_user.birthday,
        "avatar": current_user.avatar
    }