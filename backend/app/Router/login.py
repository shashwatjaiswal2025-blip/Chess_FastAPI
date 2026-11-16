from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from backend.app.database.database import get_db, User
from backend.app.schemas.schemas import Token, usercreate, userOut
from backend.app.authentication.authentication import create_access_token




router = APIRouter(prefix='', tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post('/login', response_model=Token)
async def login(user_cred: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user_cred.username)
    user = (await session.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credential")
    
    
    if not pwd_context.verify(user_cred.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credential")
    

    
    access_token = create_access_token(data={"user_id": user.id,"username": user.username})

    return Token(access_token=access_token, token_type="bearer")

@router.post('/signup', status_code=status.HTTP_201_CREATED, response_model=userOut)
async def signup(user_data: usercreate, session: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    existing_user = (await session.execute(stmt)).scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    # Create new user
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(username=user_data.username, email=user_data.email, password_hash=hashed_password)
    session.add(new_user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")
    await session.refresh(new_user)
    
    return new_user

@router.get('/{user_id}/games'){
    
}