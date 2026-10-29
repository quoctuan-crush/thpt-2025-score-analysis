"""Tạo cơ sở dữ liệu SQLite một lần từ CSV, không ghi đè dữ liệu cũ.

Chạy từ thư mục dự án: python -m database.import_data
"""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time

import pandas as pd

from database.db_connection import PROJECT_ROOT, SQLITE_PATH

CSV_FILE_PATH = PROJECT_ROOT / "data" / "diem_thi_thpt_2025_github.csv"
COLUMN_MAPPING = {
    'Số báo danh': 'sbd', 'Họ và tên': 'ho_ten', 'Ngày sinh': 'ngay_sinh',
    'Giới tính': 'gioi_tinh', 'CCCD': 'cccd', 'Địa chỉ tỉnh': 'tinh_thanh',
    'Toán': 'toan', 'Ngữ văn': 'ngu_van', 'Môn tự chọn 1': 'mon_tu_chon_1',
    'Điểm tự chọn 1': 'diem_tu_chon_1', 'Môn tự chọn 2': 'mon_tu_chon_2',
    'Điểm tự chọn 2': 'diem_tu_chon_2', 'Khu vực ưu tiên': 'khu_vuc_uu_tien',
    'Đối tượng ưu tiên': 'doi_tuong_uu_tien', 'Điểm ưu tiên': 'diem_uu_tien',
    'Điểm khuyến khích': 'diem_khuyen_khich', 'Hệ đào tạo': 'he_dao_tao',
    'Năm tốt nghiệp': 'nam_tot_nghiep', 'Mã hội đồng thi': 'ma_hoi_dong',
    'Mã hội đồng': 'ma_hoi_dong', 'Tổng điểm': 'tong_diem',
    'Điểm trung bình': 'diem_trung_binh', 'Trạng thái': 'trang_thai',
}
NUMERIC_COLUMNS = ('toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2',
                   'diem_uu_tien', 'diem_khuyen_khich', 'tong_diem', 'diem_trung_binh')

SCHEMA = """
CREATE TABLE students (
 sbd TEXT PRIMARY KEY NOT NULL, ho_ten TEXT, ngay_sinh TEXT, gioi_tinh TEXT,
 cccd TEXT, tinh_thanh TEXT, toan REAL, ngu_van REAL, mon_tu_chon_1 TEXT,
 diem_tu_chon_1 REAL, mon_tu_chon_2 TEXT, diem_tu_chon_2 REAL,
 khu_vuc_uu_tien TEXT, doi_tuong_uu_tien TEXT, diem_uu_tien REAL,
 diem_khuyen_khich REAL, he_dao_tao TEXT, nam_tot_nghiep INTEGER,
 ma_hoi_dong TEXT, tong_diem REAL, diem_trung_binh REAL, trang_thai TEXT
);
CREATE TABLE admins (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT DEFAULT 'admin',
 created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE dataset_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def import_csv(csv_path, destination, dataset_kind="custom"):
    csv_path, destination = Path(csv_path).resolve(), Path(destination).resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy CSV: {csv_path}")
    if destination.exists():
        raise FileExistsError(f"Cơ sở dữ liệu đã tồn tại, không ghi đè: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".diem_thi_import_", suffix=".sqlite3", dir=destination.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    total = 0
    start = time.monotonic()
    try:
        with closing(sqlite3.connect(temp_path)) as conn:
            conn.executescript(SCHEMA)
            conn.execute("INSERT INTO dataset_metadata (key, value) VALUES (?, ?)",
                         ("dataset_kind", dataset_kind))
            conn.commit()
            for chunk in pd.read_csv(csv_path, chunksize=10000, dtype=str, encoding="utf-8-sig"):
                chunk.columns = [str(col).strip() for col in chunk.columns]
                chunk.rename(columns=COLUMN_MAPPING, inplace=True)
                if chunk.columns.duplicated().any():
                    raise ValueError("CSV có các cột trùng tên sau khi chuẩn hóa")
                if 'sbd' not in chunk.columns:
                    raise ValueError("CSV thiếu cột Số báo danh")
                chunk = chunk[[col for col in chunk.columns if col in COLUMN_MAPPING.values()]].copy()
                chunk['sbd'] = chunk['sbd'].str.strip()
                if chunk['sbd'].isna().any() or (chunk['sbd'] == '').any():
                    raise ValueError("CSV chứa số báo danh trống")
                for col in NUMERIC_COLUMNS:
                    if col in chunk:
                        chunk[col] = pd.to_numeric(chunk[col].str.replace(',', '.', regex=False), errors='coerce')
                chunk.to_sql('students', conn, if_exists='append', index=False)
                total += len(chunk)
                print(f"Đã nhập {total:,} thí sinh...", flush=True)
            if not total:
                raise ValueError("CSV không có dữ liệu thí sinh")
            conn.executescript("""
                CREATE INDEX idx_student_cccd ON students(cccd);
                CREATE INDEX idx_tinh_thanh ON students(tinh_thanh);
                CREATE INDEX idx_phan_loai ON students(he_dao_tao, trang_thai);
                CREATE INDEX idx_diem_tb ON students(diem_trung_binh DESC);
            """)
        # Windows rename từ chối ghi đè; POSIX dùng hard link để tránh race.
        if os.name == 'nt':
            os.rename(temp_path, destination)
        else:
            os.link(temp_path, destination)
        print(f"Hoàn tất {total:,} thí sinh sau {time.monotonic() - start:.1f} giây: {destination}")
    finally:
        temp_path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tạo dữ liệu SQLite từ CSV; không ghi đè file đã có.")
    parser.add_argument('--csv', type=Path, default=CSV_FILE_PATH, help='Đường dẫn CSV nguồn')
    parser.add_argument('--database', type=Path, default=SQLITE_PATH, help='Đường dẫn file SQLite đích')
    args = parser.parse_args(argv)
    try:
        sample_path = PROJECT_ROOT / 'data' / 'sample.csv'
        kind = 'sample' if args.csv.resolve() == sample_path.resolve() else 'custom'
        import_csv(args.csv, args.database, dataset_kind=kind)
    except Exception as exc:
        detail = exc.__cause__ if exc.__cause__ is not None else exc
        print(f"Không thể nhập dữ liệu: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
