"""ResQNet — Auth API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.auth import hash_password, verify_password, create_access_token
from app.db.engine import get_session
from app.db.models import User, Organization
from app.schemas.schemas import LoginRequest, TokenResponse, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=body.role,
        org_id=body.org_id,
    )
    session.add(user)
    await session.flush()
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role, org_id=user.org_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, email=user.email, name=user.name, role=user.role, org_id=user.org_id),
    )


@router.get("/me", response_model=UserOut)
async def me(session: AsyncSession = Depends(get_session)):
    from app.auth.auth import get_current_user
    # Handled via dependency in route
    raise HTTPException(status_code=400, detail="Use /auth/me with Authorization header")
