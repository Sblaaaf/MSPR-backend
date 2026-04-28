import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
DATABASE_NAME = os.getenv("MONGODB_DB", "recommendation_db")

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(MONGODB_URL)
    _db = _client[DATABASE_NAME]
    await _client.admin.command("ping")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    return _db
