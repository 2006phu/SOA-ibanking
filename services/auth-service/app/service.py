import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User
from app.schemas import RegisterRequest


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: str, username: str, email: str) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Fetch user by unique username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch user by unique email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID, for_update: bool = False) -> User:
    """Fetch user by UUID, optionally with FOR UPDATE lock."""
    query = select(User).where(User.id == user_id)
    if for_update:
        query = query.with_for_update()
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """Authenticate a user by username and password."""
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """Register a new user with hashed password."""
    existing_username = await get_user_by_username(db, data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered",
        )

    existing_email = await get_user_by_email(db, data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    password_hash = hash_password(data.password)
    new_user = User(
        username=data.username,
        password_hash=password_hash,
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        balance=Decimal(str(data.balance)),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user


async def seed_user(db: AsyncSession, data) -> User:
    """Create a seed user with optional fixed UUID. Returns existing user if username already exists."""
    existing = await get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    password_hash = hash_password(data.password)
    user_kwargs = {
        "username": data.username,
        "password_hash": password_hash,
        "full_name": data.full_name,
        "phone": data.phone,
        "email": data.email,
        "balance": Decimal(str(data.balance)),
    }
    if data.id:
        user_kwargs["id"] = uuid.UUID(data.id)

    new_user = User(**user_kwargs)
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user
