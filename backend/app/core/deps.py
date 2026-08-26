from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services import auth_service
import logging

logger = logging.getLogger(__name__)

def get_current_user(
    token: str = Depends(auth_service.oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_str = token.credentials if hasattr(token, 'credentials') else token
        payload = jwt.decode(
            token_str,
            auth_service.SECRET_KEY, 
            algorithms=[auth_service.ALGORITHM]
        )
        accountid: str = payload.get("sub")  # 👈 Теперь это accountid
        
        if accountid is None:
            logger.warning(
                "Authentication failed: token does not contain accountid"
            )
            raise credentials_exception
            
    except JWTError:
        logger.warning(
            "Authentication failed: invalid or expired JWT",
        )
        raise credentials_exception
    
    # 👈 Ищем по accountid
    user = db.query(User).filter(User.accountid == accountid).first()
    
    if user is None:
        logger.warning(
            "Authentication failed: user not found accountid=%s",
            accountid,
        )
        raise credentials_exception

    if user.is_deleted:
        logger.warning(
            "Authentication failed: deleted user accountid=%s",
            accountid,
        )
        raise credentials_exception
    
    logger.debug(
        "User authenticated successfully: user_id=%s",
        user.id,
    )
    return user


