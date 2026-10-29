# thpt-2025-score-analysis

Ứng dụng tra cứu và phân tích điểm thi THPT 2025 bằng Python.

Hướng dẫn cài đặt, sao chép và khởi chạy trên Windows, macOS và Linux: [HUONG_DAN.md](HUONG_DAN.md).

## Bắt đầu nhanh

1. Cài Python 3.12 hoặc 3.13 có Tkinter và `venv`; kết nối Internet trong lần cài thư viện đầu tiên.
2. Tải hoặc clone kho, mở thư mục dự án, rồi chạy `run.bat` trên Windows hoặc `sh run.sh` trên macOS/Linux.
3. Lần đầu ứng dụng sẽ chuẩn bị cơ sở dữ liệu. Nếu không có CSV đầy đủ, ứng dụng dùng `data/sample.csv` gồm dữ liệu giả lập để trải nghiệm; các kết quả từ mẫu không phản ánh kết quả thi thực tế.
4. Chọn tab tra cứu hoặc đăng nhập quản trị bằng tài khoản mẫu `admin` / `admin123`.

Dữ liệu đầy đủ và cấu hình cá nhân không được đưa vào kho Git. Nếu có dữ liệu hợp lệ, xem [hướng dẫn sử dụng dữ liệu riêng](HUONG_DAN.md#sử-dụng-dữ-liệu-riêng).

## Giới thiệu

Đây là ứng dụng desktop viết bằng Python, phục vụ tra cứu và phân tích dữ liệu điểm thi THPT năm 2025. Ứng dụng có hai đối tượng sử dụng: thí sinh tra cứu kết quả của mình theo số báo danh và quản trị viên xem các biểu đồ, thống kê tổng hợp. Giao diện được xây dựng bằng Tkinter; dữ liệu mặc định được lưu trong SQLite ngay trong thư mục dự án.

## Chức năng chính

### Tra cứu thí sinh

Tại tab **Học Sinh Tra Cứu**, người dùng nhập số báo danh và chọn tra cứu. Khi tìm thấy dữ liệu, màn hình kết quả hiển thị thông tin thí sinh, điểm Toán, Ngữ văn và hai môn tự chọn, tổng điểm, điểm trung bình, trạng thái kết quả cùng tỷ lệ xếp hạng tương đối theo từng môn khi tính được.

Ô CCCD/mã bảo mật hiện chỉ là trường nhập tùy chọn; chương trình chưa kiểm tra thông tin này khi tra cứu. Vì vậy, không nên xem đây là cơ chế bảo vệ dữ liệu cá nhân.

### Phân tích dành cho quản trị viên

Sau khi đăng nhập, quản trị viên có thể chọn các nhóm chức năng trên bảng điều khiển:

1. **Phổ điểm 9 môn:** xem tổng quan và biểu đồ chi tiết theo môn, cùng các chỉ số thống kê như điểm trung bình, trung vị, điểm cao nhất và thấp nhất.
2. **Địa lý và khối thi:** so sánh kết quả theo tỉnh/thành phố, xếp hạng theo môn và phân tích các tổ hợp A00, A01, B00, C00, D01.
3. **Đề thi và hệ đào tạo:** xem phân tích độ khó, khả năng phân hóa, tương quan điểm giữa các môn, nhóm thí sinh, hệ đào tạo, điểm ưu tiên và điểm liệt.
4. **Phân tích chuyên sâu và thủ khoa:** xem các biểu đồ về giới tính, môn tự chọn, tổ hợp và thí sinh đạt điểm cao.

Tài khoản `admin` / `admin123` là tài khoản mẫu để chạy thử. Chức năng và số liệu cần được kiểm tra thêm trước khi sử dụng cho mục đích chính thức.

## Dữ liệu và cách hoạt động

1. Lần đầu chạy, trình khởi chạy tạo môi trường Python, cài thư viện và nhập CSV đầy đủ nếu có, hoặc CSV mẫu nếu không có, vào `data/diem_thi.sqlite3` nếu cơ sở dữ liệu này chưa tồn tại. Quá trình nhập thực hiện theo từng lô và không ghi đè cơ sở dữ liệu đã có.
2. Khi tra cứu, ứng dụng tìm thí sinh theo số báo danh trong cơ sở dữ liệu.
3. Khi mở chức năng phân tích, ứng dụng đọc dữ liệu vào Pandas, chuẩn hóa điểm môn tự chọn và tính thêm các tổ hợp xét tuyển. Dữ liệu được lưu tạm trong RAM để dùng lại; do tập dữ liệu lớn, thời gian tải và lượng RAM cần dùng phụ thuộc máy.
4. Matplotlib và Seaborn tạo biểu đồ để hiển thị trong giao diện Tkinter.

SQLite là cấu hình mặc định. Dự án cũng có tùy chọn kết nối MySQL đã chuẩn bị sẵn; cách cấu hình nằm trong [HUONG_DAN.md](HUONG_DAN.md). Một số phân loại trong phần phân tích dùng quy tắc và giá trị mặc định của chương trình khi dữ liệu thiếu, nên cần đối chiếu nguồn dữ liệu trước khi đưa ra kết luận.

## Cấu trúc dự án

| Tệp hoặc thư mục | Vai trò |
| --- | --- |
| `main.py` | Khởi động ứng dụng, kiểm tra kết nối dữ liệu và điều hướng các màn hình. |
| `views/` | Giao diện đăng nhập, tra cứu thí sinh và bảng điều khiển quản trị. |
| `controllers/` | Xử lý tra cứu, đăng nhập và phân tích dữ liệu. |
| `database/` | Kết nối cơ sở dữ liệu, chuẩn bị SQLite và nhập dữ liệu từ CSV. |
| `data/` | Chứa `sample.csv` giả lập; dữ liệu đầy đủ và SQLite tạo tại máy được bỏ qua bởi Git. |
| `utils/` | Các hàm hỗ trợ biểu đồ và xuất dữ liệu. |
| `requirements.txt` | Danh sách thư viện Python cần cài. |
| `run.bat`, `run.sh` | Trình khởi chạy tương ứng cho Windows và macOS/Linux. |
| `HUONG_DAN.md` | Hướng dẫn cài đặt, chạy và sao chép dự án sang máy khác. |

Dữ liệu nguồn và cơ sở dữ liệu có thể chứa thông tin cá nhân; không tải chúng, file `.env` hay môi trường Python lên kho công khai. Bộ dữ liệu mẫu đi kèm là dữ liệu giả lập, không phải kết quả thi thật.

## Các nội dung phân tích hướng tới

- Phổ điểm từng môn.
- Điểm trung bình từng môn.
- Điểm trung vị (Median).
- Điểm xuất hiện nhiều nhất (Mode).
- Độ lệch chuẩn.
- Điểm cao nhất, thấp nhất.
- Số lượng điểm 10.
- Số lượng điểm 0.
- Tỷ lệ dưới trung bình (<5).
- Tỷ lệ đạt từ 5 điểm trở lên.
- Tỷ lệ đạt từ 7, 8, 9 điểm trở lên.
- Phân bố điểm theo các khoảng (0–1, 1–2, ..., 9–10).
- Điểm trung bình theo tỉnh/thành phố.
- Xếp hạng các tỉnh theo từng môn.
- Tỷ lệ tốt nghiệp theo tỉnh.
- Phổ điểm các tổ hợp xét tuyển (A00, A01, B00, C00, D01,...).
- Đánh giá độ khó và khả năng phân hóa của đề thi.
- Tương quan điểm giữa các môn.
- Số lượng thí sinh lớp 12.
- Số lượng thí sinh tự do.
- Điểm trung bình thí sinh lớp 12.
- Điểm trung bình thí sinh tự do.
- Tỷ lệ tốt nghiệp theo đối tượng.
- Phổ điểm theo đối tượng.
- Số lượng thí sinh hệ THPT.
- Số lượng thí sinh hệ GDTX.
- Điểm trung bình theo hệ học.
- Tỷ lệ tốt nghiệp theo hệ học.
- Phổ điểm theo hệ học.
- Tỷ lệ điểm 10 theo hệ học.
