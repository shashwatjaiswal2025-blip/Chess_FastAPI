import chess
from app.database.database import Game, Active_Game
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.schemas.schemas import game_board

async def validate_moves(move_uci: str, board: chess.Board, team: bool | None = None) -> chess.Move:
    """Validate a UCI move and return it without changing the board."""
    if not isinstance(move_uci, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Move must be a UCI string.",
        )

    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid move format.",
        )

    if team is not None and board.turn != team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It is not this team's turn.",
        )

    if move not in board.legal_moves:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal move.",
        )

    return move

async def legal_moves(piece: tuple[int, int], board: chess.Board) -> list[str]:
    """Return a list of legal UCI moves for the given piece on the board."""
    legal_moves_list = []
    for move in board.legal_moves:
        if (move.from_square // 8, move.from_square % 8) == piece:
            legal_moves_list.append(move.uci())
    return legal_moves_list


async def make_move(move_uci: str, board: chess.Board) -> None:
    """Make a move on the board if it's legal."""
    move = await validate_moves(move_uci, board)
    board.push(move)
    
    return board


async def check_mate(board: chess.Board) -> bool:
    """Check if the current board state is checkmate."""
    return board.is_checkmate()

async def is_check(board: chess.Board) -> bool:
    """Check if the current board state is check."""
    return board.is_check()


