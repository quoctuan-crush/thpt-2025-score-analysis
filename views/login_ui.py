import tkinter as tk
from tkinter import ttk, messagebox
# Nhập class AuthController từ file controller để xử lý logic đăng nhập
from controllers.auth_controller import AuthController
from utils.sample_banner import show_sample_banner

class LoginUI:
    # Hàm khởi tạo: nhận cửa sổ cha (root) và hàm callback khi đăng nhập thành công
    def __init__(self, root, on_login_success_callback):
        self.root = root
        # Lưu trữ hàm callback để gọi sau khi xác thực thành công
        self.on_login_success = on_login_success_callback
        
        # Tạo một khung chứa (frame) làm nền cho giao diện đăng nhập
        self.frame = tk.Frame(self.root, bg="#f4f6f7")
        # Đặt khung vào cửa sổ, fill=tk.BOTH và expand=True giúp khung lấp đầy cửa sổ
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Gọi phương thức để thiết kế các nút bấm, ô nhập
        self.setup_ui()

    def setup_ui(self):
        # --- HEADER ---
        # Tạo một khung chứa tiêu đề
        header = tk.Frame(self.frame, bg="#1a5276", pady=15)
        header.pack(fill=tk.X)
        # Label hiển thị tên hệ thống
        tk.Label(header, text="HỆ THỐNG PHÂN TÍCH THÍ SINH THPT 2025", 
                 font=("Arial", 14, "bold"), fg="white", bg="#1a5276").pack()
        # Label hiển thị chú thích hệ thống
        tk.Label(header, text="Cổng Tra Cứu Điểm Thi & Quản Trị Hệ Thống", 
                 font=("Arial", 10, "italic"), fg="#d4efdf", bg="#1a5276").pack(pady=(3, 0))
        show_sample_banner(self.frame)

        # --- NOTEBOOK (TABS) ---
        # Sử dụng ttk.Notebook để tạo các tab chuyển đổi qua lại
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        # Tùy chỉnh kiểu hiển thị cho các Tab
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[20, 8])
        # Khởi tạo 2 khung nội dung riêng biệt cho 2 tab
        self.tab_student = ttk.Frame(self.notebook) # Tab dành cho học sinh
        self.tab_admin = ttk.Frame(self.notebook) # Tab dành cho quản trị viên
        # Thêm các tab vào giao diện với tiêu đề tương ứng
        self.notebook.add(self.tab_student, text=" Học Sinh Tra Cứu ")
        self.notebook.add(self.tab_admin, text=" Quản Trị Viên (Admin) ")
        # Gọi các hàm con để xây dựng chi tiết nội dung bên trong mỗi tab
        self.build_student_tab() # Xây dựng UI cho tab học sinh
        self.build_admin_tab() # Xây dựng UI cho tab admin

    # =================================================================
    # TAB 1: GIAO DIỆN TRA CỨU CHO HỌC SINH
    # =================================================================
    def build_student_tab(self):
        # Tạo một khung chứa bên trong tab học sinh với khoảng cách lề 
        frame = tk.Frame(self.tab_student, padx=40, pady=30, bg="white")
        frame.pack(fill=tk.BOTH, expand=True)
        # Tiêu đề chính của tab: "TRA CỨU KẾT QUẢ THI TỐT NGHIỆP"
        tk.Label(frame, text="TRA CỨU KẾT QUẢ THI TỐT NGHIỆP", font=("Arial", 13, "bold"), fg="#2c3e50", bg="white").pack(pady=(0, 15))
        
        # Nhập SBD
        tk.Label(frame, text="Số Báo Danh (SBD): *", font=("Arial", 10, "bold"), fg="#34495e", bg="white").pack(anchor=tk.W)
        # Ô nhập SBD
        self.entry_sbd = tk.Entry(frame, font=("Arial", 12), bd=2, relief=tk.GROOVE)
        self.entry_sbd.pack(fill=tk.X, pady=(5, 15), ipady=5)
        # Tự động đặt con trỏ chuột vào ô này khi vừa mở tab
        self.entry_sbd.focus()
        
        # Nhập CCCD / Ngày sinh (Tùy chọn)
        # Tiêu đề 
        tk.Label(frame, text="CCCD / Mã bảo mật (Tùy chọn):", font=("Arial", 10), fg="#7f8c8d", bg="white").pack(anchor=tk.W)
        # Ô nhập CCCD.
        self.entry_cccd = tk.Entry(frame, font=("Arial", 12), bd=2, relief=tk.GROOVE, show="*")
        self.entry_cccd.pack(fill=tk.X, pady=(5, 20), ipady=5)
        
        # Nút Tra Cứu -> LIÊN KẾT ĐÚNG HÀM handle_student_login
        # Tạo nút bấm "TRA CỨU ĐIỂM THI NGAY"
        btn_search = tk.Button(frame, text="🔍 TRA CỨU ĐIỂM THI NGAY", font=("Arial", 11, "bold"),
                               bg="#27ae60", fg="white", activebackground="#1e8449", activeforeground="white",
                               cursor="hand2", pady=10, relief=tk.RAISED, bd=2, 
                               command=self.handle_student_login)
        btn_search.pack(fill=tk.X) # Nút bấm giãn theo chiều ngang của khung
        
        #  Nút này giúp người dùng điền nhanh SBD mẫu để test hệ thống
        btn_sample = tk.Button(frame, text="💡 Điền thử SBD mẫu (10000001)", font=("Arial", 9, "italic"),
                               bg="#fef9e7", fg="#d35400", bd=1, relief=tk.FLAT, cursor="hand2",
                               command=lambda: [self.entry_sbd.delete(0, tk.END), self.entry_sbd.insert(0, "10000001")])
        btn_sample.pack(pady=15)
        # Cho phép người dùng nhấn phím "Enter" (Return) ở bất kỳ ô nhập nào
        self.entry_sbd.bind('<Return>', lambda event: self.handle_student_login())
        self.entry_cccd.bind('<Return>', lambda event: self.handle_student_login())

    # =================================================================
    # TAB 2: GIAO DIỆN ĐĂNG NHẬP ADMIN
    # =================================================================
    def build_admin_tab(self):
        # Tạo khung chứa nội dung cho tab Admin
        frame = tk.Frame(self.tab_admin, padx=40, pady=30, bg="white")
        frame.pack(fill=tk.BOTH, expand=True)
        # Tiêu đề của tab Admin
        tk.Label(frame, text="ĐĂNG NHẬP TRUNG TÂM CHỈ HUY", font=("Arial", 13, "bold"), fg="#c0392b", bg="white").pack(pady=(0, 15))
        # Nhãn dán tài khoản Admin
        tk.Label(frame, text="Tài khoản (Username):", font=("Arial", 10, "bold"), fg="#34495e", bg="white").pack(anchor=tk.W)
        # Ô nhập liệu cho Username của Admin
        self.entry_user = tk.Entry(frame, font=("Arial", 12), bd=2, relief=tk.GROOVE)
        self.entry_user.pack(fill=tk.X, pady=(5, 15), ipady=5)
        # Tự động điền giá trị "admin" vào ô này để giúp bạn tiết kiệm thời gian khi kiểm thử (test)
        self.entry_user.insert(0, "admin") 
        # Nhãn dán mật khẩu
        tk.Label(frame, text="Mật khẩu (Password):", font=("Arial", 10, "bold"), fg="#34495e", bg="white").pack(anchor=tk.W)
        # Ô nhập mật khẩu
        self.entry_pass = tk.Entry(frame, font=("Arial", 12), bd=2, relief=tk.GROOVE, show="*")
        self.entry_pass.pack(fill=tk.X, pady=(5, 20), ipady=5)
        # Điền sẵn mật khẩu mẫu để thuận tiện cho việc kiểm thử
        self.entry_pass.insert(0, "admin123")
        
        # Nút Đăng nhập -> LIÊN KẾT ĐÚNG HÀM handle_admin_login
        # command=self.handle_admin_login: gọi hàm xác thực dành riêng cho Admin
        btn_login = tk.Button(frame, text="🛡️ ĐĂNG NHẬP HỆ THỐNG", font=("Arial", 11, "bold"),
                              bg="#c0392b", fg="white", activebackground="#922b21", activeforeground="white",
                              cursor="hand2", pady=10, relief=tk.RAISED, bd=2, 
                              command=self.handle_admin_login)
        btn_login.pack(fill=tk.X)
        # Cho phép Admin nhấn phím "Enter" ở cả ô Username và Password để thực hiện đăng nhập nhanh
        self.entry_user.bind('<Return>', lambda event: self.handle_admin_login())
        self.entry_pass.bind('<Return>', lambda event: self.handle_admin_login())

    # =================================================================
    # HÀM XỬ LÝ 1: HỌC SINH TRA CỨU (CHẾ ĐỘ 1 CỬA SỔ)
    # =================================================================
    def handle_student_login(self):
        # Lấy giá trị từ các ô nhập và xóa khoảng trắng thừa ở đầu cuối bằng
        sbd = self.entry_sbd.get().strip()
        cccd_or_dob = self.entry_cccd.get().strip()
        # Kiểm tra tính hợp lệ: Nếu chưa nhập SBD thì cảnh báo và đưa con trỏ về ô nhập SBD
        if not sbd:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập Số báo danh (SBD) để tra cứu!")
            self.entry_sbd.focus()
            return
        # Gọi đến tầng Controller (AuthController) để kiểm tra thông tin trong CSDL
        user_info = AuthController.login_student(sbd, cccd_or_dob)
        # Nếu tìm thấy thông tin thí sinh (user_info trả về dữ liệu)
        if user_info:
            # 1. Ẩn khung Đăng nhập đi để nhường chỗ cho Bảng điểm
            self.frame.pack_forget()
            
            # 2. Hàm Quay lại: Bấm nút Back ở Bảng điểm thì hiện lại trang Tra cứu SBD
            def quay_lai_trang_login():
                self.root.title("Hệ Thống Phân Tích Big Data 1 Triệu Thí Sinh THPT 2025")
                self.frame.pack(fill=tk.BOTH, expand=True)
                self.entry_sbd.focus()
                
            # 3. Nhúng Bảng điểm đè thẳng lên đúng cửa sổ hiện tại
            # Truyền vào: cửa sổ chính, dữ liệu user, và hàm quay lại trang login
            from views.student_dashboard import StudentDashboard
            StudentDashboard(self.root, user_info, on_logout_callback=quay_lai_trang_login)
        # Nếu không tìm thấy thông tin thí sinh
        else:
            messagebox.showerror("Không tìm thấy", f"Không tìm thấy thí sinh nào có SBD: [{sbd}]\n\n Mẹo: Hãy bấm vào nút 'Điền thử SBD mẫu' ở bên dưới để test nhé!")

    # =================================================================
    # HÀM XỬ LÝ 2: ADMIN ĐĂNG NHẬP
    # =================================================================
    def handle_admin_login(self):
        # Lấy thông tin tài khoản và mật khẩu từ ô nhập liệu, loại bỏ khoảng trắng thừa
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        # Kiểm tra nếu người dùng để trống bất kỳ trường nào
        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ tài khoản và mật khẩu Admin!")
            return
        # Gọi hàm xác thực từ Controller (kiểm tra thông tin với CSDL)
        user_info = AuthController.login_admin(username, password)
        # Nếu xác thực thành công (user_info trả về dữ liệu user)
        if user_info:
            # Kiểm tra nếu hàm callback 'on_login_success' đã được định nghĩa
            if self.on_login_success:
                self.on_login_success(user_info)
        # Nếu xác thực thất bại
        else:
            # Thông báo lỗi và gợi ý thông tin đăng nhập mặc định để hỗ trợ test
            messagebox.showerror("Lỗi đăng nhập", "Tài khoản hoặc mật khẩu Quản trị viên không chính xác!\n(Mặc định: admin / admin123)")
