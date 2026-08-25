from pydantic import BaseModel
from typing import Optional

class game_board(BaseModel):
    id: int
    white_player: int = None
    black_player: int = None
    white_time: int
    black_time: int
    team_turn: int
    winner: Optional[int] = None
    
class game_move(BaseModel):
    game_id: int
    move: str

class legalmovesout(BaseModel):
    game_id: int
    legal_moves: list[str]

class legalmovesin(BaseModel):
    piece: str
    position: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

class userOut(BaseModel):
    id: int
    username: str

class usercreate(BaseModel):
    username: str
    email: str
    password: str