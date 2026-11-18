from datetime import datetime
from contextlib import asynccontextmanager
import os
from time import timezone
from fastapi import FastAPI
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Integer, String, Boolean, DateTime, MetaData, text, func, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship
from dotenv import load_dotenv


load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "chessdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresspostgresql://"):
        return url.replace("postgresspostgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


POSTGRES_URL = _normalize_database_url(
    os.getenv("DATABASE_URL")
    or os.getenv("Database_URL")
    or (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
)

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    white_games: Mapped[list["Game_History"]] = relationship(
        foreign_keys="Game_History.white_player_id",
        back_populates="white_player",
    )
    black_games: Mapped[list["Game_History"]] = relationship(
        foreign_keys="Game_History.black_player_id",
        back_populates="black_player",
    )
    # Read-only combined relationship for all games (white or black)
    games: Mapped[list["Game_History"]] = relationship(
        primaryjoin=(
            "or_(User.id == Game_History.white_player_id, "
            "User.id == Game_History.black_player_id)"
        ),
        viewonly=True,
        order_by="Game_History.recorded_at.desc()",
    )


class Game_History(Base):
    __tablename__ = "chess_game_history"
    __table_args__ = (
        CheckConstraint("jsonb_typeof(moves) = 'array'", name="moves_must_be_array"),
        # Optional: prevent a user from playing against themselves
        CheckConstraint("white_player_id != black_player_id", name="players_must_differ"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    white_player_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    black_player_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    moves: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    white_player: Mapped["User"] = relationship(
        foreign_keys=[white_player_id],
        back_populates="white_games",
    )
    black_player: Mapped["User"] = relationship(
        foreign_keys=[black_player_id],
        back_populates="black_games",
    )
 
class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    white_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    black_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    moves: Mapped[str] = mapped_column(String, nullable=False)  # Store moves in PGN format
    result: Mapped[str] = mapped_column(String(10), nullable=True)  # e.g., "1-0", "0-1", "1/2-1/2", "Ongoing(NULL)"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())



class waiting_player(Base):
    __tablename__ = "waiting_players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    time:Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("300"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())