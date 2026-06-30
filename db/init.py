import os

from dotenv import load_dotenv
from tortoise import Tortoise

load_dotenv()

# Exported so aerich can discover the config (reads DATABASE_URL from .env)
TORTOISE_ORM = {
    "connections": {"default": os.getenv("DATABASE_URL", "")},
    "apps": {
        "models": {
            "models": ["db.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}


async def init_db(database_url: str) -> None:
    await Tortoise.init(
        db_url=database_url,
        modules={"models": ["db.models"]},
        use_tz=True,
        timezone="UTC",
    )
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()
