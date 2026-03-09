from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from database import engine, Base
from config import DB_HOST, DB_PORT, DB_NAME, REDIS_URL
from links.router import router as links_router
from auth.users import fastapi_users, auth_backend
from auth.schemas import UserCreate, UserRead
from tasks.router import router as tasks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"Connected to {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Redis connected to {REDIS_URL}")
    
    yield
    
    await engine.dispose()
    await redis.close()
    print("Shuts down")

app = FastAPI(title="URL Shortener Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(links_router)
app.include_router(tasks_router)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

@app.get("/")
async def root():
    return {"message": "URL Shortener Service", "status": "running"}

