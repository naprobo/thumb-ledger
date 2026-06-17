"""
数据库连接模块
- 创建 async engine（asyncpg 驱动）
- 提供 AsyncSession 工厂
- 提供 get_db FastAPI 依赖项
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


def _build_async_engine():
    """构建 AsyncEngine（延迟创建，避免在 import 时读取配置）"""
    settings = get_settings()
    database_url = settings.database_url
    # 确保使用 asyncpg 驱动
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        database_url,
        echo=settings.app_env == "development",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# 模块级 engine 和 session factory（延迟初始化）
_engine = None
_async_session_factory = None


def get_engine():
    """获取（或初始化）AsyncEngine 单例"""
    global _engine
    if _engine is None:
        _engine = _build_async_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取（或初始化）AsyncSession 工厂单例"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖项：提供数据库 session。

    用法示例：
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
