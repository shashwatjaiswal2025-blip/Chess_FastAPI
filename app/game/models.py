import asyncio
import chess
from dataclasses import dataclass, field
from fastapi import WebSocket



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
