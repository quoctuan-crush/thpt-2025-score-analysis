"""Prepare the default local database on first launch."""
import sys

from database.db_connection import DB_BACKEND, PROJECT_ROOT, SQLITE_PATH


def main():
    if DB_BACKEND != "sqlite" or SQLITE_PATH.is_file():
        return 0
    from database.import_data import CSV_FILE_PATH, import_csv

    sample_path = PROJECT_ROOT / "data" / "sample.csv"
    if CSV_FILE_PATH.is_file():
        csv_path, dataset_kind = CSV_FILE_PATH, "full"
        print("Chưa có dữ liệu SQLite. Đang nhập dữ liệu từ CSV; vui lòng chờ...", flush=True)
    else:
        csv_path, dataset_kind = sample_path, "sample"
        print("Không tìm thấy CSV đầy đủ. Đang dùng dữ liệu mẫu tổng hợp, không phải điểm thi thật.", flush=True)
    try:
        import_csv(csv_path, SQLITE_PATH, dataset_kind=dataset_kind)
    except Exception as exc:
        print(f"Không thể chuẩn bị dữ liệu: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
