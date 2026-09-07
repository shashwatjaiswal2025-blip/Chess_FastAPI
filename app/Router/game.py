import asyncio
from dataclasses import dataclass, field
from uuid import uuid4
import chess
from app.authentication.authentication import current_user
from app.schemas.schemas import userOut
from app.game.moves2 import handle_game
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends


router = APIRouter(prefix="/game", tags=["game"])

@dataclass
class WaitingPlayer:
	player_id: str
	websocket: WebSocket
	matched: asyncio.Event = field(default_factory=asyncio.Event)
	room: "GameRoom | None" = None

@dataclass
class GameRoom:
	game_id: str
	players: list[WaitingPlayer] = field(default_factory=list)
	board: chess.Board = field(default_factory=chess.Board)
	board_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

class MatchmakingManager:
	def __init__(self) -> None:
		self.waiting_players: list[WaitingPlayer] = []
		self.game_rooms: dict[str, GameRoom] = {}
		self.lock = asyncio.Lock()

	async def join(self, websocket: WebSocket, user: userOut) -> tuple[WaitingPlayer, GameRoom | None]:
		player = WaitingPlayer(player_id=str(user.id), websocket=websocket)

		async with self.lock:#this part of code can run only with one user at a time, due to this lock and line
			if self.waiting_players:
				opponent = self.waiting_players.pop(0)
                
				room = GameRoom(
					game_id=str(uuid4()),
					players=[opponent, player],
				)
				self.game_rooms[room.game_id] = room
				opponent.room = room
				opponent.matched.set()
				return player, room

			self.waiting_players.append(player)
			return player, None

	async def leave(self, player: WaitingPlayer, room: GameRoom | None) -> None:
		async with self.lock:
			if player in self.waiting_players:
				self.waiting_players.remove(player)

			if room and room.game_id in self.game_rooms:
				del self.game_rooms[room.game_id]

	async def send_to_opponent(self, room: GameRoom, player: WaitingPlayer, message: dict) -> None:
		opponent = next(opponent for opponent in room.players if opponent.player_id != player.player_id)
		await opponent.websocket.send_json(message)


matchmaking = MatchmakingManager()


@router.websocket("/ws")
async def find_game(websocket: WebSocket, usercred: userOut = Depends(current_user)) -> None:
	await websocket.accept()
	player, room = await matchmaking.join(websocket, usercred)
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

				if matched_task in done: # #if matched user found, then get the room of the matched user
					room = player.room 
					break

				disconnect_task.result() # this raises WebSocketDisconnect if the user disconnected
				
		if sends_match_event:
			for room_player in room.players:
				await room_player.websocket.send_json({
					"type": "matched",
					"game_id": room.game_id,
					"game": "chess",
					"players": [room_player.player_id for room_player in room.players],
				})

		await handle_game(websocket, player, room)
	except WebSocketDisconnect:
		pass
	finally:
		await matchmaking.leave(player, room)
