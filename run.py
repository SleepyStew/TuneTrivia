from bot import app
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import nest_asyncio

nest_asyncio.apply()

if __name__ == "__main__":
    config = Config()
    print("running")
    config.bind = ["0.0.0.0:8152"]
    asyncio.run(serve(app, config))
