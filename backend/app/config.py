"""全局配置：密钥与连接串只从环境变量读取，禁止硬编码。"""
import os
import secrets
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 backend/.env（不存在时不影响运行）
load_dotenv(BASE_DIR / ".env")


def _read_secret() -> str:
    """SESSION 密钥：优先环境变量，否则生成并持久化到 backend/.secret。"""
    env_secret = os.getenv("SECRET_KEY", "").strip()
    if env_secret:
        return env_secret
    file = BASE_DIR / ".secret"
    if file.exists():
        return file.read_text(encoding="utf-8").strip()
    value = secrets.token_hex(32)
    file.write_text(value, encoding="utf-8")
    return value


def _database_url() -> str:
    """优先 DATABASE_URL；否则用 MYSQL_* 拼装；最后退化为 SQLite。"""
    explicit = os.getenv("DATABASE_URL", "").strip()
    if explicit:
        return explicit

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "campus_ai_community")

    if not password and os.getenv("ALLOW_SQLITE_FALLBACK", "1") == "1":
        # 未配置 MySQL 密码时用 SQLite 兜底，保证开箱即跑
        data_dir = BASE_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + (data_dir / "campus.db").as_posix()

    return (
        "mysql+pymysql://"
        + quote_plus(user)
        + ":"
        + quote_plus(password)
        + "@"
        + host
        + ":"
        + port
        + "/"
        + database
        + "?charset=utf8mb4"
    )


class Settings:
    """运行期配置，构造时一次性读取环境变量。"""

    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "青禾")
        self.app_subtitle = os.getenv("APP_SUBTITLE", "AI 校园社区")
        self.environment = os.getenv("ENV", "development")
        self.secret_key = _read_secret()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
        )

        self.database_url = _database_url()
        self.is_sqlite = self.database_url.startswith("sqlite")

        self.cors_origins = [
            item.strip()
            for item in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173").split(",")
            if item.strip()
        ]

        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.deepseek_base_url = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        )
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        self.ai_disclaimer = "AI 生成内容仅供参考，重要信息请以学校官方通知为准"


settings = Settings()
