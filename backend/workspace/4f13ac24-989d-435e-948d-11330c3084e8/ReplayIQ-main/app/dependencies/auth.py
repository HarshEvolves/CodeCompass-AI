import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.dependencies.db import get_db
from app.models.user import User

# Configure OAuth2PasswordBearer to read Bearer tokens from Authorization headers.
# Note: tokenUrl is configured pointing to the auth login route.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR.strip('/')}/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency that decodes, validates the incoming JWT token, and retrieves the
    associated User model from the database.
    Raises 401 Unauthorized exceptions for expired, invalid, or missing tokens.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the signature and verify payload constraints
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Retrieve user from PostgreSQL matching the sub claim
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user
