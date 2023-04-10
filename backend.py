import configparser
import logging
import random
import sys

import discord
from discord.ext import commands

intents = discord.Intents.all()

# Loading config.ini
config = configparser.ConfigParser()

try:
    config.read("config.ini")
except Exception as e:
    print("Error reading the config.ini file. Error: " + str(e))
    sys.exit()

#  Getting variables from config.ini
try:
    log_level: str = config.get("general", "log_level")
    raise_errors: bool = config.getboolean("general", "raise_errors")
    owner_id: int = config.getint("general", "your_discord_id")
    client_id: str = config.get("general", "client_id")

    bot_token: str = config.get("secret", "discord_token")
    spotify_id: str = config.get("secret", "spotify_client_id")
    spotify_secret: str = config.get("secret", "spotify_client_secret")

    wavelink_host: str = config.get("wavelink", "host")
    wavelink_port: int = int(config.get("wavelink", "port"))
    wavelink_password: str = config.get("wavelink", "password")

except Exception as err:
    print("Error getting variables from the config file. Error: " + str(err))
    sys.exit()


# Initializing the logger
def colorlogger(name="music-bot"):
    from colorlog import ColoredFormatter

    logger = logging.getLogger(name)
    stream = logging.StreamHandler()
    stream.setFormatter(
        ColoredFormatter(
            "%(reset)s%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s"
        )
    )
    logger.addHandler(stream)
    # Set logger level
    if log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.setLevel(log_level.upper())
    else:
        log.warning(f"Invalid log level {log_level}. Defaulting to INFO.")
        logger.setLevel("INFO")
    return logger  # Return the logger


log = colorlogger()

client = commands.Bot(intents=intents, command_prefix="tt!")  # Creating the Bot


embed_footers = [
    # This footer message is considered Copyright Notice and may not be removed or changed.
    "Made by SleepyStew#7777!",
    # Feel free to customize the rest of the footer messages.
    "Use /help to view all of TuneTrivia's commands!",
    "Use /stats to view live stats of TuneTrivia!",
    "Use /invite to add TuneTrivia to one of your servers!",
    "Use /support to join the support server!",
]


def random_footer():
    return embed_footers[random.randint(0, len(embed_footers) - 1)]


def embed_template():
    embed_template = discord.Embed(title="Music", color=int("2f3136", 16))
    embed_template.set_footer(
        text=random_footer(),
        # This Icon URL is considered Copyright Notice and may not be removed or changed.
        icon_url="https://cdn.discordapp.com/avatars/566951727182381057/9d1fafe95ffb1aebf8ef03baea9b4a71.webp?size=100",
    )
    return embed_template


def error_template(description: str) -> discord.Embed:
    _error_template = discord.Embed(description=description, color=0xFF0000)
    _error_template.set_footer(
        text=random_footer(),
        # This Icon URL is considered Copyright Notice and may not be removed or changed.
        icon_url="https://cdn.discordapp.com/avatars/566951727182381057/9d1fafe95ffb1aebf8ef03baea9b4a71.webp?size=100",
    )

    return _error_template.copy()
