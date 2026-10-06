from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import close_db, connect_db, get_database
from app.routers import health, poi


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — fail-soft để backend vẫn start được khi Mongo chưa lên
    try:
        await connect_db()
        # Gọi thử get_database() + list_collection_names() để xác nhận
        # kết nối + đọc DB hoạt động, đúng như Verification của DB-001.
        db = get_database()
        collections = await db.list_collection_names()
        print(f"[startup] MongoDB connected ✅ ({len(collections)} collections)")
    except Exception as e:
        print(f"[startup] MongoDB chưa sẵn sàng: {e}")
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="AMDS API",
    version="0.1.0",
    lifespan=lifespan,
)

# Mở CORS rộng tạm thời cho Phase 0 để Vite (localhost:5173) gọi được API.
# Sau này phải thu hẹp ở SEC-003 và đổi sang origin cụ thể khi dùng cookie ở AUTH-010.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(poi.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "amds-api"}