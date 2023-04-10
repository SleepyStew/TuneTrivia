from bot import app
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import nest_asyncio

nest_asyncio.apply()

if __name__ == "__main__":
    config = Config()
    config.bind = ["127.0.0.1:7000"]
    asyncio.run(serve(app, config))
