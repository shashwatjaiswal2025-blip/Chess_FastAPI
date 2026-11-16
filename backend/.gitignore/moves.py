'''
piece:
P= pawn
R= rook
N= knight
B= bishop
Q= queen
K= king


piece = (row,col)
board[row][col] = (piece, team)
'''
from app.schemas.schemas import legalmovesin
import chess
from app.database.database import Game, Active_Game
from datetime import datetime, timezone
from fastapi import HTTPException, status

def check_bounds(row, col, board):
    return 0 <= row < len(board) and 0 <= col < len(board[0])

def check_history(piece, board, team):
    # Placeholder to check the move history of a piece, To implement moves like castling and en passant.
    pass


def moves(piece, board, team):
    """Return a list of legal moves for the given piece on the board.

    This implementation currently supports pawn (`'P'`) forward and capture moves.
    - `piece` is a tuple `(row, col)`
    - `board` is a 2D list where each cell is either `None` or a tuple `(piece_char, team)`
    - `team` is the team identifier for the moving piece
    """
    legalappend = []
    row, col = piece
    tem_list=['P','R','N','B','Q','K']
    row,col=piece
    if not check_bounds(row, col, board):
        return legalappend

    P_board = board[row][col]

    if P_board is None or P_board[1] != team:
        return legalappend


    

    # Pawn moves (assumes pawns move to increasing row index)
    if P_board[0] == 'P' and P_board[1] == team:
        forward = row + 1
        # single forward
        if 0 <= forward < len(board):
            if board[forward][col] is None:
                legalappend.append((forward, col))
                # double forward from starting rank 1
                double_forward = row + 2
                if row == 1 and 0 <= double_forward < len(board) and board[double_forward][col] is None:
                    legalappend.append((double_forward, col))

            # captures
            for c in (col - 1, col + 1):
                if 0 <= c < len(board[0]):
                    target = board[forward][c]
                    if target is not None and target[1] != team:
                        legalappend.append((forward, c))
        #En passant
        if row == 4:  # En passant is only possible from the 5th rank (index 4)
            for c in (col - 1, col + 1):
                if 0 <= c < len(board[0]):
                    target = board[row][c]
                    if target is not None and target[0] == 'P' and target[1] != team:
                        if check_history((row, c), board, target[1]):  # Check if the opponent's pawn just moved two squares
                            legalappend.append((row + 1, c))


        return legalappend
    elif P_board[0] == "R" and P_board[1] == team:
        # Rook moves (horizontal and vertical)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            for i in range(1, len(board)):
                new_row, new_col = row + i * dr, col + i * dc
                if not (0 <= new_row < len(board) and 0 <= new_col < len(board[0])):
                    break
                target = board[new_row][new_col]
                if target is None:
                    legalappend.append((new_row, new_col))
                elif target[1] != team:
                    legalappend.append((new_row, new_col))
                    break
                else:
                    # friendly piece blocks movement
                    break
        return legalappend
    
    elif P_board[0] == "N" and P_board[1] == team:
        # Knight moves (L-shaped)
        for dr, dc in [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < len(board) and 0 <= new_col < len(board[0]):# checks if target in range
                target = board[new_row][new_col]
                if target is None or target[1] != team:
                    legalappend.append((new_row, new_col))
        return legalappend
    
    elif P_board[0] == "B" and P_board[1] == team:
        # Similar to rook but with diagonal moves
        # Bishop moves (diagonal)

        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for i in range(1, len(board)):
                new_row, new_col = row + i * dr, col + i * dc
                if not (0 <= new_row < len(board) and 0 <= new_col < len(board[0])):
                    break
                target = board[new_row][new_col]
                if target is None:
                    legalappend.append((new_row, new_col))
                elif target[1] != team:
                    legalappend.append((new_row, new_col))
                    break
                else:
                    # friendly piece blocks movement
                    break
        return legalappend

    elif P_board[0] == "Q" and P_board[1] == team:
        # Queen moves (combination of rook and bishop)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            for i in range(1, len(board)):
                new_row, new_col = row + i * dr, col + i * dc
                if not (0 <= new_row < len(board) and 0 <= new_col < len(board[0])):
                    break
                target = board[new_row][new_col]
                if target is None:
                    legalappend.append((new_row, new_col))
                elif target[1] != team:
                    legalappend.append((new_row, new_col))
                    break
                else:
                    # friendly piece blocks movement
                    break
        return legalappend

    elif P_board[0] == "K" and P_board[1] == team:
        # King moves (one square in any direction)
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < len(board) and 0 <= new_col < len(board[0]):
                target = board[new_row][new_col]
                if target is None or target[1] != team:
                    legalappend.append((new_row, new_col))
        
        #Castling
        if check_history((row, col), board, team):  # Check if the king has not moved
            # Kingside castling
            if  check_history((row, col + 3), board, team) and all(board[row][c] is None for c in range(col + 1, col + 3)) :
                #check if rook moved and if squares between king and rook are empty
                
                legalappend.append((row, col + 2))
            # Queenside castling

            if check_history((row, col - 4), board, team) and all(board[row][c] is None for c in range(col - 1, col - 4, -1)):
                #check if rook moved and if squares between king and rook are empty
                legalappend.append((row, col - 2))
        
        return legalappend


    else:
        print("Unsupported piece type or team.")
        return legalappend
    

def get_legal_moves(piece, position, board_state):
    board = chess.Board(board_state)
    square = chess.parse_square(position)

    legal_moves = [
        move for move in board.legal_moves
        if move.from_square == square
    ]

    return legal_moves

def checks_mate(board_state, team):
    board = chess.Board(board_state)
    if team == 0:  # Assuming team 0 is white
        return board.is_checkmate() and board.turn == chess.WHITE
    else:  # Assuming team 1 is black
        return board.is_checkmate() and board.turn == chess.BLACK
    
async def active_to_Game(active_game,winner,db):
    g= Game(
        id=active_game.id,
        white_player_id=active_game.white_player_id,
        black_player_id=active_game.black_player_id,
        moves=active_game.moves,
        result=f"winner: {winner}" if winner else "1/2-1/2",
        created_at=active_game.created_at
    )
    db.add(g)
    db.delete(active_game)
    await db.commit()
    await db.refresh(g)

def timecheck(game):
    if game.time_left_white <= 0:
        return 1  # Black wins
    elif game.time_left_black <= 0:
        return 0  # White wins
    return None  # No winner yet

async def time_update(game, db):
    if game.last_move_time is None:
        game.last_move_time = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(game)
        return
    now = datetime.now(timezone.utc)
    elapsed = (now - game.last_move_time).total_seconds()
    if game.board_state is None:
        return
    board = chess.Board(game.board_state)
    if board.turn:  
        game.time_left_black -= int(elapsed)
    else: 
        game.time_left_white -= int(elapsed)
    game.last_move_time = now  
    await db.commit()
    await db.refresh(game)
