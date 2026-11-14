"""青禾 · AI 校园社区 —— FastAPI 入口。

启动：
    uvicorn app.main:app --reload --port 8000
接口文档：
    http://127.0.0.1:8000/docs
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import SessionLocal, init_db
from .routers import admin, ai, auth, messages, meta, posts, users
from .seed import seed_if_empty
from .ws import router as ws_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("qinghe")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with SessionLocal() as db:
        if seed_if_empty(db):
            logger.info("已写入演示数据（8 位用户 / 14 篇帖子）")
    logger.info("数据库：%s", "SQLite" if settings.is_sqlite else "MySQL")
    yield


app = FastAPI(
    title=settings.app_name + " · " + settings.app_subtitle,
    description="校园 AI 社区后端：AI 问答 / 发帖助手 / 搭子匹配 / 私信",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (meta.router, auth.router, users.router, posts.router, ai.router, messages.router, admin.router, ws_router):
    app.include_router(router)


@app.get("/api/health", tags=["系统"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "sqlite" if settings.is_sqlite else "mysql",
    }


# ---------------------------------------------------------------------------
# 单服务部署：若存在前端构建产物，则由 FastAPI 直接托管 SPA。
# 这样线上只需要一个公网地址，且前后端同源，免去 CORS 与 WebSocket 跨域问题。
# 本地开发（frontend 未 build）时该段自动跳过，不影响 5173 热更新。
# ---------------------------------------------------------------------------
DIST_DIR = Path(
    os.getenv("FRONTEND_DIST", str(Path(__file__).resolve().parents[2] / "frontend" / "dist"))
)

if DIST_DIR.is_dir():
    if (DIST_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """静态文件优先；其余路由交给前端（history 模式刷新不 404）。"""
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
