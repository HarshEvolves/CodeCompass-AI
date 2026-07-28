"""
CodeCompass Authentication Service Logic
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    """
    Registers a new user, saving their hashed password into the database.
    Raises HTTPException 400 if email is already taken.
    """
    # Check if the email already exists
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    # Hash the password and save
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password
    )

    db.add(db_user)
    await db.flush()  # Populates db_user.id automatically

    return db_user


async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> User:
    """
    Authenticates user credentials.
    Raises HTTPException 401 if authentication fails.
    """
    query = select(User).where(User.email == credentials.email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user account is inactive."
        )

    return user
