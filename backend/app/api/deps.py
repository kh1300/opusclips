from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def _dev_user_payload() -> dict[str, str]:
    return {"sub": "dev-user", "email": "dev@example.local"}


def _decode_supabase_token(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if credentials is None:
        if settings.require_auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        return _dev_user_payload()

    if not settings.supabase_jwt_secret:
        if settings.require_auth:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET is required when auth is enabled",
            )
        return _dev_user_payload()

    try:
        return jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> User:
    payload = _decode_supabase_token(credentials)
    supabase_id = str(payload.get("sub") or "")
    if not supabase_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token does not include a subject")

    user = db.scalar(select(User).where(User.supabase_id == supabase_id))
    if user:
        return user

    user = User(supabase_id=supabase_id, email=payload.get("email"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

