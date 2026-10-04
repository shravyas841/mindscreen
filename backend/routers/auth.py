from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.auth import UserCreate, LoginRequest, TokenResponse
from services.auth_service import (
    create_access_token,
    create_refresh_token,
    consume_refresh_token,
    get_current_user,
    hash_password,
    revoke_refresh_token,
    verify_password,
)
from pydantic import BaseModel
from middleware.rate_limit import limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    if not user_data.has_consented:
        raise HTTPException(status_code=400, detail="Research disclaimer acknowledgement is required")
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        name=user_data.name,
        has_consented=user_data.has_consented,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute", key_func=get_remote_address)
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == login_data.email).first()
    
    if not db_user or not verify_password(login_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute", key_func=get_remote_address)
async def refresh_token(request: Request, refresh_request: RefreshRequest, db: Session = Depends(get_db)):
    payload = consume_refresh_token(refresh_request.refresh_token)
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    token_data = {"sub": str(user.id)}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute", key_func=get_remote_address)
async def logout(request: Request, refresh_request: RefreshRequest):
    # Keep logout idempotent and avoid revealing whether a supplied token was valid.
    revoke_refresh_token(refresh_request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role, "has_consented": current_user.has_consented}
