from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.redis_client import Redis_client
from app.api.routes import router
from app.config import settings

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    redis_client = Redis_client(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    await redis_client.initialize()
    app.state.redis_client = redis_client 
    try:
        yield
    finally:
        await redis_client.close_redis()

app = FastAPI(lifespan=app_lifespan)


@app.get('/')
async def health_checker():
    return JSONResponse(content={"status":"working"}, status_code=200)

app.include_router(router)
