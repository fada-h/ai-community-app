"""初始化数据库：建库（MySQL）→ 建表 → 写入演示数据。

用法：
    python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402


def ensure_database() -> None:
    """MySQL 下先创建数据库（utf8mb4）；SQLite 无需处理。"""
    if settings.is_sqlite:
        print("[1/3] SQLite 模式，跳过建库")
        return

    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url)
    database = url.database
    server_url = url.set(database=None)
    engine = create_engine(server_url, connect_args={"connect_timeout": 5})
    with engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    engine.dispose()
    print(f"[1/3] 数据库已就绪：{database}")


def main() -> None:
    ensure_database()

    init_db()
    print("[2/3] 数据表已创建")

    with SessionLocal() as db:
        seeded = seed_if_empty(db)
    print("[3/3] 演示数据" + ("已写入" if seeded else "已存在，跳过"))
    print("\n完成。启动后端：uvicorn app.main:app --reload --port 8000")


if __name__ == "__main__":
    main()
