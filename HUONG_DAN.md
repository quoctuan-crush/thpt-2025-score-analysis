# Chạy dự án trên máy khác

Ứng dụng dùng Python, giao diện Tkinter và SQLite. Không cần cài MySQL nếu dùng cấu hình mặc định.

## Chuẩn bị

- Cài Python 3.12 hoặc 3.13 có hỗ trợ Tkinter và tạo môi trường ảo (`venv`). Trên Windows, chọn thêm Python vào PATH; trên Linux có thể cần cài thêm gói `python3-venv` và `python3-tk` theo bản phân phối. macOS cần bản Python có Tcl/Tk.
- Lần chạy đầu cần kết nối Internet để cài thư viện, và đủ dung lượng trống cho các thư viện và cơ sở dữ liệu được tạo từ CSV. Quá trình nhập dữ liệu có thể mất vài phút.
- Tải hoặc sao chép mã nguồn, `requirements.txt`, các file chạy và `data/sample.csv`. Không sao chép `.venv` hoặc `.venv-portable`: môi trường ảo phải tạo lại trên từng máy.

## Khởi chạy

- **Windows:** mở `run.bat` trong thư mục dự án.
- **macOS / Linux:** mở Terminal tại thư mục dự án và chạy `sh run.sh`.

Lần đầu, chương trình tạo `.venv-portable`, cài thư viện rồi tạo `data/diem_thi.sqlite3`. Nếu có file CSV đầy đủ tại `data/diem_thi_thpt_2025_github.csv`, chương trình nhập file đó; nếu không, chương trình dùng `data/sample.csv` là dữ liệu giả lập. Các lần sau sẽ dùng lại cơ sở dữ liệu đã tạo. Trình nhập từ chối ghi đè cơ sở dữ liệu hiện có.

Nếu môi trường `.venv-portable` được sao chép từ máy khác hoặc bị lỗi, hãy đổi tên hoặc xóa **chỉ** thư mục `.venv-portable` trên máy đó, sau đó chạy lại. Nếu báo thiếu Python, Tkinter, `venv` hoặc không cài được thư viện, hãy cài các thành phần tương ứng và kiểm tra kết nối mạng.

Tài khoản quản trị mẫu là `admin` / `admin123`, chỉ phù hợp chạy thử hoặc học tập. Dữ liệu mẫu được tạo để minh họa, không phản ánh kết quả thi thực tế. Dữ liệu đầy đủ có thể chứa thông tin cá nhân; không đưa lên GitHub công khai.

## Sử dụng dữ liệu riêng

Kho Git chỉ kèm dữ liệu mẫu. Nếu có quyền sử dụng dữ liệu đầy đủ đúng cấu trúc cột, đặt file tại `data/diem_thi_thpt_2025_github.csv` trước lần chạy đầu; ứng dụng sẽ ưu tiên file này. File dữ liệu riêng và các cơ sở dữ liệu được Git bỏ qua.

Nếu trước đó đã chạy bằng dữ liệu mẫu, hãy đóng ứng dụng và đổi tên hoặc sao lưu `data/diem_thi.sqlite3`, rồi chạy lại để tạo cơ sở dữ liệu mới từ CSV đầy đủ. Lưu ý kiểm tra và giữ lại cơ sở dữ liệu cũ nếu cần: ứng dụng không tự thay thế nó. Ngược lại, có thể chạy thủ công lệnh nhập với `--csv` và `--database` để tạo một file khác.

Trước khi đăng lên GitHub, kiểm tra `git status --short` và bảo đảm `.env`, file CSV riêng, SQLite, môi trường ảo và tài liệu cá nhân không nằm trong danh sách sẽ gửi. Quy tắc `.gitignore` chỉ áp dụng tự động cho tệp chưa được Git theo dõi.

## Tùy chọn

Để tạo dữ liệu thủ công sau khi đã cài các thư viện, chạy từ thư mục dự án: `python -m database.import_data`. Lệnh sẽ không ghi đè file SQLite đã tồn tại. Có thể chỉ định đường dẫn khác bằng `--csv` và `--database`.

Cấu hình mặc định dùng SQLite. Nếu muốn tiếp tục dùng MySQL đã có sẵn, đặt `DB_BACKEND=mysql` cùng các biến `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` trong `.env`; cần tự chuẩn bị MySQL và dữ liệu. `database/schema.sql` là schema MySQL cũ, có lệnh xóa bảng nên không chạy trên dữ liệu cần giữ.
