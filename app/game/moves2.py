from app.game.chess_functions import make_move,check_mate, is_check
from fastapi import HTTPException, WebSocket
from app.game.models import WaitingPlayer, GameRoom


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
                    await make_move(move, room.board)
                except HTTPException as exc:
                    await websocket.send_json({
                        "type": "error",
                        "message": exc.detail,
                    })
                    continue

                if await check_mate(room.board):
                    await websocket.send_json({
                        "type": "checkmate",
                        "message": "Checkmate! Game over.",
                        "winner": player.player_id,
                    })
                
                    break

                elif await is_check(room.board):
                    await websocket.send_json({
                        "type": "check",
                        "message": "Check!",
                    })


                board_state = room.board.fen()

            for room_player in room.players:
                await room_player.websocket.send_json({
                    "type": "board_state",
                    "board_state": board_state,
                })

        


