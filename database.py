from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Integer, String, Boolean, DateTime, MetaData, text, func, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column, Mapped

POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_DB="chessdb"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="password"
algorithm="HS256"


POSTGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_async_engine(POSTGRES_URL, echo=False)
Base = declarative_base(metadata=MetaData())
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async def get_db():
    async with SessionLocal() as session:
        yield session
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    white_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    black_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    moves: Mapped[str] = mapped_column(String, nullable=False)  # Store moves in PGN format
    result: Mapped[str] = mapped_column(String(10), nullable=True)  # e.g., "1-0", "0-1", "1/2-1/2", "Ongoing(NULL)"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Active_Game(Base):
    __tablename__ = "active_games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    white_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    black_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    time_left_white: Mapped[int] = mapped_column(Integer, nullable=False)  # Time left for white in seconds
    time_left_black: Mapped[int] = mapped_column(Integer, nullable=False)  # Time left for black in seconds
    board_state: Mapped[str] = mapped_column(String, nullable=False)  # FEN string
    moves: Mapped[str] = mapped_column(String, nullable=False)  # Store moves in PGN format
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_move_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class waiting_player(Base):
    __tablename__ = "waiting_players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    time:Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("300"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())