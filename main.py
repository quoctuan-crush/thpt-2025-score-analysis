import tkinter as tk # Nhập thư viện tkinter để tạo giao diện đồ họa (GUI)
from tkinter import messagebox # Nhập module hộp thoại để hiển thị các thông báo (lỗi, cảnh báo, thành công)
import os # Nhập thư viện os để tương tác với hệ điều hành (xử lý đường dẫn file/thư mục)
import sys # Nhập thư viện sys để can thiệp vào các biến và hàm của trình thông dịch Python
import traceback # Nhập thư viện traceback để in ra lịch sử dòng code bị lỗi (rất hữu ích khi debug)

# BƯỚC CHUẨN BỊ QUAN TRỌNG TRƯỚC KHI CHẠY APP:
# Đảm bảo Python nhận diện đúng đường dẫn thư mục gốc của dự án. 
# Điều này giúp các lệnh như 'from views.login_ui import...' ở bên dưới không bị lỗi "ModuleNotFoundError".
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

class MainApplication:
    # Hàm khởi tạo, chạy đầu tiên khi phần mềm được bật
    def __init__(self):
        # In ra màn hình Terminal (màn hình đen) một đoạn text giới thiệu (Console Log)
        print("\n" + "="*70)
        print("HỆ THỐNG PHÂN TÍCH TRIỆU THÍ SINH THPT 2025")
        print("="*70 + "\n")
        
        # 1. KHỞI TẠO CỬA SỔ CHÍNH
        self.root = tk.Tk() # Tạo ra cửa sổ chính duy nhất của toàn bộ chương trình (cửa sổ mẹ)
        self.root.title("Hệ Thống Phân Tích Thí Sinh THPT 2025") # Đặt tiêu đề cho phần mềm
        self.root.geometry("600x500") # Cài đặt kích thước mặc định ban đầu: Rộng 600px, Cao 500px
        self.root.minsize(550, 450) # Chặn không cho người dùng thu nhỏ cửa sổ quá mức này (tránh vỡ giao diện)
        self.center_window(600, 500) # Gọi hàm tự viết để căn giữa cửa sổ ra chính giữa màn hình máy tính
        
        # Biến này dùng để theo dõi xem màn hình nào (Login, Dashboard...) đang được hiển thị. 
        # Ban đầu chưa có gì nên gán bằng None.
        self.current_ui = None

        # 2. KIỂM TRA DATABASE KHI KHỞI ĐỘNG
        # Gọi hàm kiểm tra kết nối cơ sở dữ liệu an toàn (không làm sập phần mềm nếu lỗi)
        self.check_database_safe()

    def center_window(self, width, height):
        """Hàm hỗ trợ căn giữa cửa sổ ra chính giữa màn hình máy tính"""
        # Lấy chiều rộng và chiều cao thực tế của màn hình máy tính người dùng
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Công thức toán học tính tọa độ điểm đặt góc trên bên trái của cửa sổ phần mềm 
        # sao cho nó nằm ngay giữa màn hình
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        
        # Áp dụng chuỗi định dạng hình học của Tkinter (Ví dụ: '600x500+250+150')
        self.root.geometry(f'{int(width)}x{int(height)}+{int(x)}+{int(y)}')

    def check_database_safe(self):
        """Kiểm tra kết nối dữ liệu trước khi mở giao diện."""
        print("[HỆ THỐNG] Đang kiểm tra kết nối tới cơ sở dữ liệu...")
        try: # Thử thực thi khối lệnh rủi ro (kết nối DB)
            from database.db_connection import get_connection # Chỗ này import cục bộ (chỉ import khi cần gọi)
            conn = get_connection() # Cố gắng tạo kết nối
            
            if conn: # Nếu kết nối thành công (conn có dữ liệu)
                print("[HỆ THỐNG] Kết nối cơ sở dữ liệu thành công! Hệ thống sẵn sàng hoạt động.")
                conn.close() # Test xong thì đóng lại ngay để nhường tài nguyên cho các tính năng khác
            else: # Nếu hàm get_connection() trả về False/None (do sai mật khẩu, chưa bật XAMPP...)
                print("[CẢNH BÁO] Không thể kết nối tới dữ liệu. Phần mềm sẽ mở ở chế độ xem trước giao diện.")
                # Hiển thị thông báo Popup (hộp thoại) cho người dùng biết
                messagebox.showwarning(
                    "Cảnh Báo Kết Nối Dữ Liệu", 
                    "Chưa kết nối được với cơ sở dữ liệu. Hãy chạy run.bat (Windows) hoặc run.sh (macOS/Linux) để chuẩn bị dữ liệu.\n\n"
                    "Phần mềm vẫn sẽ hiển thị giao diện để bạn trải nghiệm, nhưng các tính năng tra cứu hoặc đăng nhập sẽ không tìm thấy dữ liệu!"
                )
        except Exception as e: # Nếu có lỗi văng ra trong khối try (VD: thiếu file module db_connection)
            print(f"[CẢNH BÁO] Lỗi kiểm tra kết nối dữ liệu: {e}")
        
        # Luôn luôn mở màn hình đăng nhập dù Database có sập đi chăng nữa (để tránh app bị tắt ngóm không rõ lý do)
        self.show_login_screen()

    def don_dep_giao_dien_cu(self):
        """Xóa sạch tất cả các widget (khung, nút, nhãn) cũ trên cửa sổ để chừa chỗ vẽ màn hình mới"""
        # self.root.winfo_children() trả về một danh sách chứa tất cả các thành phần giao diện đang nằm trong cửa sổ chính
        for widget in self.root.winfo_children():
            widget.destroy() # Xóa vĩnh viễn thành phần đó khỏi bộ nhớ và màn hình
        self.current_ui = None # Đặt lại trạng thái màn hình hiện tại về rỗng

    def show_login_screen(self):
        """Màn hình 1: Cổng Đăng nhập Admin & Tra cứu Điểm thi Học sinh"""
        self.don_dep_giao_dien_cu() # Quét dọn nhà cửa sạch sẽ trước khi mời giao diện mới vào
        
        # Thiết lập lại kích thước cửa sổ về mặc định cho màn hình đăng nhập (vì màn hình khác có thể đang phóng to)
        self.root.state('normal') # Thoát chế độ toàn màn hình (nếu đang ở toàn màn hình)
        self.root.geometry("600x500") # Thu nhỏ kích thước lại
        self.center_window(600, 500) # Căn giữa lại cửa sổ
        self.root.title("Hệ Thống Phân Tích Thí Sinh THPT 2025") # Trả lại tên tiêu đề gốc

        try:
            # Nhập module LoginUI từ thư mục views
            from views.login_ui import LoginUI
            # Khởi tạo giao diện Đăng nhập, truyền cửa sổ chính (root) và hàm callback khi login thành công
            self.current_ui = LoginUI(self.root, on_login_success_callback=self.handle_login_success)
        except Exception as e: # Nếu source code của file LoginUI bị lỗi (vd lỗi cú pháp, lùi lề sai)
            print("[LỖI NGHIÊM TRỌNG] Không thể vẽ màn hình Đăng nhập (LoginUI):")
            traceback.print_exc() # In chi tiết toàn bộ các dòng code dẫn đến lỗi ra Terminal để DEV dễ sửa
            # Bật popup báo lỗi cho người dùng
            messagebox.showerror("Lỗi Mã Nguồn Giao Diện", f"Không thể hiển thị màn hình Đăng nhập do lỗi mã nguồn:\n\n{e}\n\n👉 Hãy nhìn xuống màn hình đen Terminal để xem dòng nào bị lỗi nhé!")

    def handle_login_success(self, user_info):
        """Hàm điều hướng trung tâm khi người dùng xác thực thành công"""
        # Lấy thông tin quyền (role) từ dữ liệu truyền vào và viết hoa toàn bộ để dễ so sánh
        role = user_info.get("role", "").upper() 
        if role == "ADMIN": # Nếu là Quản trị viên
            print(f"[XÁC THỰC] Quản trị viên '{user_info.get('username')}' đăng nhập thành công. Đang mở Bảng điều khiển...")
            # Gọi hàm chuyển trang sang Bảng điều khiển (Dashboard)
            self.show_admin_dashboard(user_info)

    def show_admin_dashboard(self, admin_info):
        """Màn hình 2: Trung tâm Chỉ huy Quản trị viên (Phóng to toàn màn hình)"""
        self.don_dep_giao_dien_cu() # Xóa giao diện Login đi
        try:
            # Khởi tạo màn hình AdminDashboard
            from views.admin_dashboard import AdminDashboard
            # Gửi quyền điều khiển cửa sổ root cho AdminDashboard, truyền thông tin admin vào, 
            # và đưa kèm hàm self.show_login_screen để khi họ bấm "Đăng xuất" thì nó sẽ gọi hàm này quay lại trang Login.
            self.current_ui = AdminDashboard(self.root, admin_info=admin_info, on_logout_callback=self.show_login_screen)
        except Exception as e: # Xử lý lỗi an toàn nếu file admin_dashboard.py có vấn đề
            print("[LỖI NGHIÊM TRỌNG] Không thể mở Bảng điều khiển Quản trị viên:")
            traceback.print_exc()
            messagebox.showerror("Lỗi Trang Quản Trị", f"Có lỗi xảy ra khi mở trang Quản trị viên:\n\n{e}")

    def run(self):
        """Kích hoạt vòng lặp chính để duy trì cửa sổ phần mềm hoạt động"""
        # mainloop() là vòng lặp vô hạn của Tkinter. Nó sẽ giữ cửa sổ trên màn hình 
        # và liên tục lắng nghe các sự kiện (chuột, bàn phím). Không có lệnh này, phần mềm sẽ chạy qua và tắt cụp ngay lập tức.
        self.root.mainloop()

# =================================================================
# ĐIỂM KHỞI ĐỘNG (ENTRY POINT) - Đoạn code này chỉ chạy khi file main.py được thực thi trực tiếp
# =================================================================
if __name__ == "__main__":
    try:
        app = MainApplication() # Tạo một thực thể (instance) của phần mềm
        app.run() # Gọi hàm run() để bắt đầu vòng lặp giao diện
    except Exception as e:
        # Nếu có lỗi nghiêm trọng ở mức độ toàn hệ thống (hiếm khi xảy ra ở đây vì đã xử lý nội bộ hết rồi)
        print("[LỖI CHÍNH] Hệ thống gặp sự cố bất ngờ và phải dừng lại:")
        traceback.print_exc()
