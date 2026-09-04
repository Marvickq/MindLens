"""
Auth API — Counselor login / JWT management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.counselor import User, Organization
from app.utils.security import verify_password, create_access_token, hash_password
from app.schemas.schemas import LoginRequest, TokenResponse, SignupRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token(
        data={
            "sub": str(user.id),
            "org": str(user.organization_id),
            "role": user.role.value,
        }
    )
    return TokenResponse(
        access_token=token,
        user_name=user.name,
        role=user.role.value,
    )


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == payload.email)).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    org = db.exec(select(Organization)).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No organization found",
        )
    
    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        organization_id=org.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(
        data={
            "sub": str(new_user.id),
            "org": str(new_user.organization_id),
            "role": new_user.role.value,
        }
    )
    return TokenResponse(
        access_token=token,
        user_name=new_user.name,
        role=new_user.role.value,
    )
