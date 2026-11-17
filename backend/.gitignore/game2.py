
from typing import Optional
from app.authentication.authentication import current_user
from fastapi import APIRouter, Response, status, HTTPException, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.database.database import Active_Game, User, get_db,Game,waiting_player
from app.schemas.schemas import userOut as userout,legalmovesin
from app.game.moves import get_legal_moves as calculate_legal_moves,checks_mate,active_to_Game,timecheck,time_update
import chess

router = APIRouter(prefix="/game", tags=["game"])

async def time_update_and_check(game, db):
    await time_update(game, db)
    if timecheck(game):
        winner = game.black_player_id if game.time_left_white <= 0 else game.white_player_id
        await active_to_Game(game, winner, db)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Time's up! Player {winner} wins.")


@router.get("/new")
async def create_new_game(db: AsyncSession = Depends(get_db),usercred: userout= Depends(current_user)):
    
    # Check if user is already in an active game
    stmt = select(Active_Game).where(
        (Active_Game.white_player_id == usercred.id) | (Active_Game.black_player_id == usercred.id)
    )
    result = await db.execute(stmt)
    active_game = result.scalar_one_or_none()
    if active_game:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already in an active game")
        
    
    # Check if user is already in the waiting list
    stmt = select(waiting_player).where(waiting_player.user_id == usercred.id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already in the waiting list")
    
    # Check if there is a waiting player
    stmt = select(waiting_player)
    result = await db.execute(stmt)
    waiting_players = result.scalars().all()
    if not waiting_players:
        new_waiting_player = waiting_player(user_id=usercred.id)
        db.add(new_waiting_player)
        await db.commit()
        await db.refresh(new_waiting_player)
        return {"message": "Added to waiting list"}
    #change it to make sure it is wasy to move over to websocket in future

    black_player = waiting_players[0]
    

    new_game = Active_Game(
        white_player_id=usercred.id,
        black_player_id=black_player.user_id,
        time_left_white=300,  # 5 minutes in seconds
        time_left_black=300,  
        board_state=chess.Board().fen(), #initialise board
        moves=""
    )

    
    db.add(new_game)
    db.delete(black_player)
    await db.commit()
    await db.refresh(new_game)
    return new_game

@router.get("/status")
async def get_game_status(usercred: userout = Depends(current_user), db: AsyncSession = Depends(get_db)):
#to check if user is in active game or waiting list or none of them
    
    stmt = select(Active_Game).where(
        (Active_Game.white_player_id == usercred.id) | (Active_Game.black_player_id == usercred.id)
    )
    result = await db.execute(stmt)
    active_game = result.scalar_one_or_none()
    if active_game:
        return {"status": "active", "game_id": active_game.id}
    
    stmt = select(waiting_player).where(waiting_player.user_id == usercred.id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return {"status": "waiting"}
    
    return {"status": "none"}


@router.get("/{id}")
async def get_game(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Active_Game).where(Active_Game.id == id)
    result = await db.execute(stmt)
    game = result.scalar_one_or_none()
    if game is None:
        stmt = select(Game).where(Game.id == id)
        result = await db.execute(stmt)
        game = result.scalar_one_or_none()
        if game is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
        return game
    
    await time_update_and_check(game, db)
    
    return game

@router.get("/{game_id}/legal_moves")
async def get_game_legal_moves(game_id: int, legalmoves: legalmovesin = Depends(), usercred: userout = Depends(current_user), db: AsyncSession = Depends(get_db)):
    
    
    stmt = select(Active_Game).where(Active_Game.id == game_id)
    result = await db.execute(stmt)
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    
    await time_update_and_check(game, db)

    
    if game.white_player_id != usercred.id and game.black_player_id != usercred.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a player in this game")
    
    board = chess.Board(game.board_state)
    if (board.turn and game.white_player_id != usercred.id) or (not board.turn and game.black_player_id != usercred.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="It's not your turn")
    
    legal_moves = calculate_legal_moves(piece=legalmoves.piece, position=legalmoves.position, board_state=game.board_state)

    return legal_moves

@router.post("/{game_id}/move")
async def make_move(game_id: int, move: str, usercred: userout = Depends(current_user),db: AsyncSession=Depends(get_db)):
     

    
    stmt = select(Active_Game).where(Active_Game.id == game_id)
    result = await db.execute(stmt)
    game = result.scalar_one_or_none()

    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    
    await time_update_and_check(game, db)

    if game.white_player_id != usercred.id and game.black_player_id != usercred.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a player in this game")
    
    board = chess.Board(game.board_state)
    if (board.turn and game.white_player_id != usercred.id) or (not board.turn and game.black_player_id != usercred.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="It's not your turn")
    


    try:
        chess_move = chess.Move.from_uci(move)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid move format")

    if chess_move not in board.legal_moves:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Illegal move")

    board.push(chess_move)
    game.board_state = board.fen()
    game.moves += move + " "

    
    
    await db.commit()
    await db.refresh(game)  # Refresh the game instance to get the latest data

    

    if checks_mate(game.board_state, 0):
        game.winner = game.white_player_id
        await db.commit()
        await active_to_Game(game, game.white_player_id,db)
        return {"message": "Checkmate! White wins!"}
    elif checks_mate(game.board_state, 1):
        game.winner = game.black_player_id
        await db.commit()
        await active_to_Game(game, game.black_player_id, db)
        return {"message": "Checkmate! Black wins!"}
    return {"message": "Move accepted", "board_state": game.board_state}
