from __future__ import annotations

import asyncio
import urllib.error
import urllib.request

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

BACKEND_BASE_URL = "http://127.0.0.1:8000"
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 8501

app = FastAPI(title="Chess Frontend")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Chess Arena</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Source+Sans+3:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111e;
      --panel: rgba(10, 18, 31, 0.84);
      --line: rgba(255, 255, 255, 0.08);
      --text: #eef3fb;
      --muted: #9eadc2;
      --accent: #7dd3fc;
      --accent-2: #f5c86f;
      --success: #79d9a0;
      --danger: #ff7c8a;
      --light: #f2d8b5;
      --dark: #9d6947;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      min-height: 100%;
      color: var(--text);
      font-family: "Source Sans 3", system-ui, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(125, 211, 252, 0.15), transparent 26%),
        radial-gradient(circle at top right, rgba(245, 200, 111, 0.12), transparent 24%),
        linear-gradient(180deg, #050b13 0%, #0a1323 55%, #05070d 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
      background-size: 72px 72px;
      opacity: 0.22;
    }

    .app {
      max-width: 1500px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      gap: 20px;
    }

    .hero, .panel, .board-card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
      gap: 20px;
      padding: 26px;
    }

    .hero h1 {
      margin: 0;
      font-family: Cinzel, serif;
      font-size: clamp(2.2rem, 4vw, 4.2rem);
      line-height: 0.96;
      letter-spacing: 0.03em;
    }

    .subtitle {
      max-width: 70ch;
      margin-top: 16px;
      color: var(--muted);
      line-height: 1.65;
      font-size: 1rem;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(125, 211, 252, 0.2);
      background: rgba(125, 211, 252, 0.08);
      color: var(--accent);
      font-size: 0.88rem;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 16px rgba(121, 217, 160, 0.7);
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }

    .chip {
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.04);
      color: var(--text);
      font-weight: 600;
      font-size: 0.9rem;
    }

    .chip strong { color: var(--accent-2); }

    .status-box {
      padding: 22px;
      display: grid;
      gap: 14px;
      align-content: center;
    }

    .meta-grid {
      display: grid;
      gap: 10px;
    }

    .meta-item {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,0.06);
      background: rgba(255,255,255,0.03);
      color: var(--muted);
      font-size: 0.92rem;
    }

    .meta-item strong {
      color: var(--text);
      text-align: right;
      word-break: break-word;
    }

    .layout {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr) 320px;
      gap: 20px;
      align-items: start;
    }

    .panel, .board-card {
      padding: 20px;
    }

    h2 {
      margin: 0 0 14px;
      font-size: 1.05rem;
      letter-spacing: -0.02em;
    }

    .tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }

    .tab {
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.03);
      color: var(--muted);
      padding: 10px 14px;
      border-radius: 999px;
      cursor: pointer;
    }

    .tab.active {
      color: var(--text);
      border-color: rgba(125, 211, 252, 0.22);
      background: rgba(125, 211, 252, 0.12);
    }

    .stack { display: grid; gap: 14px; }
    .field { display: grid; gap: 8px; }
    label { color: var(--muted); font-size: 0.84rem; }
    input, button, textarea { font: inherit; }

    input, textarea {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.04);
      color: var(--text);
      padding: 12px 14px;
      outline: none;
    }

    input:focus, textarea:focus {
      border-color: rgba(125, 211, 252, 0.4);
      box-shadow: 0 0 0 4px rgba(125, 211, 252, 0.08);
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    button.primary, button.secondary, button.ghost {
      border: none;
      border-radius: 14px;
      cursor: pointer;
      padding: 12px 14px;
      transition: transform 150ms ease, filter 150ms ease;
    }

    button.primary {
      background: linear-gradient(135deg, var(--accent), #6ca9ff);
      color: #08111d;
      font-weight: 800;
    }

    button.secondary {
      background: rgba(245, 200, 111, 0.14);
      border: 1px solid rgba(245, 200, 111, 0.22);
      color: var(--text);
    }

    button.ghost {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.08);
      color: var(--text);
    }

    button:hover {
      transform: translateY(-1px);
      filter: brightness(1.04);
    }

    .message {
      min-height: 20px;
      color: var(--muted);
      font-size: 0.93rem;
    }

    .message.ok { color: var(--success); }
    .message.err { color: var(--danger); }

    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .board-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.03);
      color: var(--muted);
      font-size: 0.85rem;
    }

    .board {
      display: grid;
      grid-template-columns: repeat(8, minmax(0, 1fr));
      aspect-ratio: 1;
      width: min(100%, 780px);
      margin: 0 auto;
      overflow: hidden;
      border-radius: 24px;
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 20px 60px rgba(0,0,0,0.4);
      user-select: none;
    }

    .square {
      position: relative;
      display: grid;
      place-items: center;
      font-size: clamp(1.8rem, 3vw, 3.2rem);
      cursor: pointer;
      transition: transform 150ms ease, filter 150ms ease;
    }

    .square:hover {
      transform: scale(1.01);
      filter: brightness(1.05);
    }

    .square.light { background: var(--light); }
    .square.dark { background: var(--dark); }
    .square.selected { outline: 4px solid rgba(125, 211, 252, 0.75); outline-offset: -4px; }
    .square.target::after {
      content: "";
      position: absolute;
      width: 26%;
      height: 26%;
      border-radius: 50%;
      background: rgba(121, 217, 160, 0.52);
      box-shadow: 0 0 0 8px rgba(121, 217, 160, 0.08);
    }

    .square .coord {
      position: absolute;
      left: 8px;
      bottom: 6px;
      font-size: 0.68rem;
      font-weight: 700;
      color: rgba(8, 17, 31, 0.6);
      mix-blend-mode: multiply;
      pointer-events: none;
    }

    .square.dark .coord {
      color: rgba(255,255,255,0.45);
      mix-blend-mode: screen;
    }

    .side {
      display: grid;
      gap: 20px;
    }

    .log {
      display: grid;
      gap: 10px;
      max-height: 330px;
      overflow: auto;
      padding-right: 6px;
    }

    .log-item {
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      color: var(--muted);
      font-size: 0.9rem;
    }

    .log-item strong {
      color: var(--text);
      display: block;
      margin-bottom: 4px;
    }

    .footer-note {
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.5;
      padding: 0 6px 16px;
    }

    .hidden { display: none !important; }

    @media (max-width: 1200px) {
      .hero, .layout {
        grid-template-columns: 1fr;
      }

      .side {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 780px) {
      .app { padding: 14px; }
      .hero, .layout, .panel, .board-card, .status-box { border-radius: 20px; }
      .side, .mini-grid { grid-template-columns: 1fr; }
      .board { width: 100%; border-radius: 18px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <section class="hero">
      <div class="card status-box">
        <div class="badge"><span class="dot"></span><span>FastAPI chess interface</span></div>
        <h1>Chess Arena</h1>
        <p class="subtitle">
          A standalone front end for your chess API: login, signup, game creation, live board rendering,
          legal move previews, and move submission from a single file.
        </p>
        <div class="chips">
          <div class="chip"><strong>Auth</strong> login and signup</div>
          <div class="chip"><strong>Lobby</strong> queue or pair</div>
          <div class="chip"><strong>Board</strong> click-to-move</div>
          <div class="chip"><strong>Live</strong> polling updates</div>
        </div>
      </div>
      <div class="card status-box">
        <div class="badge"><span class="dot"></span><span id="connectionState">Ready</span></div>
        <div class="meta-grid">
          <div class="meta-item"><span>API base</span><strong id="apiBaseValue">http://127.0.0.1:8000</strong></div>
          <div class="meta-item"><span>User</span><strong id="userValue">Guest</strong></div>
          <div class="meta-item"><span>Active game</span><strong id="gameValue">None</strong></div>
        </div>
      </div>
    </section>

    <main class="layout">
      <section class="panel">
        <div class="tabs">
          <button class="tab active" data-target="loginPanel">Login</button>
          <button class="tab" data-target="signupPanel">Signup</button>
          <button class="tab" data-target="lobbyPanel">Lobby</button>
        </div>

        <div id="loginPanel" class="stack tab-panel">
          <h2>Login</h2>
          <div class="field">
            <label for="loginUsername">Username</label>
            <input id="loginUsername" autocomplete="username" placeholder="your_username" />
          </div>
          <div class="field">
            <label for="loginPassword">Password</label>
            <input id="loginPassword" type="password" autocomplete="current-password" placeholder="••••••••" />
          </div>
          <div class="button-row">
            <button class="primary" id="loginBtn">Sign in</button>
            <button class="ghost" id="logoutBtn">Logout</button>
          </div>
          <div class="message" id="loginMessage"></div>
        </div>

        <div id="signupPanel" class="stack tab-panel hidden">
          <h2>Create account</h2>
          <div class="field">
            <label for="signupUsername">Username</label>
            <input id="signupUsername" autocomplete="username" placeholder="new_player" />
          </div>
          <div class="field">
            <label for="signupEmail">Email</label>
            <input id="signupEmail" type="email" autocomplete="email" placeholder="name@example.com" />
          </div>
          <div class="field">
            <label for="signupPassword">Password</label>
            <input id="signupPassword" type="password" autocomplete="new-password" placeholder="Choose a password" />
          </div>
          <button class="secondary" id="signupBtn">Create account</button>
          <div class="message" id="signupMessage"></div>
        </div>

        <div id="lobbyPanel" class="stack tab-panel hidden">
          <h2>Lobby</h2>
          <div class="button-row">
            <button class="primary" id="createGameBtn">Create / Join game</button>
            <button class="ghost" id="refreshStatusBtn">Refresh status</button>
          </div>
          <div class="mini-grid">
            <div class="meta-item"><span>Match state</span><strong id="matchState">-</strong></div>
            <div class="meta-item"><span>Perspective</span><strong id="sideState">-</strong></div>
          </div>
          <div class="message" id="lobbyMessage"></div>
        </div>
      </section>

      <section class="board-card">
        <div class="board-head">
          <div>
            <h2 style="margin-bottom:8px;">Board</h2>
            <div class="pill" id="boardInfo">Load a game to start</div>
          </div>
          <div class="button-row">
            <button class="ghost" id="reloadGameBtn">Reload game</button>
            <button class="ghost" id="flipBtn">Flip board</button>
          </div>
        </div>
        <div class="board" id="board"></div>
        <div class="message" id="boardMessage"></div>
      </section>

      <aside class="side">
        <section class="panel">
          <h2>Game details</h2>
          <div class="stack">
            <div class="meta-item"><span>Game ID</span><strong id="gameIdValue">-</strong></div>
            <div class="meta-item"><span>White</span><strong id="whitePlayerValue">-</strong></div>
            <div class="meta-item"><span>Black</span><strong id="blackPlayerValue">-</strong></div>
            <div class="meta-item"><span>Turn</span><strong id="turnValue">-</strong></div>
            <div class="meta-item"><span>White clock</span><strong id="whiteClockValue">-</strong></div>
            <div class="meta-item"><span>Black clock</span><strong id="blackClockValue">-</strong></div>
            <div class="meta-item"><span>Selected</span><strong id="selectedValue">None</strong></div>
            <div class="meta-item"><span>Targets</span><strong id="targetCountValue">0</strong></div>
          </div>
        </section>

        <section class="panel">
          <h2>Move log</h2>
          <div class="log" id="moveLog"></div>
        </section>

        <section class="panel">
          <h2>Move box</h2>
          <div class="stack">
            <div class="field">
              <label for="manualMove">Manual UCI move</label>
              <input id="manualMove" placeholder="e2e4" />
            </div>
            <button class="secondary" id="submitManualMoveBtn">Submit move</button>
          </div>
        </section>
      </aside>
    </main>

    <div class="footer-note">
      This file runs a small local proxy so the browser can talk to your existing FastAPI routes without touching your current code.
      If your backend is already configured for CORS, you can also reuse the page structure and point it straight at the API.
    </div>
  </div>

  <script>
    const API_BASE = "http://127.0.0.1:8000";
    const TOKEN_KEY = "chess_token";
    const USER_KEY = "chess_user";
    const ORIENTATION_KEY = "chess_orientation";

    let token = localStorage.getItem(TOKEN_KEY) || "";
    let user = JSON.parse(localStorage.getItem(USER_KEY) || "null");
    let currentGame = null;
    let selectedSquare = null;
    let legalTargets = [];
    let orientation = localStorage.getItem(ORIENTATION_KEY) || "white";
    let pollTimer = null;

    const pieceMap = {
      P: "♙", R: "♖", N: "♘", B: "♗", Q: "♕", K: "♔",
      p: "♟", r: "♜", n: "♞", b: "♝", q: "♛", k: "♚",
    };

    const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
    const $ = (id) => document.getElementById(id);

    function decodeJwt(jwt) {
      try {
        const payload = jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const json = JSON.parse(atob(payload + "=".repeat((4 - payload.length % 4) % 4)));
        return { id: json.user_id, username: json.username };
      } catch {
        return null;
      }
    }

    function setMessage(id, text, kind = "") {
      const el = $(id);
      el.textContent = text || "";
      el.className = kind ? `message ${kind}` : "message";
    }

    function formatClock(seconds) {
      if (seconds === null || seconds === undefined) return "-";
      const value = Math.max(0, Number(seconds));
      const minutes = String(Math.floor(value / 60)).padStart(2, "0");
      const secs = String(value % 60).padStart(2, "0");
      return `${minutes}:${secs}`;
    }

    function boardToMatrix(fen) {
      const placement = fen.split(" ")[0];
      return placement.split("/").map((row) => {
        const cells = [];
        for (const ch of row) {
          if (/\\d/.test(ch)) {
            for (let i = 0; i < Number(ch); i += 1) cells.push(null);
          } else {
            cells.push(ch);
          }
        }
        return cells;
      });
    }

    function squareName(row, col) {
      return `${files[col]}${8 - row}`;
    }

    function squareCoords(square) {
      return { row: 8 - Number(square[1]), col: files.indexOf(square[0]) };
    }

    function currentSide() {
      if (!currentGame || !user) return "";
      if (Number(currentGame.white_player_id) === Number(user.id)) return "white";
      if (Number(currentGame.black_player_id) === Number(user.id)) return "black";
      return "spectator";
    }

    function actualBoardMatrix() {
      return currentGame?.board_state ? boardToMatrix(currentGame.board_state) : [];
    }

    function displayToActual(displayRow, displayCol) {
      const row = orientation === "black" ? 7 - displayRow : displayRow;
      const col = orientation === "black" ? 7 - displayCol : displayCol;
      return { row, col, square: squareName(row, col) };
    }

    function updateHeader() {
      $("apiBaseValue").textContent = API_BASE;
      $("userValue").textContent = user?.username || "Guest";
      $("gameValue").textContent = currentGame?.id ?? "None";
      $("sideState").textContent = currentSide() || "-";
      $("selectedValue").textContent = selectedSquare || "None";
      $("targetCountValue").textContent = String(legalTargets.length);
      $("connectionState").textContent = token ? "Session loaded" : "Ready";
    }

    async function api(path, options = {}) {
      const headers = new Headers(options.headers || {});
      if (token) headers.set("Authorization", `Bearer ${token}`);
      const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
      const text = await response.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch { data = text; }
      if (!response.ok) throw new Error(data?.detail || data?.message || text || response.statusText);
      return data;
    }

    function renderHistory() {
      const log = $("moveLog");
      const moves = (currentGame?.moves || "").trim().split(/\\s+/).filter(Boolean);
      if (!moves.length) {
        log.innerHTML = `<div class="log-item"><strong>No moves yet</strong>Waiting for the first move.</div>`;
        return;
      }
      log.innerHTML = moves.slice().reverse().map((move, index) => {
        return `<div class="log-item"><strong>Move ${moves.length - index}</strong>${move}</div>`;
      }).join("");
    }

    function renderBoard() {
      const board = $("board");
      board.innerHTML = "";
      if (!currentGame?.board_state) {
        board.innerHTML = `<div style="grid-column:1/-1;display:grid;place-items:center;min-height:320px;color:var(--muted);">Load a game to show the board.</div>`;
        return;
      }

      const matrix = actualBoardMatrix();
      for (let displayRow = 0; displayRow < 8; displayRow += 1) {
        for (let displayCol = 0; displayCol < 8; displayCol += 1) {
          const mapped = displayToActual(displayRow, displayCol);
          const piece = matrix[mapped.row]?.[mapped.col];
          const square = document.createElement("button");
          square.type = "button";
          square.className = `square ${(displayRow + displayCol) % 2 === 0 ? "dark" : "light"}`;
          square.dataset.square = mapped.square;

          if (selectedSquare === mapped.square) square.classList.add("selected");
          if (legalTargets.includes(mapped.square)) square.classList.add("target");

          square.textContent = piece ? pieceMap[piece] : "";

          const coord = document.createElement("span");
          coord.className = "coord";
          const showLabel = orientation === "white" ? displayRow === 7 : displayRow === 0;
          coord.textContent = showLabel ? mapped.square : "";
          square.appendChild(coord);

          square.addEventListener("click", () => handleSquareClick(mapped.square));
          board.appendChild(square);
        }
      }

      $("gameIdValue").textContent = currentGame?.id ?? "-";
      $("whitePlayerValue").textContent = currentGame?.white_player_id ?? "-";
      $("blackPlayerValue").textContent = currentGame?.black_player_id ?? "-";
      $("turnValue").textContent = currentGame ? (currentGame.board_state.split(" ")[1] === "w" ? "White" : "Black") : "-";
      $("whiteClockValue").textContent = formatClock(currentGame?.time_left_white);
      $("blackClockValue").textContent = formatClock(currentGame?.time_left_black);
      updateHeader();
      renderHistory();
    }

    async function loadGame(gameId) {
      currentGame = await api(`/game/${gameId}`);
      orientation = currentSide() === "black" ? "black" : "white";
      localStorage.setItem(ORIENTATION_KEY, orientation);
      selectedSquare = null;
      legalTargets = [];
      $("boardInfo").textContent = `Game ${currentGame.id} loaded`;
      renderBoard();
      startPolling();
      setMessage("boardMessage", `Loaded game ${currentGame.id}.`, "ok");
    }

    async function refreshStatus() {
      if (!token) {
        currentGame = null;
        selectedSquare = null;
        legalTargets = [];
        updateHeader();
        renderBoard();
        setMessage("lobbyMessage", "Sign in to create or join a game.");
        return;
      }

      const status = await api("/game/status");
      $("matchState").textContent = status.status;
      if (status.status === "active") {
        await loadGame(status.game_id);
      } else {
        currentGame = null;
        selectedSquare = null;
        legalTargets = [];
        $("boardInfo").textContent = `Lobby: ${status.status}`;
        renderBoard();
      }
      $("sideState").textContent = currentSide() || status.status;
      setMessage("lobbyMessage", `Current status: ${status.status}`, "ok");
      updateHeader();
    }

    async function createGame() {
      if (!token) throw new Error("Please sign in first.");
      setMessage("lobbyMessage", "Requesting a game...");
      const result = await api("/game/new");
      if (result?.id) {
        await loadGame(result.id);
        setMessage("lobbyMessage", `Matched into game ${result.id}.`, "ok");
      } else {
        setMessage("lobbyMessage", result?.message || "Added to waiting list.", "ok");
        await refreshStatus();
      }
    }

    async function loadLegalMoves(square) {
      const { row, col } = squareCoords(square);
      const piece = actualBoardMatrix()?.[row]?.[col];
      if (!piece || !currentGame) return [];
      const response = await api(`/game/${currentGame.id}/legal_moves?game_id=${currentGame.id}&piece=${encodeURIComponent(piece)}&position=${encodeURIComponent(square)}`);
      const list = Array.isArray(response) ? response : (response?.legal_moves || []);
      return list.map((move) => {
        if (typeof move === "string") return move;
        if (move && typeof move.uci === "string") return move.uci;
        return String(move);
      }).filter(Boolean);
    }

    async function submitMove(move) {
      if (!currentGame) throw new Error("Load a game first.");
      if (!move) throw new Error("Enter a move.");
      const result = await api(`/game/${currentGame.id}/move?move=${encodeURIComponent(move)}`, { method: "POST" });
      setMessage("boardMessage", result.message || "Move accepted.", "ok");
      await loadGame(currentGame.id);
    }

    async function handleSquareClick(square) {
      if (!currentGame) return;
      const board = actualBoardMatrix();
      const { row, col } = squareCoords(square);
      const piece = board[row]?.[col];
      const side = currentSide();

      if (!selectedSquare) {
        if (!piece) return;
        const isWhitePiece = piece === piece.toUpperCase();
        if ((side === "white" && !isWhitePiece) || (side === "black" && isWhitePiece) || side === "spectator") {
          setMessage("boardMessage", "That piece does not belong to you.", "err");
          return;
        }

        selectedSquare = square;
        setMessage("boardMessage", `Selected ${square}. Loading legal moves...`);
        try {
          legalTargets = (await loadLegalMoves(square)).map((move) => move.slice(2, 4));
          setMessage("boardMessage", legalTargets.length ? `Legal targets: ${legalTargets.join(", ")}` : `No legal targets for ${square}.`, legalTargets.length ? "ok" : "err");
        } catch (error) {
          legalTargets = [];
          setMessage("boardMessage", error.message, "err");
        }
        renderBoard();
        return;
      }

      const source = selectedSquare;
      const sourceCoords = squareCoords(source);
      const sourcePiece = board[sourceCoords.row]?.[sourceCoords.col];
      const promotion = (sourcePiece === "P" && row === 0) || (sourcePiece === "p" && row === 7);
      let move = `${source}${square}`;
      if (promotion) {
        const chosen = (window.prompt("Promotion piece: q, r, b, or n", "q") || "q").trim().toLowerCase();
        move += ["q", "r", "b", "n"].includes(chosen) ? chosen : "q";
      }

      try {
        await submitMove(move);
      } catch (error) {
        setMessage("boardMessage", error.message, "err");
      } finally {
        selectedSquare = null;
        legalTargets = [];
        renderBoard();
      }
    }

    async function login() {
      setMessage("loginMessage", "Signing in...");
      const body = new URLSearchParams();
      body.set("username", $("loginUsername").value.trim());
      body.set("password", $("loginPassword").value);
      const response = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Login failed");
      token = data.access_token;
      user = decodeJwt(token);
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setMessage("loginMessage", `Signed in as ${user?.username || "player"}.`, "ok");
      updateHeader();
      await refreshStatus();
    }

    async function signup() {
      setMessage("signupMessage", "Creating account...");
      const response = await fetch(`${API_BASE}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: $("signupUsername").value.trim(),
          email: $("signupEmail").value.trim(),
          password: $("signupPassword").value,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Signup failed");
      setMessage("signupMessage", `Account created for ${data.username}. Log in next.`, "ok");
    }

    function stopPolling() {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = null;
    }

    function startPolling() {
      stopPolling();
      if (!currentGame?.id) return;
      pollTimer = setInterval(async () => {
        if (!currentGame?.id || !token) return;
        try {
          await loadGame(currentGame.id);
        } catch {
          // Ignore transient refresh failures.
        }
      }, 7000);
    }

    function bindTabs() {
      document.querySelectorAll(".tab").forEach((button) => {
        button.addEventListener("click", () => {
          document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.add("hidden"));
          button.classList.add("active");
          $(button.dataset.target).classList.remove("hidden");
        });
      });
    }

    function bindActions() {
      $("loginBtn").addEventListener("click", async () => {
        try { await login(); } catch (error) { setMessage("loginMessage", error.message, "err"); }
      });
      $("signupBtn").addEventListener("click", async () => {
        try { await signup(); } catch (error) { setMessage("signupMessage", error.message, "err"); }
      });
      $("logoutBtn").addEventListener("click", () => {
        token = "";
        user = null;
        currentGame = null;
        selectedSquare = null;
        legalTargets = [];
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        stopPolling();
        updateHeader();
        renderBoard();
        setMessage("loginMessage", "Logged out.", "ok");
      });
      $("createGameBtn").addEventListener("click", async () => {
        try { await createGame(); } catch (error) { setMessage("lobbyMessage", error.message, "err"); }
      });
      $("refreshStatusBtn").addEventListener("click", async () => {
        try { await refreshStatus(); } catch (error) { setMessage("lobbyMessage", error.message, "err"); }
      });
      $("reloadGameBtn").addEventListener("click", async () => {
        try {
          if (currentGame) await loadGame(currentGame.id);
        } catch (error) {
          setMessage("boardMessage", error.message, "err");
        }
      });
      $("flipBtn").addEventListener("click", () => {
        orientation = orientation === "white" ? "black" : "white";
        localStorage.setItem(ORIENTATION_KEY, orientation);
        renderBoard();
      });
      $("submitManualMoveBtn").addEventListener("click", async () => {
        try { await submitMove($("manualMove").value.trim()); } catch (error) { setMessage("boardMessage", error.message, "err"); }
      });
    }

    async function bootstrap() {
      bindTabs();
      bindActions();
      updateHeader();
      renderBoard();
      if (token) {
        user = user || decodeJwt(token);
        try {
          await refreshStatus();
        } catch (error) {
          setMessage("lobbyMessage", error.message, "err");
        }
      } else {
        setMessage("lobbyMessage", "Sign in to create or join a game.");
      }
    }

    bootstrap();
  </script>
</body>
</html>
"""


def _forward_to_backend(method: str, path: str, query: str, headers: dict[str, str], body: bytes | None) -> Response:
    target = f"{BACKEND_BASE_URL}/{path.lstrip('/')}"
    if query:
        target = f"{target}?{query}"

    request = urllib.request.Request(target, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as upstream:
            content = upstream.read()
            media_type = upstream.headers.get_content_type()
            charset = upstream.headers.get_content_charset()
            if charset and media_type.startswith("text/"):
                media_type = f"{media_type}; charset={charset}"
            return Response(content=content, status_code=upstream.status, media_type=media_type)
    except urllib.error.HTTPError as exc:
        content = exc.read()
        media_type = exc.headers.get_content_type() if exc.headers else "application/json"
        return Response(content=content, status_code=exc.code, media_type=media_type)
    except urllib.error.URLError as exc:
        return Response(content=str(exc.reason), status_code=502, media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(HTML)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request) -> Response:
    body = await request.body()
    headers = {}
    for key in ("authorization", "content-type", "accept"):
        value = request.headers.get(key)
        if value:
            headers[key.title()] = value
    payload = None if request.method in {"GET", "HEAD", "OPTIONS"} else body or None
    return await asyncio.to_thread(_forward_to_backend, request.method, path, request.url.query, headers, payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("frontend_app:app", host=FRONTEND_HOST, port=FRONTEND_PORT, reload=False)
