import asyncio
from collections import deque
from uuid import uuid4
import chess
from backend.app.authentication.authentication import websocket_current_user
from backend.app.schemas.schemas import userOut
from backend.app.game.moves2 import handle_game
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.app.game.models import WaitingPlayer, GameRoom


router = APIRouter(prefix="/game", tags=["game"])


class DuplicateActivePlayerError(Exception):
	"""Raised when an account already has an active game websocket."""


class MatchmakingManager:
	def __init__(self) -> None:
		self.waiting_players: deque[WaitingPlayer] = deque()
		self.game_rooms: dict[str, GameRoom] = {}
		self.active_players: dict[str, WaitingPlayer] = {}
		self.lock = asyncio.Lock()

	async def join(self, websocket: WebSocket, user: userOut) -> tuple[WaitingPlayer, GameRoom | None]:
		player = WaitingPlayer(player_id=str(user.id), websocket=websocket)

		async with self.lock:#this part of code can run only with one user at a time, due to this lock and line
			if player.player_id in self.active_players:
				raise DuplicateActivePlayerError

			self.active_players[player.player_id] = player
			if self.waiting_players:
				opponent = self.waiting_players.popleft()
                
				room = GameRoom(
					game_id=str(uuid4()),
					players=[opponent, player],
				)
				self.game_rooms[room.game_id] = room
				opponent.room = room
				player.room = room
				opponent.matched.set()
				return player, room

			self.waiting_players.append(player)
			return player, None

	async def leave(self, player: WaitingPlayer, room: GameRoom | None) -> None:
		async with self.lock:
			self.active_players.pop(player.player_id, None)

			try:
				self.waiting_players.remove(player)
			except ValueError:
				pass

			if room and room.game_id in self.game_rooms:
				del self.game_rooms[room.game_id]

	async def send_to_opponent(self, room: GameRoom, player: WaitingPlayer, message: dict) -> None:
		opponent = next(opponent for opponent in room.players if opponent.player_id != player.player_id)
		await opponent.websocket.send_json(message)

	async def active_connections(self) -> list[dict[str, str | None]]:
		async with self.lock:
			return [
				{
					"user_id": player.player_id,
					"room_id": player.room.game_id if player.room else None,
				}
				for player in self.active_players.values()
			]


matchmaking = MatchmakingManager()


@router.get("/active-websockets")
async def get_active_websockets() -> dict[str, list[dict[str, str | None]]]:
	return {"active_websockets": await matchmaking.active_connections()}


@router.websocket("/ws")
async def find_game(websocket: WebSocket, usercred: userOut = Depends(websocket_current_user)) -> None:
	await websocket.accept()
	player: WaitingPlayer | None = None
	room: GameRoom | None = None

	try:
		player, room = await matchmaking.join(websocket, usercred)
	except DuplicateActivePlayerError:
		await websocket.send_json({
			"type": "error",
			"message": "This account already has an active game.",
		})
		await websocket.close(code=1008, reason="Account already has an active game")
		return

	sends_match_event = room is not None

	try:
		if room is None:
			await websocket.send_json({
				"type": "waiting",
				"game": "chess",
				"message": "Waiting for another player",
			}) #send messgae that the use is waiting for opponent to be matched

            
			while room is None:
				matched_task = asyncio.create_task(player.matched.wait()) # creates task 1 that checks if user matched
				disconnect_task = asyncio.create_task(websocket.receive_text()) # creates task 2 that checks if user sent anything
				done, pending = await asyncio.wait(
					{matched_task, disconnect_task},
					return_when=asyncio.FIRST_COMPLETED,
				)   # checks for both events, taks1, task 2. 
				    #FIRST_COMPLETED means if anyone task is comepleted, the code moves forward
				
				for task in pending: # cancels task that is not completed
					task.cancel()
				await asyncio.gather(*pending, return_exceptions=True)

				if matched_task in done: # #if matched user found, then get the room of the matched user
					room = player.room 
					break

				disconnect_task.result() # this raises WebSocketDisconnect if the user disconnected
				
		if sends_match_event:
			for room_player in room.players:
				room.black_player = room.players[0].player_id
				room.white_player = room.players[1].player_id
				await room_player.websocket.send_json({
					"type": "matched",
					"game_id": room.game_id,
					"game": "chess",
					"players": [room_player.player_id for room_player in room.players],
					"player_color": "black" if room_player.player_id == room.black_player else "white",
				})
				

		await handle_game(websocket, player, room)
	except WebSocketDisconnect:
		pass
	finally:
		if player is not None:
			await matchmaking.leave(player, room)
