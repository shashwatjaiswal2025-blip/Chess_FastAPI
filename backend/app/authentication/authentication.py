import jwt
import os
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from app.database.database import get_db, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.schemas import TokenData, userOut, Token


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-key-change-me-32")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": int(expires_at.timestamp())}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def verify_access_token(token: str, credential_exception: HTTPException) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id is None:
            raise credential_exception
        return TokenData(user_id=str(user_id), username=username)
    except PyJWTError:
        raise credential_exception


async def current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)) -> userOut:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = await verify_access_token(token, credential_exception)

    stmt = select(User).where(User.id == int(token_data.user_id))
    result = await session.execute(stmt)
    user = result.scalars().first()
    if user is None:
        print("User ID not in database")
        raise credential_exception

    return userOut(id=user.id, username=user.username)


async def websocket_current_user(websocket: WebSocket, session: AsyncSession = Depends(get_db)) -> userOut:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = websocket.query_params.get("token")
    if not token:
        raise credential_exception

    token_data = await verify_access_token(token, credential_exception)
    stmt = select(User).where(User.id == int(token_data.user_id))
    result = await session.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise credential_exception

    return userOut(id=user.id, username=user.username)