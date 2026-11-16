from app.game.chess_functions import make_move,check_mate, is_check
from fastapi import HTTPException, WebSocket
from app.game.models import WaitingPlayer, GameRoom
from fastapi.websockets import WebSocketDisconnect


async def send_to_players(room: GameRoom, message: dict) -> None:
    for room_player in room.players:
        try:
            await room_player.websocket.send_json(message)
        except (WebSocketDisconnect, RuntimeError):
            continue


async def handle_game(websocket: WebSocket,player: WaitingPlayer, room: GameRoom) -> None:
    while True:
        message = await websocket.receive_json()
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

                board_state = room.board.fen()
                await send_to_players(room, {
                    "type": "board_state",
                    "board_state": board_state,
                    "move": move,
                })

                if await check_mate(room.board):
                    await send_to_players(room, {
                        "type": "checkmate",
                        "message": "Checkmate! Game over.",
                        "winner": player.player_id,
                    })
                    break
                elif await is_check(room.board):
                    await send_to_players(room, {
                        "type": "check",
                        "message": "Check!",
                    })

        
