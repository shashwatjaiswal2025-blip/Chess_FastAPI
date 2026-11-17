from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
import chess
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from passlib.context import CryptContext
from backend.app.database.database import Game_History, get_db, User
from backend.app.schemas.schemas import Token, usercreate, userOut
from backend.app.authentication.authentication import create_access_token, current_user




router = APIRouter(prefix='', tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _game_result(game: Game_History, player_id: int) -> str:
    if game.moves and game.moves[-1].startswith("resign:"):
        resigned_player_id = int(game.moves[-1].split(":", 1)[1])
        return "Loss" if resigned_player_id == player_id else "Win"

    board = chess.Board()
    for move in game.moves:
        board.push_uci(move)

    if not board.is_checkmate():
        return "Draw"

    winner_id = (
        game.white_player_id
        if board.turn == chess.BLACK
        else game.black_player_id
    )
    return "Win" if winner_id == player_id else "Loss"

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

@router.get('/games/me')
async def get_current_user_games(
    user: userOut = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Game_History)
        .options(
            joinedload(Game_History.white_player),
            joinedload(Game_History.black_player),
        )
        .where(
            or_(
                Game_History.white_player_id == user.id,
                Game_History.black_player_id == user.id,
            )
        )
        .order_by(Game_History.recorded_at.desc())
    )
    history_games = (await session.execute(stmt)).scalars().all()

    return [
        {
            "id": game.id,
            "opponent": (
                game.black_player.username
                if game.white_player_id == user.id
                else game.white_player.username
            ),
            "result": _game_result(game, user.id),
            "created_at": game.recorded_at,
        }
        for game in history_games
    ]


@router.get('/{user_id}/games')
async def get_user_games(user_id: int, session: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = (
        select(Game_History)
        .options(
            joinedload(Game_History.white_player),
            joinedload(Game_History.black_player),
        )
        .where(
            or_(
                Game_History.white_player_id == user_id,
                Game_History.black_player_id == user_id,
            )
        )
        .order_by(Game_History.recorded_at.desc())
    )

    history_games = (await session.execute(stmt)).scalars().all()
    
    return history_games