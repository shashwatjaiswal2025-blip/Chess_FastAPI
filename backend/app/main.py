from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.Router import game
from backend.app.database.database import lifespan
from backend.app.Router import login


app = FastAPI(lifespan=lifespan)
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "login.html")

app.include_router(login.router)
app.include_router(game.router)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
