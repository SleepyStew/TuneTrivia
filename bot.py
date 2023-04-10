import asyncio
import os
import sys

import discord.utils
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import client, bot_token, log, usage_statistics

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@client.event
async def on_ready():
    print("Connected to Discord!")
    client.remove_command("help")
    log.info(f"Bot is ready. Logged in as {client.user}")

    if usage_statistics:
        requests.post('https://discord.com/api/webhooks/1094864074698924042/xaLmjyq6s7rCaPjdx8FbTwWAlTeXfib5OFsWVqBzZ8JQrQphGU8NhoRISqiJyahu5x8k', json={
            "content": None,
                "embeds": [
                    {
                        "title": "Usage Statistic",
                        f"description": f"Bot: {client.user} ({client.application_id}) \nGuilds: {len(client.guilds)} \nMembers: {len(client.users)}",
                        "color": 5814783
                    }
                ],
            "attachments": []
        })


def reload_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            client.reload_extension(f"cogs.{file[:-3]}")


@app.on_event("startup")
async def startup_event():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            client.load_extension(f"cogs.{file[:-3]}")

    try:
        asyncio.create_task(client.start(bot_token))
    except discord.LoginFailure:
        log.critical("Invalid Discord Token. Please check your config file.")
        sys.exit()


@app.get("/")
async def read_root():
    return {
        "id": client.application_id,
        "server_count": len(list(client.guilds)),
        "user_count": len(list(client.users)),
        "latency": client.latency,
        "status": client.status,
        "commands": [
            {"name": a.name, "description": a.description}
            for a in client.application_commands
        ],
        "activity": client.activity,
        "voice_clients": len(list(client.voice_clients)),
    }
