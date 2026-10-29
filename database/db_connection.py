"""Kết nối dữ liệu cục bộ. SQLite mặc định; có thể chọn MySQL qua .env."""
import os
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower().strip()
_sqlite_path = Path(os.getenv("DB_SQLITE_PATH", "data/diem_thi.sqlite3"))
SQLITE_PATH = _sqlite_path if _sqlite_path.is_absolute() else PROJECT_ROOT / _sqlite_path


def is_sample_data():
    """Chỉ xác nhận dữ liệu mẫu khi cơ sở dữ liệu có metadata tương ứng."""
    if DB_BACKEND != "sqlite" or not SQLITE_PATH.is_file():
        return False
    try:
        conn = sqlite3.connect(SQLITE_PATH.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT value FROM dataset_metadata WHERE key = ?", ("dataset_kind",)
            ).fetchone()
            return row is not None and row[0] == "sample"
        finally:
            conn.close()
    except sqlite3.Error:
        # Cơ sở dữ liệu cũ chưa có metadata: không suy đoán nguồn dữ liệu.
        return False


class _SQLiteCursor:
    """Giao diện tương thích với các truy vấn PyMySQL hiện có."""
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cursor.close()

    def execute(self, sql, params=()):
        return self.cursor.execute(sql.replace("%s", "?"), params)

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def close(self):
        self.cursor.close()


class _SQLiteConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return _SQLiteCursor(self.connection.cursor())

    def close(self):
        self.connection.close()


def get_connection():
    """Trả kết nối cho tra cứu; không tạo file SQLite rỗng nếu thiếu dữ liệu."""
    try:
        if DB_BACKEND == "sqlite":
            if not SQLITE_PATH.is_file():
                print(f"[DB] Chưa có dữ liệu: {SQLITE_PATH}. Hãy chạy python -m database.import_data")
                return None
            conn = sqlite3.connect(SQLITE_PATH.resolve().as_uri() + "?mode=rw", uri=True)
            conn.row_factory = sqlite3.Row
            return _SQLiteConnection(conn)
        if DB_BACKEND == "mysql":
            import pymysql
            return pymysql.connect(
                host=os.getenv("DB_HOST", "127.0.0.1").replace("@", "").strip(),
                user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "diem_thi_thpt"),
                port=int(os.getenv("DB_PORT", "3306")), charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        raise ValueError(f"DB_BACKEND không hợp lệ: {DB_BACKEND}")
    except Exception as exc:
        print(f"[DB ERROR] Không thể kết nối: {exc}")
        return None


def get_engine():
    """Trả SQLAlchemy engine cho Pandas."""
    try:
        if DB_BACKEND == "sqlite":
            if not SQLITE_PATH.is_file():
                print(f"[DB] Chưa có dữ liệu: {SQLITE_PATH}. Hãy chạy python -m database.import_data")
                return None
            return create_engine(URL.create("sqlite", database=str(SQLITE_PATH.resolve())))
        if DB_BACKEND == "mysql":
            url = URL.create(
                "mysql+pymysql", username=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                host=os.getenv("DB_HOST", "127.0.0.1").replace("@", "").strip(),
                port=int(os.getenv("DB_PORT", "3306")),
                database=os.getenv("DB_NAME", "diem_thi_thpt"), query={"charset": "utf8mb4"},
            )
            return create_engine(url, pool_pre_ping=True)
        raise ValueError(f"DB_BACKEND không hợp lệ: {DB_BACKEND}")
    except Exception as exc:
        print(f"[DB ERROR] Không thể tạo engine: {exc}")
        return None
