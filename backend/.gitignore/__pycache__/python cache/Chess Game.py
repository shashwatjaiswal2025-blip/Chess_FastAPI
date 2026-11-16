import sys,pygame,pygame_gui
pygame.init()
manager=pygame_gui.UIManager((500,500))
gui=pygame.display.set_mode((500,500))
pygame.display.set_caption('Chess Engine v0.69')
clock=pygame.time.Clock()


#setting up the board i.e.,board[row][col]
board=[[None]*8,[None]*8,[None]*8,[None]*8,[None]*8,[None]*8,[None]*8,[None]*8]

#All the user menus and buttons
promote_menu=pygame_gui.elements.UISelectionList(relative_rect=pygame.Rect((5,405),(100,86)),
                                                 item_list=['Queen (Q)','Rook (R)','Knight (N)','Bishop (B)'],
                                                 default_selection='Queen (Q)',
                                                 manager=manager)

time=10
wTime=bTime=time*3600
current_player=0 #1 -> white and -1 -> black

bTimer=pygame_gui.elements.UIButton(relative_rect=pygame.Rect((400,0),(100,50)),
                                        text='00:00:00',
                                        manager=manager)
wTimer=pygame_gui.elements.UIButton(relative_rect=pygame.Rect((400,350),(100,50)),
                                        text='00:00:00',
                                        manager=manager)
SetTime=pygame_gui.elements.UISelectionList(relative_rect=pygame.Rect((205,417),(100,66)),
                                            item_list=['1 min','5 min','10 min'],
                                            default_selection='10 min',
                                            manager=manager)


def timer():
    global wTime,bTime
    if current_player==1:
        wTime-=1
        wMin,wSec=divmod(wTime,3600)
        wSec,wmSec=divmod(wSec,60)
        wTimer.set_text(f'{wMin:02d}:{wSec:02d}:{wmSec:02d}')
    elif current_player==-1:
        bTime-=1
        bMin,bSec=divmod(bTime,3600)
        bSec,bmSec=divmod(bSec,60)
        bTimer.set_text(f'{bMin:02d}:{bSec:02d}:{bmSec:02d}')
    pygame.display.update() 
    if wTime==-1 or bTime==-1:
        wTimer.kill()
        bTimer.kill()


#retrieving images
chessboard=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\chessboard.png")
wR=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wR.png")
wN=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wN.png")
wB=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wB.png")
wQ=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wQ.png")
wK=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wK.png")
wp=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\wp.png")
bR=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bR.png")
bN=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bN.png")
bB=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bB.png")
bQ=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bQ.png")
bK=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bK.png")
bK2=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bK.png")
bp=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\bp.png")
highlighter=pygame.image.load(r"C:\Users\Dell\Desktop\Python\python cache\highlighter.png")

gui.blit(chessboard,(0,0))
pygame.display.update()

wL=[wR,wN,wB,wQ,wK,wp]
bL=[bR,bN,bB,bQ,bK,bp]
promote='Queen (Q)'

#Initial position of the board
board[0]=[bR,bN,bB,bQ,bK,bB,bN,bR]
board[1]=[bp,bp,bp,bp,bp,bp,bp,bp]
board[6]=[wp,wp,wp,wp,wp,wp,wp,wp]
board[7]=[wR,wN,wB,wQ,wK,wB,wN,wR]

wK_pos=[7,4]
bK_pos=[0,4]
    
def set_board():
    #set board to the needed position
    gui.blit(chessboard,(0,0)) 
    for row in range(8):
        for col in range(8):
            piece=board[row][col]
            if piece is not None:
                x=col*50+5
                y=row*50+3
                gui.blit(piece,(x,y))
    pygame.display.update()


a=0
def click():
    global piece,a
    if event.type==pygame.MOUSEBUTTONDOWN:
        x,y=pygame.mouse.get_pos()
        if 0<=x<=400 and 0<=y<=400:
            row=y//50
            col=x//50
            piece=board[row][col]
            if a==0:
                if piece is not None:
                    highlight(possible_moves(piece,row,col))
            else:
                if (row,col) in legal_list:
                    move(a,row,col)
                    set_board()
                a=0

def possible_moves(piece,row,col):
    global a
    a=[piece,row,col]
    global legal_list
    legal_list=[]
    tem_list=[]
    if current_player==1:
        tem_list=list(wL)
    elif current_player==-1:
        tem_list=list(bL)
    if piece==wp and piece in tem_list:
        if row==6:
            if board[row-2][col] is None and board[row-1][col] is None:
                legalappend(row-2,col)            
        if board[row-1][col] is None:
            legalappend(row-1,col)
        if board[row-1][col-1] is not None:
            legalappend(row-1,col-1)
        if col+1!=8 and board[row-1][col+1] is not None:
            legalappend(row-1,col+1)

    if piece==bp and piece in tem_list:
        if row==1:
            if board[row+2][col] is None and board[row+1][col] is None:
                legalappend(row+1,col)
                legalappend(row+2,col)            
        if board[row+1][col] is None:
            legalappend(row+1,col)
        if col+1!=8 and board[row+1][col+1] is not None:
            legalappend(row+1,col+1)
        if board[row+1][col-1] is not None:
            legalappend(row+1,col-1)

    if (piece==wK or piece==bK) and piece in tem_list:
        legal_list=illegal_moves(piece)

    if (piece==bR or piece==wR) and piece in tem_list:
        rook_moves=[(0,1),(0,-1),(1,0),(-1,0)]
        for dr,dc in rook_moves:
            nr,nc=row+dr,col+dc
            while 0<=nr<=7 and 0<=nc<=7:
                legalappend(nr,nc)
                if board[nr][nc] is not None:
                    break
                nr,nc=nr+dr,nc+dc

    if (piece==bB or piece==wB) and piece in tem_list:
        bishop_moves=[(1,1),(1,-1),(-1,-1),(-1,1)]
        for dr,dc in bishop_moves:
            nr,nc=row+dr,col+dc
            while 0<=nr<=7 and 0<=nc<=7:
                legalappend(nr,nc)
                if board[nr][nc] is not None:
                    break
                nr,nc=nr+dr,nc+dc

    if (piece==wQ or piece==bQ) and piece in tem_list:
        queen_moves=[(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,-1),(-1,1)]
        for dr,dc in queen_moves:
            nr,nc=row+dr,col+dc
            while 0<=nr<=7 and 0<=nc<=7:
                legalappend(nr,nc)
                if board[nr][nc] is not None:
                    break
                nr,nc=nr+dr,nc+dc

    
    if (piece==bN or piece==wN) and piece in tem_list:
        knight_moves=[(1,2),(-1,2),(-1,-2),(1,-2),(2,1),(-2,1),(-2,-1),(2,-1)]
        for dr,dc in knight_moves:
            nr,nc=row+dr,col+dc
            if 0<=nr<=7 and 0<=nc<=7:
                legalappend(nr,nc)
    if piece=='L':
        king_moves=[(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,-1),(-1,1)]
        for dr,dc in king_moves:
            nr,nc=row+dr,col+dc
            if 0<=nr<=7 and 0<=nc<=7:
                legalappend(nr,nc)
        piece='L'
    
    return legal_list

    


def legalappend(r,c):
    global piece,bL,wL,f
    if piece in wL and board[r][c] not in wL:
        legal_list.append((r,c))
        f='w'
    elif piece in bL and board[r][c] not in bL:
        legal_list.append((r,c))
        f='b'
    


def highlight(legal_list):
    set_board()    
    #to light up legal moves
    for (hr,hc) in legal_list:
        gui.blit(highlighter,(hc*50,hr*50))
    pygame.display.update()



def illegal_moves(piece):
    global wK_pos

#when white moves
#    if bK's moves in legal_list of white
#        that move is removed from bK's legal_list(illegal move)
#    if bK is itself in legal_list of all white
#        (check
#    if wK is in legal_list of all black
#    white's above move is cancelled (absolute pin)"""
    
    w_c_list=[]
    b_c_list=[]
    for row in range(8):
        for col in range(8):
            p=board[row][col]
            if p==wK:
                wK_pos=(row,col)
            if p in [wR,wN,wB,wQ,wp]:
                w_c_list+=possible_moves(p,row,col)
            if p in [bR,bN,bB,bQ,bp]:
                b_c_list+=possible_moves(p,row,col)
    w_k_list=possible_moves('L',wK_pos[0],wK_pos[1])
    
    legal_list=list(set(w_k_list) - set(b_c_list))
    print (w_k_list)
    return legal_list


def move(piece,r,c):
    global current_player
    if a[0]=='L':
        a[0]==wK
    board[r][c]=a[0]
    
        
    if (a[0]==wp and r==0) or (a[0]==bp and r==7):
        print('Promoted to',promote)
        board[r][c]=eval(f+promote[-2])
    board[a[1]][a[2]]=None
    pygame.display.update()

    if a[0]==bK:
        bk_pos=[r,c]
    current_player*=-1

def set_time():
    global time,wTime,bTime
    time=int(SetTime.get_single_selection()[0:2])
    wTime=bTime=time*3600

set_board()
while True:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type==pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element==promote_menu:
                promote=promote_menu.get_single_selection()
            if event.ui_element==SetTime:
                set_time()
        if event.type==pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element==wTimer:                
                current_player=1
                SetTime.disable()
            
        click()
        manager.process_events(event)
    timer()
    manager.update(clock.tick(60)/1000.0)
    manager.draw_ui(gui)
    pygame.display.update()

