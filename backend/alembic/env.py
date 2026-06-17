"""
Alembic 环境配置
从 DATABASE_URL 环境变量读取数据库连接信息
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 将 backend/ 目录加入 sys.path，确保 app 包可被找到
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# 导入所有模型，确保 Base.metadata 包含所有表
from app.models import Base  # noqa: E402
from app.models import (  # noqa: E402, F401
    User,
    PasswordResetToken,
    Ledger,
    LedgerMember,
    ShareRequest,
    Subject,
    Transaction,
    TransactionItem,
    TransactionSubject,
    TransactionImage,
    RecurringTransaction,
    Budget,
    BudgetCategory,
    Preference,
    AuditLog,
)

# Alembic Config 对象
config = context.config

# 从 alembic.ini 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 从环境变量读取 DATABASE_URL
# asyncpg 驱动不支持同步迁移，改用 psycopg2（同步驱动）
database_url = os.environ.get("DATABASE_URL", "")

# asyncpg URL 转换为 psycopg2 同步 URL（Alembic 在同步模式运行）
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://"):
    # 保持兼容
    pass

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# 使用从模型导入的 Base.metadata，支持 --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（不需要数据库连接）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 支持枚举类型比较
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（需要数据库连接）"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # 支持枚举类型比较
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
