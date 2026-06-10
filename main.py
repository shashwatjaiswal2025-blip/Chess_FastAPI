import asyncio
import os
import sys

from fastapi import FastAPI
from database import lifespan
from Router import login, game

app = FastAPI(lifespan=lifespan)



@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(login.router)
app.include_router(game.router)
