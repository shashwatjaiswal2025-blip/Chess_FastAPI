const API_URL = localStorage.getItem('castleline_api') ||
    (window.location.protocol === 'http:' || window.location.protocol === 'https:' ? window.location.origin : 'http://127.0.0.1:8000');
const pieceMap = { r: '♜', n: '♞', b: '♝', q: '♛', k: '♚', p: '♟', R: '♖', N: '♘', B: '♗', Q: '♕', K: '♔', P: '♙' };
const initialFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

function showMessage(element, message, isError = true) { element.textContent = message; element.style.color = isError ? 'var(--copper)' : 'var(--lime)'; }
function setToken(token) { localStorage.setItem('castleline_token', token); }
function getToken() { return localStorage.getItem('castleline_token'); }

function setupAuth() {
    const form = document.getElementById('auth-form');
    if (!form) return;
    let mode = 'login';
    const username = document.getElementById('username');
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    const message = document.getElementById('auth-message');
    const submitLabel = document.getElementById('auth-submit-label');
    document.querySelectorAll('[data-auth-mode]').forEach(tab => tab.addEventListener('click', () => {
        mode = tab.dataset.authMode;
        document.querySelectorAll('[data-auth-mode]').forEach(item => {
            item.classList.toggle('is-active', item === tab);
            item.setAttribute('aria-selected', item === tab ? 'true' : 'false');
        });
        document.getElementById('email-label').classList.toggle('hidden', mode === 'login');
        email.classList.toggle('hidden', mode === 'login');
        email.required = mode === 'signup';
        submitLabel.textContent = mode === 'login' ? 'Sign in' : 'Create account';
        message.textContent = '';
    }));
    form.addEventListener('submit', async event => {
        event.preventDefault(); const button = form.querySelector('button[type="submit"]'); button.disabled = true; button.setAttribute('aria-busy', 'true');
        submitLabel.textContent = mode === 'login' ? 'Signing in…' : 'Creating account…';
        try {
            const isLogin = mode === 'login';
            const normalizedUsername = username.value.trim();
            if (!normalizedUsername) throw new Error('Username cannot be empty.');
            const body = isLogin ? new URLSearchParams({ username: normalizedUsername, password: password.value }) : JSON.stringify({ username: normalizedUsername, email: email.value, password: password.value });
            const response = await fetch(`${API_URL}/${isLogin ? 'login' : 'signup'}`, { method: 'POST', headers: { 'Content-Type': isLogin ? 'application/x-www-form-urlencoded' : 'application/json' }, body });
            const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || 'Unable to continue.');
            if (!isLogin) {
                showMessage(message, 'Account created. Sign in to play.', false);
                document.querySelector('[data-auth-mode="login"]').click();
            } else {
                if (!data.access_token) throw new Error('The server did not return a sign-in token.');
                setToken(data.access_token); localStorage.setItem('castleline_username', normalizedUsername); window.location.href = 'dashboard.html';
            }
        } catch (error) { showMessage(message, error instanceof Error ? error.message : 'The server is unavailable.'); } finally { button.disabled = false; button.removeAttribute('aria-busy'); submitLabel.textContent = mode === 'login' ? 'Sign in' : 'Create account'; }
    });
}

function squareName(index) { return String.fromCharCode(97 + (index % 8)) + (8 - Math.floor(index / 8)); }
function pieceAt(fen, square) {
    const [position] = fen.split(' ');
    const rows = position.split('/');
    const row = rows[8 - Number(square[1])];
    let file = 0;
    for (const character of row) {
        if (/\d/.test(character)) {
            file += Number(character);
        } else {
            if (file === square.charCodeAt(0) - 97) return character;
            file += 1;
        }
    }
    return null;
}

function findKingSquare(fen, color) {
    const position = fen.split(' ')[0].split('/');
    const king = color === 'w' ? 'K' : 'k';
    for (let rowIndex = 0; rowIndex < position.length; rowIndex += 1) {
        let fileIndex = 0;
        for (const character of position[rowIndex]) {
            if (/\d/.test(character)) {
                fileIndex += Number(character);
            } else {
                if (character === king) return String.fromCharCode(97 + fileIndex) + (8 - rowIndex);
                fileIndex += 1;
            }
        }
    }
    return null;
}

function renderBoard(fen, selected = null, legalMoves = [], orientation = 'white', lastMove = null, inCheck = false) {
    const board = document.getElementById('board'); if (!board) return;
    board.innerHTML = '';
    const checkedKing = inCheck ? findKingSquare(fen, fen.split(' ')[1]) : null;
    const position = fen.split(' ')[0].split('/');
    const rows = orientation === 'black' ? [...Array(8).keys()].reverse() : [...Array(8).keys()];
    const files = orientation === 'black' ? [...Array(8).keys()].reverse() : [...Array(8).keys()];
    const pieces = position.map(row => {
        const expanded = [];
        [...row].forEach(char => {
            const count = Number(char) || 1;
            for (let i = 0; i < count; i += 1) expanded.push(Number(char) ? null : char);
        });
        return expanded;
    });

    rows.forEach((rowIndex, displayRow) => files.forEach((fileIndex, displayFile) => {
        const name = String.fromCharCode(97 + fileIndex) + (8 - rowIndex);
        const pieceValue = pieces[rowIndex][fileIndex];
        const square = document.createElement('button');
        square.type = 'button';
        square.dataset.square = name;
        square.className = `square ${(rowIndex + fileIndex) % 2 ? 'dark' : 'light'}`;
        if (name === selected) square.classList.add('selected');
        if (lastMove && (name === lastMove.from || name === lastMove.to)) square.classList.add('last-move');
        if (name === checkedKing) square.classList.add('in-check');
        if (legalMoves.includes(name)) square.classList.add('legal');
        if (pieceValue) {
            const piece = document.createElement('span');
            piece.textContent = pieceMap[pieceValue];
            piece.className = pieceValue === pieceValue.toUpperCase() ? 'piece-white' : 'piece-black';
            square.append(piece);
        }
        if (displayFile === 0) {
            const rank = document.createElement('span');
            rank.textContent = 8 - rowIndex;
            rank.className = 'rank-label';
            square.append(rank);
        }
        if (displayRow === 7) {
            const file = document.createElement('span');
            file.textContent = String.fromCharCode(97 + fileIndex);
            file.className = 'file-label';
            square.append(file);
        }
        board.append(square);
    }));
}

function showPromotionPicker(board, targetSquare, piece, onChoose) {
    board.closest('.board-wrap').querySelector('.promotion-picker')?.remove();
    const target = board.querySelector(`[data-square="${targetSquare}"]`);
    if (!target) return;

    const picker = document.createElement('div');
    picker.className = 'promotion-picker';
    const choices = [
        ['q', 'Queen'],
        ['r', 'Rook'],
        ['b', 'Bishop'],
        ['n', 'Knight'],
    ];
    choices.forEach(([code, name]) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'promotion-choice';
        button.title = `Promote to ${name}`;
        button.setAttribute('aria-label', name);
        button.textContent = pieceMap[piece === piece.toUpperCase() ? code.toUpperCase() : code];
        button.addEventListener('click', event => {
            event.stopPropagation();
            picker.remove();
            onChoose(code);
        });
        picker.append(button);
    });

    const boardWrap = board.closest('.board-wrap');
    picker.style.left = `${target.offsetLeft + target.offsetWidth / 2}px`;
    picker.style.top = `${target.offsetTop + target.offsetHeight / 2}px`;
    boardWrap.append(picker);
}

function setupGame() {
    if (!document.getElementById('board')) return;
    const token = getToken(); if (!token) { window.location.href = 'login.html'; return; }
    const shouldStart = new URLSearchParams(window.location.search).get('start') === '1';
    const state = { fen: initialFen, selected: null, socket: null, moves: [], lastMove: null, inCheck: false, orientation: 'white', matched: false, gameOver: false };
    const status = document.getElementById('game-status'); const turnStatus = document.getElementById('turn-status'); const toast = document.getElementById('toast');
    const exitButton = document.getElementById('exit-game');
    const opponentName = document.querySelector('.opponent-name');
    const gameOverOverlay = document.getElementById('game-over-overlay');
    const gameOverTitle = document.getElementById('game-over-title');
    const gameOverDetail = document.getElementById('game-over-detail');
    const showGameOver = (title, detail) => {
        gameOverTitle.textContent = title;
        gameOverDetail.textContent = detail;
        gameOverOverlay.classList.add('show');
    };
    const hideGameOver = () => gameOverOverlay.classList.remove('show');
    const updateTurnStatus = () => {
        if (!shouldStart) {
            turnStatus.textContent = 'Start a game to play';
            turnStatus.className = 'turn-status';
            return;
        }
        if (state.gameOver) {
            turnStatus.textContent = 'Game over';
            turnStatus.className = 'turn-status';
            return;
        }
        if (!state.matched) {
            turnStatus.textContent = 'Waiting for opponent';
            turnStatus.className = 'turn-status';
            return;
        }
        const activeColor = state.fen.split(' ')[1];
        const yourTurn = activeColor === state.orientation[0];
        turnStatus.textContent = yourTurn ? 'Your turn' : "Opponent's turn";
        turnStatus.className = `turn-status ${yourTurn ? 'your-turn' : 'opponent-turn'}`;
    };
    document.getElementById('user-name').textContent = localStorage.getItem('castleline_username') || 'Player';
    const showToast = text => { toast.textContent = text; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 2400); };
    const renderMoves = () => {
        const moves = document.getElementById('moves');
        moves.replaceChildren();
        if (!state.moves.length) {
            const row = document.createElement('div');
            row.className = 'move-row';
            row.innerHTML = '<span>—</span><span>Waiting</span>';
            moves.append(row);
            return;
        }
        state.moves.forEach((move, i) => {
            const row = document.createElement('div');
            row.className = 'move-row';
            const number = document.createElement('span');
            const notation = document.createElement('span');
            number.textContent = `${Math.floor(i / 2) + 1}${i % 2 ? '.' : ''}`;
            notation.textContent = `${move[0]}-${move[1]}`;
            row.append(number, notation);
            moves.append(row);
        });
    };
    const submitMove = (from, to, promotion = '') => {
        let move = from + to;
        move += promotion;
        state.socket?.send(JSON.stringify({ type: 'move', move }));
        state.selected = null; renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck);
    };
    const board = document.getElementById('board');
    board.addEventListener('click', event => {
        const square = event.target.closest('.square')?.dataset.square;
        if (!square) return;
        if (!state.selected) {
            state.selected = square;
            renderBoard(state.fen, square, [], state.orientation, state.lastMove, state.inCheck);
            return;
        }
        if (square === state.selected) {
            state.selected = null;
            renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck);
            return;
        }
        const piece = pieceAt(state.fen, state.selected);
        if (piece?.toLowerCase() === 'p' && (square[1] === '1' || square[1] === '8')) {
            showPromotionPicker(board, square, piece, promotion => submitMove(state.selected, square, promotion));
            return;
        }
        submitMove(state.selected, square);
    });
    document.getElementById('logout').addEventListener('click', () => { localStorage.removeItem('castleline_token'); localStorage.removeItem('castleline_username'); window.location.href = 'login.html'; });
    exitButton.addEventListener('click', () => {
        if (state.socket?.readyState === WebSocket.OPEN && !state.gameOver) {
            state.socket.send(JSON.stringify({ type: 'resign' }));
        }
        window.location.href = 'dashboard.html';
    });
    document.getElementById('new-game').addEventListener('click', () => {
        state.fen = initialFen;
        state.selected = null;
        state.moves = [];
        state.orientation = 'white';
        state.matched = false;
        opponentName.textContent = 'Searching...';
        state.lastMove = null;
        state.inCheck = false;
        state.gameOver = false;
        hideGameOver();
        document.querySelector('.promotion-picker')?.remove();
        renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck);
        renderMoves();
        updateTurnStatus();
        connect();
    });
    function connect() {
        if (state.socket) state.socket.close(); state.moves = []; renderMoves();
        const protocol = API_URL.startsWith('https') ? 'wss' : 'ws'; const host = API_URL.replace(/^https?:\/\//, '');
        state.socket = new WebSocket(`${protocol}://${host}/game/ws?token=${encodeURIComponent(token)}`); status.textContent = 'Connecting'; updateTurnStatus();
        state.socket.onopen = () => { status.textContent = 'Searching'; showToast('Finding a worthy opponent'); };
        state.socket.onmessage = event => {
            let data;
            try { data = JSON.parse(event.data); } catch { showToast('Received an invalid server response'); return; }
            if (data.type === 'waiting') status.textContent = 'Waiting';
            if (data.type === 'matched') { state.orientation = data.player_color === 'black' ? 'black' : 'white'; opponentName.textContent = data.opponent_username; state.matched = true; status.textContent = 'Live'; updateTurnStatus(); renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck); showToast('Match found'); }
            if (data.type === 'board_state') { state.fen = data.board_state; state.inCheck = false; if (data.move) { state.lastMove = { from: data.move.slice(0, 2), to: data.move.slice(2, 4) }; state.moves.push([data.move.slice(0, 2), data.move.slice(2, 4) + (data.move.length === 5 ? `=${data.move[4].toUpperCase()}` : '')]); renderMoves(); } updateTurnStatus(); renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck); }
            if (data.type === 'check') { state.inCheck = true; renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck); showToast('Check'); }
            if (data.type === 'checkmate') { state.inCheck = true; state.gameOver = true; status.textContent = 'Game over'; updateTurnStatus(); renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck); const winnerColor = state.fen.split(' ')[1] === 'w' ? 'Black' : 'White'; showGameOver('Checkmate', winnerColor === (state.orientation === 'white' ? 'White' : 'Black') ? 'You won' : 'Opponent won'); }
            if (data.type === 'game_over') { state.gameOver = true; status.textContent = 'Game over'; updateTurnStatus(); showGameOver('Game over', 'Draw'); }
            if (data.type === 'resigned') { state.gameOver = true; status.textContent = 'Game over'; updateTurnStatus(); showGameOver('Game over', data.winner_color === state.orientation ? 'You won' : 'You resigned'); }
            if (data.type === 'error') {
                if (data.message === 'This account already has an active login.') {
                    window.location.href = 'dashboard.html';
                    return;
                }
                showToast(data.message);
            }
        };
        state.socket.onerror = () => { status.textContent = 'Offline preview'; showToast('Could not reach the game server'); };
        state.socket.onclose = () => { if (status.textContent !== 'Game over') status.textContent = 'Disconnected'; };
    }
    renderBoard(state.fen, null, [], state.orientation, state.lastMove, state.inCheck); renderMoves(); updateTurnStatus();
    if (shouldStart) connect();
}

async function setupDashboard() {
    const history = document.getElementById('game-history');
    if (!history) return;

    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const username = localStorage.getItem('castleline_username') || 'Player';
    document.querySelectorAll('[data-user-name]').forEach(element => { element.textContent = username; });
    document.getElementById('start-game').addEventListener('click', () => { window.location.href = 'game.html?start=1'; });
    document.getElementById('dashboard-logout').addEventListener('click', () => {
        localStorage.removeItem('castleline_token');
        localStorage.removeItem('castleline_username');
        window.location.href = 'login.html';
    });

    try {
        const response = await fetch(`${API_URL}/games/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || 'Game history is not available yet.');
        const games = Array.isArray(data) ? data : data.games;
        if (!Array.isArray(games)) throw new Error('The game history response has an invalid format.');
        history.replaceChildren();
        if (!games.length) {
            history.innerHTML = '<div class="empty-state"><span class="empty-icon">♞</span><p>No games yet</p><span>Start your first game to see it here.</span></div>';
            return;
        }
        games.forEach(game => {
            const row = document.createElement('article');
            row.className = 'history-row';
            const opponent = game.opponent || 'Unknown opponent';
            const result = game.result || 'Ongoing';
            const date = game.created_at ? new Date(game.created_at).toLocaleDateString() : 'Date unavailable';
            const details = document.createElement('div');
            const opponentElement = document.createElement('strong');
            const dateElement = document.createElement('span');
            const resultElement = document.createElement('b');
            opponentElement.textContent = `vs. ${opponent}`;
            dateElement.textContent = date;
            resultElement.textContent = result;
            resultElement.className = result === 'Win' ? 'result-win' : result === 'Loss' ? 'result-loss' : '';
            details.append(opponentElement, dateElement);
            row.append(details, resultElement);
            history.append(row);
        });
    } catch (error) {
        history.innerHTML = `<div class="empty-state"><span class="empty-icon">!</span><p>History unavailable</p><span>${error instanceof Error ? error.message : 'Unable to load game history.'}</span></div>`;
    }
}

setupAuth(); setupGame(); setupDashboard();
