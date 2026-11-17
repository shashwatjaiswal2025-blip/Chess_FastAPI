import asyncio

from fastapi import HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect

from backend.app.database.database import Game_History, SessionLocal
from backend.app.game.chess_functions import make_move
from backend.app.game.models import GameRoom, WaitingPlayer


async def send_to_players(room: GameRoom, message: dict) -> None:
    """Send a message to every connected player without blocking on one player."""
    await asyncio.gather(
        *(_send_to_player(room_player.websocket, message) for room_player in room.players)
    )


async def _send_to_player(websocket: WebSocket, message: dict) -> None:
    try:
        await websocket.send_json(message)
    except (WebSocketDisconnect, RuntimeError):
        pass


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


async def resign_game(room: GameRoom, player: WaitingPlayer) -> None:
    async with room.board_lock:
        if room.history_saved:
            return

        winner = next(
            opponent for opponent in room.players
            if opponent.player_id != player.player_id
        )
        room.move_history.append(f"resign:{player.player_id}")
        await save_game_history(room)
        await send_to_players(room, {
            "type": "resigned",
            "player": player.player_id,
            "winner": winner.player_id,
            "winner_color": (
                "white" if winner.player_id == room.white_player else "black"
            ),
        })


async def _send_error(websocket: WebSocket, message: str) -> None:
    await websocket.send_json({"type": "error", "message": message})


async def handle_game(
    websocket: WebSocket,
    player: WaitingPlayer,
    room: GameRoom,
) -> None:
    while True:
        message = await websocket.receive_json()
        message_type = message.get("type")

        if message_type == "resign":
            await resign_game(room, player)
            return

        if message_type != "move":
            await _send_error(websocket, "Unknown game message.")
            continue

        move = message.get("move")
        if not isinstance(move, str):
            await _send_error(websocket, "Move must be a UCI string.")
            continue

        async with room.board_lock:
            if room.board.turn != (player.player_id == room.white_player):
                await _send_error(websocket, "It is not your turn.")
                continue

            try:
                await make_move(move, room.board)
            except HTTPException as exc:
                await _send_error(websocket, str(exc.detail))
                continue

            room.move_history.append(move)
            game_over = room.board.is_game_over()
            checkmate = room.board.is_checkmate() if game_over else False
            in_check = room.board.is_check() if not game_over else False

            if game_over:
                await save_game_history(room)

            await send_to_players(room, {
                "type": "board_state",
                "board_state": room.board.fen(),
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
            elif in_check:
                await send_to_players(room, {
                    "type": "check",
                    "message": "Check!",
                })

            if game_over:
                return