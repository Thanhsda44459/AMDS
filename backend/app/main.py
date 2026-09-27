from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_db, connect_db
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — fail-soft để backend vẫn start được khi Mongo chưa lên
    try:
        await connect_db()
        print("[startup] MongoDB connected ✅")
    except Exception as e:
        print(f"[startup] MongoDB chưa sẵn sàng: {e}")
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Quan4 Culinary Tourism API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "quan4-culinary-api"}