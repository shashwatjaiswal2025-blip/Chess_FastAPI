const API_URL = localStorage.getItem('castleline_api') || 'http://127.0.0.1:8000';
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
            const body = isLogin ? new URLSearchParams({ username: username.value, password: password.value }) : JSON.stringify({ username: username.value, email: email.value, password: password.value });
            const response = await fetch(`${API_URL}/${isLogin ? 'login' : 'signup'}`, { method: 'POST', headers: { 'Content-Type': isLogin ? 'application/x-www-form-urlencoded' : 'application/json' }, body });
            const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || 'Unable to continue.');
            if (!isLogin) {
                showMessage(message, 'Account created. Sign in to play.', false);
                document.querySelector('[data-auth-mode="login"]').click();
            } else {
                if (!data.access_token) throw new Error('The server did not return a sign-in token.');
                setToken(data.access_token); localStorage.setItem('castleline_username', username.value); window.location.href = 'game.html';
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

function renderBoard(fen, selected = null, legalMoves = [], orientation = 'white') {
    const board = document.getElementById('board'); if (!board) return;
    board.innerHTML = '';
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
    const token = getToken(); if (!token) { window.location.href = 'home.html'; return; }
    const state = { fen: initialFen, selected: null, socket: null, moves: [], orientation: 'white' };
    const status = document.getElementById('game-status'); const matchStatus = document.getElementById('match-status'); const toast = document.getElementById('toast');
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
        state.selected = null; renderBoard(state.fen, null, [], state.orientation);
    };
    const board = document.getElementById('board');
    board.addEventListener('click', event => {
        const square = event.target.closest('.square')?.dataset.square;
        if (!square) return;
        if (!state.selected) {
            state.selected = square;
            renderBoard(state.fen, square, [], state.orientation);
            return;
        }
        if (square === state.selected) {
            state.selected = null;
            renderBoard(state.fen, null, [], state.orientation);
            return;
        }
        const piece = pieceAt(state.fen, state.selected);
        if (piece?.toLowerCase() === 'p' && (square[1] === '1' || square[1] === '8')) {
            showPromotionPicker(board, square, piece, promotion => submitMove(state.selected, square, promotion));
            return;
        }
        submitMove(state.selected, square);
    });
    document.getElementById('logout').addEventListener('click', () => { localStorage.removeItem('castleline_token'); window.location.href = 'home.html'; });
    document.getElementById('new-game').addEventListener('click', () => connect());
    function connect() {
        if (state.socket) state.socket.close(); state.moves = []; renderMoves();
        const protocol = API_URL.startsWith('https') ? 'wss' : 'ws'; const host = API_URL.replace(/^https?:\/\//, '');
        state.socket = new WebSocket(`${protocol}://${host}/game/ws?token=${encodeURIComponent(token)}`); status.textContent = 'Connecting'; matchStatus.textContent = 'Looking for an opponent...';
        state.socket.onopen = () => { status.textContent = 'Searching'; showToast('Finding a worthy opponent'); };
        state.socket.onmessage = event => {
            let data;
            try { data = JSON.parse(event.data); } catch { showToast('Received an invalid server response'); return; }
            if (data.type === 'waiting') { status.textContent = 'Waiting'; matchStatus.textContent = data.message; }
            if (data.type === 'matched') { state.orientation = data.player_color === 'black' ? 'black' : 'white'; status.textContent = 'Live'; matchStatus.textContent = 'Opponent found. Your move.'; renderBoard(state.fen, null, [], state.orientation); showToast('Match found'); }
            if (data.type === 'board_state') { state.fen = data.board_state; if (data.move) { state.moves.push([data.move.slice(0, 2), data.move.slice(2, 4) + (data.move.length === 5 ? `=${data.move[4].toUpperCase()}` : '')]); renderMoves(); } renderBoard(state.fen, null, [], state.orientation); }
            if (data.type === 'check') { matchStatus.textContent = 'Check. Find your escape.'; showToast('Check'); }
            if (data.type === 'checkmate') { matchStatus.textContent = 'Game over by checkmate.'; status.textContent = 'Game over'; }
            if (data.type === 'error') showToast(data.message);
        };
        state.socket.onerror = () => { status.textContent = 'Offline preview'; matchStatus.textContent = 'API unavailable. Board is ready for preview.'; showToast('Could not reach the game server'); };
        state.socket.onclose = () => { if (status.textContent !== 'Game over') { status.textContent = 'Disconnected'; matchStatus.textContent = 'Connection closed. Find a new game to reconnect.'; } };
    }
    renderBoard(state.fen, null, [], state.orientation); renderMoves(); connect();
}

setupAuth(); setupGame();
