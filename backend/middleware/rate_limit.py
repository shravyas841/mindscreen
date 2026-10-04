from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import JWTError, jwt

from config import settings


def get_rate_limit_key(request) -> str:
    """Use a stable user key for valid access tokens and IP otherwise."""
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") == "access" and payload.get("sub") is not None:
                return f"user:{payload['sub']}"
        except (JWTError, ValueError, TypeError):
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_rate_limit_key)
