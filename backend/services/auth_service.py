from datetime import datetime, timedelta, timezone
import hashlib
from threading import Lock
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# This registry fits the current single-process deployment without requiring a
# database migration. A shared revocation store remains necessary if the API is
# later run with multiple workers or replicas.
_revoked_refresh_tokens: dict[str, float] = {}
_revocation_lock = Lock()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid4()),
        "type": token_type,
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict) -> str:
    return _create_token(data, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_verified_token(token: str, expected_type: str) -> dict:
    credentials_error = _credentials_error()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if (
            payload.get("type") != expected_type
            or payload.get("sub") is None
        ):
            raise credentials_error
        if expected_type == "refresh" and payload.get("jti") is None:
            # Tokens issued before one-time rotation was introduced remain
            # usable once; their signature-derived identifier is not logged.
            payload["jti"] = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return payload
    except (JWTError, ValueError, TypeError):
        raise credentials_error


def _prune_revocations(now_timestamp: float) -> None:
    expired = [jti for jti, expires_at in _revoked_refresh_tokens.items() if expires_at <= now_timestamp]
    for jti in expired:
        del _revoked_refresh_tokens[jti]


def decode_token(token: str, expected_type: str) -> dict:
    payload = _decode_verified_token(token, expected_type)
    if expected_type == "refresh":
        now_timestamp = datetime.now(timezone.utc).timestamp()
        with _revocation_lock:
            _prune_revocations(now_timestamp)
            if payload["jti"] in _revoked_refresh_tokens:
                raise _credentials_error()
    return payload


def consume_refresh_token(token: str) -> dict:
    """Validate and atomically invalidate a refresh token before rotation."""
    payload = _decode_verified_token(token, "refresh")
    now_timestamp = datetime.now(timezone.utc).timestamp()
    with _revocation_lock:
        _prune_revocations(now_timestamp)
        if payload["jti"] in _revoked_refresh_tokens:
            raise _credentials_error()
        _revoked_refresh_tokens[payload["jti"]] = float(payload["exp"])
    return payload


def revoke_refresh_token(token: str) -> bool:
    """Revoke a valid refresh token; return False for invalid/expired input."""
    try:
        payload = _decode_verified_token(token, "refresh")
    except HTTPException:
        return False
    now_timestamp = datetime.now(timezone.utc).timestamp()
    with _revocation_lock:
        _prune_revocations(now_timestamp)
        _revoked_refresh_tokens[payload["jti"]] = float(payload["exp"])
    return True


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials, "access")
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    return user


def require_role(role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in {role, "admin"}:
            raise HTTPException(status_code=403, detail=f"Access denied. Required role: {role}")
        return current_user

    return role_checker
