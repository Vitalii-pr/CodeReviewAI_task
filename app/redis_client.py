from redis.asyncio import Redis
from fastapi import Depends, Request

from typing import Optional, Annotated, Union

# Global Redis client
class Redis_client:

    def __init__(self, host: str, port: int, db:Optional[str] = None, password:Optional[str] = None, username:Optional[str] = None):
        """Initialize the Redis client."""
        self.host: str = host
        self.port: int = port
        self.db: Optional[str] = db
        self.password:Optional[str] = password
        self.username:Optional[str] = username
        self.redis_client: Redis

    async def initialize(self):
        """Asynchronous initialization of the Redis client."""
        self.redis_client = Redis(host=self.host, port=self.port, password=self.password, username=self.username, decode_responses=True)
        await self.redis_client.ping() 

    async def close_redis(self) -> None:
        """Close the Redis client."""
        if self.redis_client:
            await self.redis_client.close()

    def get_redis_client(self, request: Request) -> Optional['Redis_client']:
        """Provide the Redis client instance."""
        return request.app.state.redis_client
    
    async def exists(self, redis_key:str) -> int:
        return await self.redis_client.exists(redis_key)

    def generate_file_key(self, file_name:str, hash:str) -> str:
        return f"file_{file_name}:{hash}"
    
    def generate_repo_key(self, repo_hash:str) -> str:
        return f'repo_{repo_hash}'

    async def get_file_review_from_redis(self, redis_key:str) -> Optional[str]:
        return await self.redis_client.get(redis_key)

    async def write_file_review_to_redis(self, redis_key:str, content:str):
            return await self.redis_client.set(redis_key, content)

        
    

