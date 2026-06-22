"""
FastAPI 应用入口
"""
import logging
import subprocess
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app.config import get_settings
from app.middleware.content_type import reject_unexpected_content_type
from app.routers.auth import limiter as auth_limiter

logger = logging.getLogger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
}


def apply_security_headers(response) -> None:
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期事件：启动时执行数据库迁移"""
    settings = get_settings()
    logger.info("Running Alembic migrations...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Alembic output: %s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Alembic migration failed: %s", e.stderr)
        raise RuntimeError(f"Database migration failed: {e.stderr}") from e

    from app.services.recurring import create_recurring_scheduler

    scheduler = create_recurring_scheduler()
    scheduler.start()
    app.state.recurring_scheduler = scheduler
    logger.info("Application startup complete.")
    yield

    scheduler.shutdown(wait=False)
    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Thumb Ledger API",
        version="0.1.0",
        description="Thumb Ledger 后端 API",
        lifespan=lifespan,
    )
    app.state.limiter = auth_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ----------------------------------------------------------------
    # CORS 中间件
    # ----------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(reject_unexpected_content_type)

    # ----------------------------------------------------------------
    # 安全响应头中间件
    # ----------------------------------------------------------------
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        apply_security_headers(response)
        return response

    # ----------------------------------------------------------------
    # 全局异常处理
    # ----------------------------------------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception for %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred.",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )

    # ----------------------------------------------------------------
    # 路由挂载（占位，后续任务中逐步取消注释）
    # ----------------------------------------------------------------
    from app.routers import admin, auth, budget, images, ledgers, notifications, preferences, recurring, suggestions, transactions
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(ledgers.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(preferences.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")
    app.include_router(budget.router, prefix="/api/v1")
    app.include_router(images.router, prefix="/api/v1")
    app.include_router(recurring.router, prefix="/api/v1")
    app.include_router(suggestions.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    # 健康检查端点
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
