import tkinter as tk  # Nhập thư viện tkinter (chuyên dùng để tạo giao diện đồ họa GUI) và gọi tắt là 'tk'
from tkinter import ttk # Nhập module ttk chứa các thành phần giao diện hiện đại hơn (dù file này chưa dùng tới)
from utils.sample_banner import show_sample_banner

class StudentDashboard:
    # Hàm __init__ là hàm khởi tạo, tự động chạy đầu tiên khi bạn tạo một đối tượng từ lớp này
    def __init__(self, root, student_data, on_logout_callback=None):
        self.root = root # Lưu lại cửa sổ chính của ứng dụng vào biến của lớp để dùng sau
        self.on_logout = on_logout_callback # Lưu lại hàm callback (hàm sẽ được gọi khi bấm nút "Quay lại")
        
        # --- BƯỚC 1: XỬ LÝ VÀ LÀM SẠCH DỮ LIỆU ĐẦU VÀO ---
        # Kiểm tra xem student_data truyền vào có phải là kiểu từ điển (dict) không. Nếu không, gán bằng từ điển rỗng {}
        self.raw = student_data if isinstance(student_data, dict) else {}
        self.clean = {} # Tạo một từ điển mới để chứa dữ liệu đã được "làm sạch" (chuẩn hóa key)
        
        # Duyệt qua từng cặp khóa (k) và giá trị (v) trong dữ liệu gốc
        for k, v in self.raw.items():
            # Chuyển khóa thành chuỗi, viết thường toàn bộ, xóa dấu gạch dưới và khoảng trắng
            # Ví dụ: "Ho_Ten" hoặc "Họ Tên" sẽ đều biến thành "hoten"
            k_clean = str(k).lower().replace('_', '').replace(' ', '')
            self.clean[k_clean] = v # Lưu giá trị vào từ điển mới với khóa đã được làm sạch
        
        # --- BƯỚC 2: LẤY THÔNG TIN CƠ BẢN CHO TIÊU ĐỀ CỬA SỔ ---
        # Dùng hàm get_val (tự viết bên dưới) để tìm họ tên bằng nhiều từ khóa khác nhau
        ho_ten = self.get_val('ho_ten', 'hoten', 'ten', 'fullname', 'name', default='Thí sinh')
        sbd = self.get_val('sbd', 'id', 'student_id', default='N/A') # Lấy số báo danh
        
        # Đặt tên tiêu đề trên thanh bar trên cùng của cửa sổ phần mềm
        self.root.title(f"Kết Quả Tra Cứu Điểm Thi THPT 2025 - Thí sinh: {ho_ten} (SBD: {sbd})")
        
        # --- BƯỚC 3: TẠO KHUNG CHỨA CHÍNH TỔNG THỂ ---
        # Tạo một Frame (khu vực chứa) tổng bao trùm toàn bộ giao diện, màu nền xám nhạt (#f4f6f7)
        self.main_frame = tk.Frame(self.root, bg="#f4f6f7")
        # Đẩy Frame này lên màn hình, cho phép lấp đầy toàn bộ không gian (fill=BOTH, expand=True)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Gọi hàm setup_ui để bắt đầu vẽ các chi tiết bên trong main_frame
        self.setup_ui()

    # Hàm hỗ trợ trích xuất dữ liệu thông minh, tránh lỗi chương trình bị sập khi thiếu cột trong Database
    def get_val(self, *keys, default='N/A'):
        """Quét dữ liệu linh hoạt, hỗ trợ mọi biến thể tên cột MySQL"""
        for k in keys: # Lặp qua danh sách các từ khóa truyền vào (vd: 'ho_ten', 'hoten'...)
            # Kiểm tra: Nếu từ khóa có trong dữ liệu gốc VÀ giá trị không rỗng (None) VÀ không phải chuỗi rỗng/nan
            if k in self.raw and self.raw[k] is not None and str(self.raw[k]).strip() not in ['', 'nan', 'None']:
                return self.raw[k] # Trả về luôn giá trị đó
            
            # Nếu không tìm thấy ở bản gốc, thử làm sạch từ khóa đang tìm
            k_clean = str(k).lower().replace('_', '').replace(' ', '')
            # Tìm trong bản dữ liệu đã làm sạch (self.clean)
            if k_clean in self.clean and self.clean[k_clean] is not None and str(self.clean[k_clean]).strip() not in ['', 'nan', 'None']:
                return self.clean[k_clean]
        
        return default # Nếu thử mọi cách vẫn không có, trả về giá trị mặc định (thường là 'N/A')

    # Hàm chịu trách nhiệm vẽ (render) toàn bộ giao diện
    def setup_ui(self):
        # =============================================================
        # --- PHẦN HEADER (THANH TIÊU ĐỀ MÀU XANH TRÊN CÙNG) ---
        # =============================================================
        # Tạo khung Header, màu nền xanh đậm (#1a5276), có khoảng cách lề trên/dưới (pady) và trái/phải (padx)
        header = tk.Frame(self.main_frame, bg="#1a5276", pady=15, padx=25)
        header.pack(fill=tk.X) # Ép Header lấp đầy toàn bộ chiều ngang (X)
        show_sample_banner(self.main_frame)
        
        # Tạo nút "Quay Lại", gán lệnh (command) là hàm self.handle_back
        btn_back = tk.Button(header, text="⬅ QUAY LẠI TRANG TRA CỨU", font=("Arial", 10, "bold"),
                             bg="#c0392b", fg="white", activebackground="#922b21", activeforeground="white",
                             cursor="hand2", padx=15, pady=5, relief=tk.RAISED, borderwidth=2, command=self.handle_back)
        btn_back.pack(side=tk.LEFT) # Đẩy nút này neo về phía bên trái của Header
        
        # Tạo dòng chữ tiêu đề lớn
        tk.Label(header, text="CỔNG THÔNG TIN KẾT QUẢ KỲ THI TỐT NGHIỆP THPT 2025", 
                 font=("Arial", 14, "bold"), fg="white", bg="#1a5276").pack(side=tk.RIGHT) # Neo về phía bên phải

        # =============================================================
        # 1. KHUNG THÔNG TIN CÁ NHÂN 
        # =============================================================
        # Tạo một LabelFrame (Khung có viền và có dòng chữ tiêu đề lồng trên viền)
        info_frame = tk.LabelFrame(self.main_frame, text="THÔNG TIN CHI TIẾT THÍ SINH ", font=("Arial", 11, "bold"), 
                                   fg="#1a5276", bg="white", padx=20, pady=15, bd=2, relief=tk.GROOVE)
        info_frame.pack(fill=tk.X, padx=30, pady=(15, 15)) # Đẩy lên màn hình, cách hai bên 30px, cách trên/dưới 15px
        
        # Tạo một Frame ẩn bên trong để dùng lưới (grid) xếp các thông tin thành 3 cột
        info_grid = tk.Frame(info_frame, bg="white")
        info_grid.pack(fill=tk.X)
        # Cấu hình 3 cột có tỉ lệ độ rộng bằng nhau (weight=1)
        info_grid.columnconfigure(0, weight=1); info_grid.columnconfigure(1, weight=1); info_grid.columnconfigure(2, weight=1)
        
        # Rút trích thông tin từ database bằng hàm get_val an toàn
        sbd_val = str(self.get_val('sbd', 'id', 'student_id'))
        hoten_val = str(self.get_val('ho_ten', 'hoten', 'ten', 'fullname', 'name'))
        ngaysinh_val = str(self.get_val('ngay_sinh', 'ngaysinh', 'dob', 'birthdate'))
        gioitinh_val = str(self.get_val('gioi_tinh', 'gioitinh', 'gender', 'sex'))
        he_val = str(self.get_val('he_dao_tao', 'hedaotao', 'system', default='GDPT'))
        kv_val = str(self.get_val('khu_vuc_uu_tien', 'khuvucuutien', 'khuvuc', default='KV3'))
        tinh_val = str(self.get_val('tinh_thanh', 'tinhthanh', 'province', 'city', 'location', default='Sở GD&ĐT'))
        doi_tuong_val = str(self.get_val('doi_tuong_thi', 'doituongthi', 'doituong', 'doi_tuong', default='Học sinh lớp 12'))
        
        # Lấy tên 2 môn tự chọn và ghép thành chuỗi danh sách 4 môn thi
        ten_tc1 = str(self.get_val('mon_tu_chon_1', 'montuchon1', 'subject1', default='Tự chọn 1'))
        ten_tc2 = str(self.get_val('mon_tu_chon_2', 'montuchon2', 'subject2', default='Tự chọn 2'))
        mon_thi_val = f"Toán, Văn, {ten_tc1}, {ten_tc2}"

        # Đổ dữ liệu lên UI bằng hàm create_info_item (hàng và cột tính từ 0)
        # Hàng 1 (row=0)
        self.create_info_item(info_grid, "Số Báo Danh:", sbd_val, 0, 0) # Nằm ở Hàng 0, Cột 0
        self.create_info_item(info_grid, "Họ và Tên:", hoten_val, 0, 1)  # Nằm ở Hàng 0, Cột 1
        self.create_info_item(info_grid, "Ngày Sinh:", ngaysinh_val, 0, 2) # Nằm ở Hàng 0, Cột 2
        
        # Hàng 2 (row=1)
        self.create_info_item(info_grid, "Giới Tính:", gioitinh_val, 1, 0)
        self.create_info_item(info_grid, "Hệ Đào Tạo:", he_val, 1, 1)
        self.create_info_item(info_grid, "Khu Vực Ưu Tiên:", kv_val, 1, 2)

        # Hàng 3 (row=2)
        self.create_info_item(info_grid, "Hội Đồng Thi:", tinh_val, 2, 0)
        self.create_info_item(info_grid, "Đối Tượng Thi:", doi_tuong_val, 2, 1)
        self.create_info_item(info_grid, "Các Môn Thi:", mon_thi_val, 2, 2)

        # =============================================================
        # CẤU TRÚC LAYOUT 2 CỘT BÊN DƯỚI (Cho phần Điểm và Xếp hạng)
        # =============================================================
        # Tạo một khung chứa (container) để chia đôi màn hình phần bên dưới
        score_container = tk.Frame(self.main_frame, bg="#f4f6f7")
        score_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        # Cấu hình 2 cột bằng nhau (weight=3)
        score_container.columnconfigure(0, weight=3); score_container.columnconfigure(1, weight=3)
        
        # =============================================================
        # 2. BÊN TRÁI: ĐIỂM THI CHI TIẾT 4 MÔN
        # =============================================================
        # Khung chứa điểm thi, đặt ở dòng 0, cột 0 (bên trái) của score_container
        score_frame = tk.LabelFrame(score_container, text=" 📊 ĐIỂM THI CHI TIẾT 4 MÔN ", font=("Arial", 11, "bold"), 
                                    fg="#c0392b", bg="white", padx=15, pady=15, bd=2, relief=tk.GROOVE)
        score_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10)) # sticky="nsew" giúp khung tự giãn ra lấp đầy ô lưới
        
        # Lấy điểm số từ database
        diem_tc1 = self.get_val('diem_tu_chon_1', 'diemtuchon1', 'score1')
        diem_tc2 = self.get_val('diem_tu_chon_2', 'diemtuchon2', 'score2')

        # Gom tên môn và điểm thành một danh sách (list) để lặp cho dễ
        display_subjects = [
            ("Môn Toán", self.get_val('toan', 'math', 'math_score')),
            ("Môn Ngữ Văn", self.get_val('ngu_van', 'nguvan', 'van', 'literature')),
            (f"Môn {ten_tc1}", diem_tc1),
            (f"Môn {ten_tc2}", diem_tc2)
        ]
        
        tong_diem_thuc_te = 0.0 # Biến để tự cộng dồn tổng điểm đề phòng DB không có sẵn cột tổng điểm
        
        # Lặp qua 4 môn thi để in ra giao diện
        for idx, (sub_name, score_val) in enumerate(display_subjects):
            # Tạo hiệu ứng màu nền xen kẽ: môn chẵn màu xám nhạt, môn lẻ màu trắng cho dễ nhìn
            row_bg = "#f9fbfd" if idx % 2 == 0 else "white" 
            
            # Tạo một hàng ngang cho môn thi hiện tại
            row_frame = tk.Frame(score_frame, bg=row_bg, pady=8, padx=10)
            row_frame.pack(fill=tk.X, pady=2)
            
            # In tên môn thi nằm sát lề trái
            tk.Label(row_frame, text=sub_name, font=("Arial", 11, "bold"), bg=row_bg, fg="#2c3e50").pack(side=tk.LEFT)
            
            # Xử lý logic hiển thị màu sắc của điểm số
            score_str = str(score_val)
            score_color = "#2c3e50" # Màu mặc định (xanh đen)
            try:
                val = float(score_val) # Ép kiểu sang số thực để tính toán
                tong_diem_thuc_te += val # Cộng dồn vào tổng điểm
                score_str = f"{val:.2f}" # Định dạng điểm luôn có 2 số thập phân (vd: 8.50)
                
                # Logic màu sắc: 10 điểm -> Xanh lá; <= 1 điểm (Liệt) -> Đỏ
                if val == 10.0: score_color = "#27ae60"
                elif val <= 1.0: score_color = "#e74c3c"
            except: pass # Nếu lỗi (ví dụ điểm là chữ "Vắng"), thì bỏ qua toán học, in ra chữ "Vắng" màu xanh đen
            
            # In điểm số nằm sát lề phải
            tk.Label(row_frame, text=score_str, font=("Arial", 12, "bold"), bg=row_bg, fg=score_color).pack(side=tk.RIGHT)

        # =============================================================
        # 3. BÊN PHẢI: KẾT QUẢ & XẾP HẠNG TOP % TỪNG MÔN
        # =============================================================
        # Khung chứa xếp hạng, đặt ở dòng 0, cột 1 (bên phải)
        result_frame = tk.LabelFrame(score_container, text="  ĐÁNH GIÁ & XẾP HẠNG NĂNG LỰC ", font=("Arial", 11, "bold"), 
                                     fg="#27ae60", bg="white", padx=15, pady=15, bd=2, relief=tk.GROOVE)
        result_frame.grid(row=0, column=1, sticky="nsew")
        
        # --- KHỐI HIỂN THỊ ĐỖ/TRƯỢT ---
        status = str(self.get_val('trang_thai', 'trangthai', 'ketqua', 'status', default='Đang cập nhật'))
        # Đổi màu nền khối dựa trên chữ: Có chữ "đỗ" -> Xanh lá, "trượt" -> Đỏ, còn lại (Đang chờ) -> Vàng cam
        status_color = "#27ae60" if "đỗ" in status.lower() or "pass" in status.lower() else ("#e74c3c" if "trượt" in status.lower() or "fail" in status.lower() else "#f39c12")
        
        # Vẽ một ô hình chữ nhật nổi bật hiển thị trạng thái
        st_box = tk.Frame(result_frame, bg=status_color, pady=10)
        st_box.pack(fill=tk.X, pady=(0, 15))
        tk.Label(st_box, text=f"KẾT QUẢ: {status.upper()}", font=("Arial", 12, "bold"), fg="white", bg=status_color).pack()
        
        # --- KHỐI HIỂN THỊ TỔNG ĐIỂM ---
        tong_val = self.get_val('tong_diem', 'tongdiem', 'tong', 'total')
        # Nếu DB không có cột tổng điểm, tự lấy biến đã cộng dồn (tong_diem_thuc_te) ở trên để xài
        if tong_val == 'N/A' and tong_diem_thuc_te > 0:
            tong_str = f"{tong_diem_thuc_te:.2f} điểm"
        else:
            try: tong_str = f"{float(tong_val):.2f} điểm" # Format 2 số thập phân
            except: tong_str = str(tong_val) + " điểm" if tong_val != 'N/A' else "N/A"

        # Tương tự với điểm trung bình
        tb_val = self.get_val('diem_trung_binh', 'diemtrungbinh', 'diemtb', 'diem_tb_4_mon')
        try: tb_str = f"{float(tb_val):.2f} điểm"
        except: tb_str = str(tb_val) + " điểm" if tb_val != 'N/A' else "N/A"
        
        # In tổng điểm và điểm TB lên khung bằng hàm create_block_score
        self.create_block_score(result_frame, "Tổng Điểm 4 Môn:", tong_str, "#c0392b")
        self.create_block_score(result_frame, "Điểm TB Toàn Khóa:", tb_str, "#1a5276")
        
        # Vẽ một đường kẻ ngang (phân cách) bằng một Frame cao 1 pixel
        tk.Frame(result_frame, height=1, bg="#bdc3c7").pack(fill=tk.X, pady=8) 
        
        # --- TỰ ĐỘNG TÍNH TOP % XẾP HẠNG TỪNG MÔN THI TỪ MYSQL ---
        colors = ["#2980b9", "#d35400", "#27ae60", "#8e44ad"] # Mảng màu cho 4 môn xếp hạng
        for idx, (sub_name, score_val) in enumerate(display_subjects):
            # Gọi hàm calc_top_percent để lấy chuỗi xếp hạng từ DB
            top_pct_str = self.calc_top_percent(sub_name, score_val)
            # In ra màn hình với màu luân phiên
            self.create_block_score(result_frame, f"🏆 Xếp Hạng {sub_name}:", top_pct_str, colors[idx % len(colors)])

    # =============================================================
    # CÁC HÀM HỖ TRỢ VẼ GIAO DIỆN VÀ XỬ LÝ LOGIC (HELPER FUNCTIONS)
    # =============================================================
    
    def create_info_item(self, parent, label_text, value_text, row, col):
        """Hàm tự động vẽ 1 ô thông tin cá nhân (VD: SBD: 123456) vào đúng vị trí hàng/cột"""
        frame = tk.Frame(parent, bg="white", pady=6)
        frame.grid(row=row, column=col, sticky="w") # Sticky="w" nghĩa là bám vào lề Tây (trái)
        # Chữ tiêu đề nhỏ màu xám
        tk.Label(frame, text=label_text, font=("Arial", 10), fg="#7f8c8d", bg="white").pack(anchor=tk.W)
        # Chữ giá trị lớn in đậm màu đen
        tk.Label(frame, text=value_text, font=("Arial", 11, "bold"), fg="#2c3e50", bg="white").pack(anchor=tk.W)

    def create_block_score(self, parent, label_text, value_text, color):
        """Hàm tự động vẽ 1 dòng kết quả bên tay phải (VD: 🏆 Xếp hạng môn Toán: Top 10%)"""
        frame = tk.Frame(parent, bg="white", pady=4)
        frame.pack(fill=tk.X)
        # Tên mục nằm sát mép trái
        tk.Label(frame, text=label_text, font=("Arial", 11, "bold"), fg="#34495e", bg="white").pack(side=tk.LEFT)
        # Giá trị (Top % hoặc Điểm) nằm sát mép phải và có màu sắc tùy chỉnh
        tk.Label(frame, text=str(value_text), font=("Arial", 11, "bold"), fg=color, bg="white").pack(side=tk.RIGHT)

    def calc_top_percent(self, sub_name, score_val):
        """Kết nối MySQL: Tính tỷ lệ % thí sinh cả nước bị người này đánh bại ở môn tương ứng"""
        try:
            val_f = float(score_val) # Ép điểm thành số thập phân. Lỗi -> nhảy xuống except
            from database.db_connection import get_connection # Import file kết nối database
            conn = get_connection()
            if not conn: return "Đang cập nhật" # Nếu rớt mạng DB thì báo đang cập nhật
            
            cursor = conn.cursor()
            clean_name = sub_name.replace("Môn ", "").strip().lower() # Cắt bỏ chữ "Môn" để đối chiếu dễ hơn
            
            # Nếu là môn Toán
            if clean_name in ['toán', 'toan']:
                # Đếm số học sinh có điểm môn toán CAO HƠN điểm người này (higher)
                cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE toan > %s", (val_f,))
                higher = cursor.fetchone().get('cnt', 0)
                # Đếm tổng số học sinh đã nộp bài (điểm > 0 và không NULL) (total)
                cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE toan IS NOT NULL AND toan > 0")
                total = cursor.fetchone().get('cnt', 1)
                
            # Nếu là môn Văn (tương tự như môn Toán)
            elif clean_name in ['ngữ văn', 'văn', 'ngu van', 'ngu_van']:
                cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE ngu_van > %s", (val_f,))
                higher = cursor.fetchone().get('cnt', 0)
                cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE ngu_van IS NOT NULL AND ngu_van > 0")
                total = cursor.fetchone().get('cnt', 1)
                
            # Nếu là Môn Tự Chọn
            else:
                # Do môn tự chọn có thể nằm ở cột mon_tu_chon_1 HOẶC mon_tu_chon_2, nên query phức tạp hơn
                # Đếm những bạn cùng thi môn này mà có điểm cao hơn
                query_higher = "SELECT COUNT(*) as cnt FROM students WHERE (mon_tu_chon_1 = %s AND diem_tu_chon_1 > %s) OR (mon_tu_chon_2 = %s AND diem_tu_chon_2 > %s)"
                cursor.execute(query_higher, (sub_name.replace("Môn ", "").strip(), val_f, sub_name.replace("Môn ", "").strip(), val_f))
                higher = cursor.fetchone().get('cnt', 0)
                
                # Đếm tổng số bạn đăng ký thi môn này
                query_total = "SELECT COUNT(*) as cnt FROM students WHERE mon_tu_chon_1 = %s OR mon_tu_chon_2 = %s"
                cursor.execute(query_total, (sub_name.replace("Môn ", "").strip(), sub_name.replace("Môn ", "").strip()))
                total = cursor.fetchone().get('cnt', 1)
            
            conn.close() # Đóng kết nối để không treo máy chủ
            
            if total > 0:
                # Công thức lấy top %: (Số người điểm cao hơn / Tổng số người thi) * 100
                pct = (higher / total) * 100
                # Trả về kết quả, làm tròn 1 chữ số thập phân, nếu top 0.0% thì báo tối thiểu là 0.1% để tránh lỗi
                return f"Top {max(0.1, round(pct, 1))}% Cả Nước"
        except Exception:
            pass # Nếu lỗi ép kiểu (điểm là N/A) hoặc lỗi DB thì tự động rơi xuống dòng return mặc định
        
        return "Đang cập nhật" # Không hiển thị số liệu giả khi không tính được

    def handle_back(self):
        """Hàm thực thi khi nhấn nút Quay Lại"""
        self.main_frame.destroy() # Hủy/Xóa toàn bộ giao diện bảng điểm hiện tại khỏi bộ nhớ
        if self.on_logout: # Nếu lúc khởi tạo class có truyền hàm chuyển trang vào
            self.on_logout() # Gọi hàm chuyển trang đó (thường là để mở lại trang Đăng Nhập / Nhập SBD)
