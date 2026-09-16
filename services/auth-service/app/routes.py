import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app import service
from app.database import get_db
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    SeedUserRequest,
    TokenResponse,
    UserResponse,
    VerifyResponse,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract Bearer token from authorization header."""
    if credentials and credentials.credentials:
        return credentials.credentials

    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        elif len(parts) == 1:
            return parts[0]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authorization token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=TokenResponse, summary="User Login")
async def login(
    request_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user with username and password.
    Returns access token and user profile information.
    """
    user = await service.authenticate_user(db, request_data.username, request_data.password)
    access_token = service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, summary="Get Current User")
async def get_me(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode JWT token and return currently authenticated user info.
    """
    payload = service.decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identity claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await service.get_user_by_id(db, user_uuid)
    return UserResponse.model_validate(user)


@router.get("/verify", response_model=VerifyResponse, summary="Verify Token for API Gateway")
async def verify_token(
    token: str = Depends(get_token_from_request),
):
    """
    Internal endpoint for Gateway to verify tokens.
    Decodes and validates token, returning user_id, username, and email.
    """
    payload = service.decode_access_token(token)
    user_id = payload.get("sub")
    username = payload.get("username")
    email = payload.get("email")

    if not user_id or not username or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return VerifyResponse(
        user_id=str(user_id),
        username=username,
        email=email,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="User Registration")
async def register(
    request_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    """
    user = await service.register_user(db, request_data)
    return UserResponse.model_validate(user)


@router.post("/seed-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Seed User (Dev)")
async def seed_user(
    request_data: SeedUserRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a seed user with optional fixed UUID. For development/testing only.
    """
    user = await service.seed_user(db, request_data)
    return UserResponse.model_validate(user)
