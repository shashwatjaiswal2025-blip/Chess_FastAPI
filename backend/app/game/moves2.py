from backend.app.game.chess_functions import make_move,check_mate, is_check
from fastapi import HTTPException, WebSocket
from backend.app.game.models import WaitingPlayer, GameRoom
from fastapi.websockets import WebSocketDisconnect
from backend.app.database.database import Game_History, SessionLocal

async def send_to_players(room: GameRoom, message: dict) -> None:
    for room_player in room.players:
        try:
            await room_player.websocket.send_json(message)
        except (WebSocketDisconnect, RuntimeError):
            continue


async def save_game_history(room: GameRoom) -> None:
    if room.history_saved:
        return

    if room.white_player is None or room.black_player is None:
        raise RuntimeError("Cannot save game history before both players are assigned.")

    history = Game_History(
        white_player_id=int(room.white_player),
        black_player_id=int(room.black_player),
        moves=list(room.move_history),
    )
    async with SessionLocal() as session:
        session.add(history)
        await session.commit()
    room.history_saved = True


async def handle_game(websocket: WebSocket,player: WaitingPlayer, room: GameRoom) -> None:
    while True:
        message = await websocket.receive_json()
        if message.get("type") == "resign":
            async with room.board_lock:
                if room.history_saved:
                    return
                winner_player = next(
                    opponent
                    for opponent in room.players
                    if opponent.player_id != player.player_id
                )
                room.move_history.append(f"resign:{player.player_id}")
                await save_game_history(room)
                await send_to_players(room, {
                    "type": "resigned",
                    "player": player.player_id,
                    "winner": winner_player.player_id,
                    "winner_color": "white" if winner_player.player_id == room.white_player else "black",
                })
            return

        if message["type"] == "move":
            move = message.get("move")
            if not isinstance(move, str):
                await websocket.send_json({
                    "type": "error",
                    "message": "Move must be a UCI string.",
                })
                continue

            async with room.board_lock:
                try:
                    if room.board.turn != (player.player_id == room.white_player):
                        await websocket.send_json({
                            "type": "error",
                            "message": "It is not your turn.",
                        })
                        continue
                    
                    await make_move(move, room.board)
                except HTTPException as exc:
                    await websocket.send_json({
                        "type": "error",
                        "message": exc.detail,
                    })
                    continue

                room.move_history.append(move)
                game_over = room.board.is_game_over()
                checkmate = await check_mate(room.board) if game_over else False
                if game_over:
                    await save_game_history(room)

                board_state = room.board.fen()
                await send_to_players(room, {
                    "type": "board_state",
                    "board_state": board_state,
                    "move": move,
                })

                if game_over:
                    if checkmate:
                        await send_to_players(room, {
                            "type": "checkmate",
                            "message": "Checkmate! Game over.",
                            "winner": player.player_id,
                        })
                    else:
                        await send_to_players(room, {
                            "type": "game_over",
                            "message": "Game over.",
                        })
                    break
                elif await is_check(room.board):
                    await send_to_players(room, {
                        "type": "check",
                        "message": "Check!",
                    })

        
