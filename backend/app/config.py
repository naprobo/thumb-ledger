"""
应用配置模块
使用 pydantic-settings 从环境变量读取配置
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 数据库
    database_url: str = "postgresql+asyncpg://dev:dev@db:5432/bookkeeping_dev"

    # 安全
    secret_key: str = "change-me-to-a-strong-random-secret-key"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7

    # 邮件
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@bookkeeping.local"

    # 对象存储
    storage_backend: str = "local"
    local_storage_path: str = "/app/storage/images"
    s3_endpoint_url: str = "http://objstore:9000"
    s3_bucket_name: str = "bookkeeping-images"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # PostgreSQL（供 docker-compose 使用）
    postgres_db: str = "bookkeeping_dev"
    postgres_user: str = "dev"
    postgres_password: str = "dev"

    # MinIO
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"

    # 应用
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173,http://localhost:8025"

    # 密码重置令牌过期时间（分钟）
    password_reset_token_expire_minutes: int = 30

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> str:
        return v

    def get_allowed_origins_list(self) -> List[str]:
        """返回解析后的 CORS 允许来源列表"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取应用配置（使用 lru_cache 确保单例）"""
    return Settings()
