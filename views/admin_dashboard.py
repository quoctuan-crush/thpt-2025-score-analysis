import sys
import os
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import controllers.data_analysis as da
from utils.sample_banner import show_sample_banner


class AdminDashboard:
    def __init__(self, root, admin_info, on_logout_callback=None):
        self.root = root
        self.admin_info = admin_info
        self.on_logout = on_logout_callback

        self.root.title(f"Hệ Thống Phân Tích Thí Sinh THPT - [{self.admin_info.get('full_name', 'Admin')}]")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        # Tk hỗ trợ phóng to khác nhau trên Windows, Linux và macOS.
        try:
            self.root.state('zoomed')
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)
            except tk.TclError:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        self.setup_ui()

        print("[UI] Đang nạp dữ liệu ngầm bằng Đa luồng (Threading)...")
        threading.Thread(target=da.get_all_data, daemon=True).start()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#1a5276", pady=15, padx=20)
        header.pack(fill=tk.X)

        lbl_title = tk.Label(header, text="TRUNG TÂM PHÂN TÍCH DỮ LIỆU ĐIỂM THI THPT 2025",
                             font=("Arial", 16, "bold"), fg="white", bg="#1a5276")
        lbl_title.pack(side=tk.LEFT)

        btn_logout = tk.Button(header, text="Đăng xuất", font=("Arial", 10, "bold"),
                               bg="#c0392b", fg="white", activebackground="#922b21", activeforeground="white",
                               cursor="hand2", padx=15, pady=4, relief=tk.FLAT, command=self.handle_logout)
        btn_logout.pack(side=tk.RIGHT)
        show_sample_banner(self.root)

        # TABS TỔNG
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[15, 10])

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text=" 1. Phổ Điểm 9 Môn ")
        self.notebook.add(self.tab2, text=" 2. Địa Lý & Khối Thi ")
        self.notebook.add(self.tab3, text=" 3. Đề Thi & Hệ Đào Tạo ")
        self.notebook.add(self.tab4, text=" 4. Thủ Khoa ")

        self.build_tab_1()
        self.build_tab_2()
        self.build_tab_3()
        self.build_tab_4()

    def create_btn(self, parent, text, command, bg_color="#34495e"):
        return tk.Button(parent, text=text, font=("Arial", 10, "bold"), bg=bg_color, fg="white",
                         activebackground="#2c3e50", activeforeground="white", cursor="hand2",
                         pady=8, relief=tk.RAISED, borderwidth=1, command=command)

    # =================================================================
    # CÔNG CỤ NHÚNG BIỂU ĐỒ VÀO BÊN TRONG CỬA SỔ HIỆN TẠI (KHÔNG MỞ POPUP)
    # =================================================================
    def show_in_frame(self, plot_func):
        """Ẩn menu điều khiển, nhúng hình ảnh Matplotlib vào thẳng giao diện Tkinter"""
        self.notebook.pack_forget() # Giấu các Tabs đi

        self.chart_frame = tk.Frame(self.root)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # Nút Quay Lại cực to
        top_bar = tk.Frame(self.chart_frame, bg="#ecf0f1", pady=8)
        top_bar.pack(fill=tk.X)
        btn_back = tk.Button(top_bar, text="← QUAY LẠI BẢNG ĐIỀU KHIỂN CHÍNH", font=("Arial", 11, "bold"),
                             bg="#c0392b", fg="white", cursor="hand2", padx=20, command=self.close_chart)
        btn_back.pack(side=tk.LEFT, padx=15)

        # Bắt cóc plt.show() để vẽ vào Tkinter
        original_show = plt.show
        def embedded_show(*args, **kwargs):
            fig = plt.gcf()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        plt.show = embedded_show
        
        try:
            plot_func()
        except Exception as e:
            messagebox.showerror("Lỗi Biểu Đồ", f"Vui lòng kiểm tra lại data: {e}")
        finally:
            plt.show = original_show

    def close_chart(self):
        plt.close('all') # Dọn dẹp RAM
        self.chart_frame.destroy()
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=20, pady=15) # Hiện lại Tabs

    def run_and_notify(self, func, msg="Đã xuất báo cáo số liệu chi tiết ra màn hình Terminal thành công!"):
        """Hàm chạy các báo cáo chữ và hiện thông báo"""
        func()
        messagebox.showinfo("Hoàn Tất", msg)

    # =================================================================
    # XÂY DỰNG GIAO DIỆN 4 TABS
    # =================================================================
    def build_tab_1(self):
        frame = tk.Frame(self.tab1, padx=25, pady=15)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="1.PHỔ ĐIỂM & SỐ LIỆU", font=("Arial", 11, "bold"), fg="#1a5276").pack(anchor=tk.W, pady=(0, 6))
        f1 = tk.Frame(frame); f1.pack(fill=tk.X, pady=(0, 15)); f1.columnconfigure(0, weight=1); f1.columnconfigure(1, weight=1)

        self.create_btn(f1, "PHỔ ĐIỂM 9 MÔN", lambda: self.show_in_frame(da.plot_all_9_subjects_overview), "#8e44ad").grid(row=0, column=0, padx=5, sticky="ew")
        self.create_btn(f1, "TỔNG QUAN SỐ LIỆU 9 MÔN", self.show_overview_table, "#16a085").grid(row=0, column=1, padx=5, sticky="ew")

        tk.Label(frame, text="2. PHỔ ĐIỂM CHUYÊN SÂU TỪNG MÔN:", font=("Arial", 11, "bold"), fg="#c0392b").pack(anchor=tk.W, pady=(0, 8))
        grid = tk.Frame(frame); grid.pack(fill=tk.X); grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1); grid.columnconfigure(2, weight=1)
        
        self.create_btn(grid, "1. Môn Toán", lambda: self.show_in_frame(da.plot_toan), "#2980b9").grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "2. Môn Ngữ Văn", lambda: self.show_in_frame(da.plot_ngu_van), "#c0392b").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "3. Ngoại Ngữ", lambda: self.show_in_frame(da.plot_ngoai_ngu), "#16a085").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "4. Môn Vật Lý", lambda: self.show_in_frame(da.plot_vat_ly), "#d35400").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "5. Môn Hóa Học", lambda: self.show_in_frame(da.plot_hoa_hoc), "#27ae60").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "6. Môn Sinh Học", lambda: self.show_in_frame(da.plot_sinh_hoc), "#8e44ad").grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "7. Môn Lịch Sử", lambda: self.show_in_frame(da.plot_lich_su), "#7f8c8d").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "8. Môn Địa Lý", lambda: self.show_in_frame(da.plot_dia_ly), "#e67e22").grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "9. Môn GDCD", lambda: self.show_in_frame(da.plot_gdcd), "#f39c12").grid(row=2, column=2, padx=5, pady=5, sticky="ew")

    def build_tab_2(self):
        frame = tk.Frame(self.tab2, padx=25, pady=15)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="1. XẾP HẠNG CHUNG VÙNG MIỀN & KHỐI ĐẠI HỌC", font=("Arial", 11, "bold"), fg="#1a5276").pack(anchor=tk.W, pady=(0, 6))
        f1 = tk.Frame(frame); f1.pack(fill=tk.X, pady=(0, 15)); f1.columnconfigure(0, weight=1); f1.columnconfigure(1, weight=1)
        self.create_btn(f1, "ĐỊA LÝ: ĐIỂM TB & % ĐỖ", lambda: self.show_in_frame(lambda: da.analyze_group2_geography(30)), "#27ae60").grid(row=0, column=0, padx=5, sticky="ew")
        self.create_btn(f1, "PHỔ ĐIỂM 5 KHỐI ĐẠI HỌC (A00-D01)", lambda: self.show_in_frame(da.analyze_group3_admission_blocks), "#d35400").grid(row=0, column=1, padx=5, sticky="ew")

        tk.Label(frame, text="2. XẾP HẠNG ĐỊA PHƯƠNG THEO TỈNH THÀNH:", font=("Arial", 11, "bold"), fg="#c0392b").pack(anchor=tk.W, pady=(0, 8))
        grid = tk.Frame(frame); grid.pack(fill=tk.X); grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1); grid.columnconfigure(2, weight=1)

        self.create_btn(grid, "1. Top Tỉnh Toán", lambda: self.show_in_frame(da.rank_prov_toan), "#2980b9").grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "2. Top Tỉnh Văn", lambda: self.show_in_frame(da.rank_prov_ngu_van), "#c0392b").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "3. Top Ngoại Ngữ", lambda: self.show_in_frame(da.rank_prov_ngoai_ngu), "#16a085").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "4. Top Tỉnh Lý", lambda: self.show_in_frame(da.rank_prov_vat_ly), "#d35400").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "5. Top Tỉnh Hóa", lambda: self.show_in_frame(da.rank_prov_hoa_hoc), "#27ae60").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "6. Top Tỉnh Sinh", lambda: self.show_in_frame(da.rank_prov_sinh_hoc), "#8e44ad").grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "7. Top Tỉnh Sử", lambda: self.show_in_frame(da.rank_prov_lich_su), "#7f8c8d").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "8. Top Tỉnh Địa", lambda: self.show_in_frame(da.rank_prov_dia_ly), "#e67e22").grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.create_btn(grid, "9. Top Tỉnh GDCD", lambda: self.show_in_frame(da.rank_prov_gdcd), "#f39c12").grid(row=2, column=2, padx=5, pady=5, sticky="ew")

    def build_tab_3(self):
        frame = tk.Frame(self.tab3, padx=25, pady=15)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="1. ĐÁNH GIÁ ĐỀ THI", font=("Arial", 11, "bold"), fg="#1a5276").pack(anchor=tk.W, pady=(0, 4))
        f1 = tk.Frame(frame); f1.pack(fill=tk.X, pady=(0, 10)); f1.columnconfigure(0, weight=1); f1.columnconfigure(1, weight=1)
        self.create_btn(f1, "ĐÁNH GIÁ ĐỘ KHÓ & PHÂN HÓA", lambda: self.show_in_frame(da.analyze_group4_exam_evaluation), "#34495e").grid(row=0, column=0, padx=5, sticky="ew")
        self.create_btn(f1, "MA TRẬN TƯƠNG QUAN 9 MÔN", lambda: self.show_in_frame(da.plot_group4_correlation_matrix), "#8e44ad").grid(row=0, column=1, padx=5, sticky="ew")

        tk.Label(frame, text="2. ĐỐI TƯỢNG DỰ THI & HỆ ĐÀO TẠO", font=("Arial", 11, "bold"), fg="#c0392b").pack(anchor=tk.W, pady=(0, 4))
        f2 = tk.Frame(frame); f2.pack(fill=tk.X, pady=(0, 10)); f2.columnconfigure(0, weight=1); f2.columnconfigure(1, weight=1)
        self.create_btn(f2, "LỚP 12 vs TỰ DO", lambda: self.show_in_frame(da.plot_group5_target_comparison_dashboard), "#2980b9").grid(row=0, column=0, padx=5, sticky="ew")
        self.create_btn(f2, "HỆ GDPT vs GDTX", lambda: self.show_in_frame(da.plot_group5_education_system_dashboard), "#27ae60").grid(row=0, column=1, padx=5, sticky="ew")

        tk.Label(frame, text="3. CHÍNH SÁCH ƯU TIÊN & TRƯỢT TỐT NGHIỆP", font=("Arial", 11, "bold"), fg="#1a5276").pack(anchor=tk.W, pady=(0, 4))
        f3 = tk.Frame(frame); f3.pack(fill=tk.X); f3.columnconfigure(0, weight=1); f3.columnconfigure(1, weight=1)
        self.create_btn(f3, "NGUYÊN NHÂN TRƯỢT: LIỆT vs TB THẤP", lambda: self.show_in_frame(da.analyze_group6_policies_and_failures), "#c0392b").grid(row=0, column=0, padx=5, sticky="ew")
        self.create_btn(f3, "TÁC ĐỘNG CỨU RỖI ĐIỂM ƯU TIÊN", lambda: self.show_in_frame(da.analyze_group6_policies_and_failures), "#e67e22").grid(row=0, column=1, padx=5, sticky="ew")

    def build_tab_4(self):
        frame = tk.Frame(self.tab4, padx=25, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)
        tk.Label(frame, text="TẦNG 2: PHÂN TÍCH CHUYÊN SÂU, XÃ HỘI HỌC & HÀNH VI", font=("Arial", 12, "bold"), fg="#1a5276").pack(anchor=tk.W, pady=(0, 15))

        self.create_btn(frame, "GIỚI TÍNH: % ĐỖ NAM vs NỮ",
                        lambda: self.show_in_frame(da.analyze_group7_gender_dashboard), "#2980b9").pack(fill=tk.X, pady=8, ipady=3)
        self.create_btn(frame, "XU HƯỚNG: TOP COMBO 'HOT' & CHIẾN LƯỢC",
                        lambda: self.show_in_frame(da.analyze_group8_electives_dashboard), "#d35400").pack(fill=tk.X, pady=8, ipady=3)
        self.create_btn(frame, "THỦ KHOA: TOP ĐIỂM CAO, 5 KHỐI",
                        lambda: self.show_in_frame(da.analyze_group9_valedictorians_dashboard), "#27ae60").pack(fill=tk.X, pady=8, ipady=3)

    def handle_logout(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?"):
            if self.on_logout: self.on_logout()

    def show_overview_table(self):
        from controllers.data_analysis import analyze_group1_descriptive_stats
        import tkinter as tk
        from tkinter import ttk, messagebox

        # 1. Lấy dữ liệu từ Pandas
        df = analyze_group1_descriptive_stats()
        if df is None or len(df) == 0:
            messagebox.showerror("Lỗi", "Bảng dữ liệu trống!")
            return

        # 2. Xóa giao diện cũ, tạo Khung chứa bảng
        self.notebook.pack_forget()
        self.chart_frame = tk.Frame(self.root, bg="#f4f6f7")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # 3. Nút Quay Lại & Tiêu đề
        top_bar = tk.Frame(self.chart_frame, bg="#ecf0f1", pady=10)
        top_bar.pack(fill=tk.X)
        btn_back = tk.Button(top_bar, text="← QUAY LẠI BẢNG ĐIỀU KHIỂN CHÍNH", font=("Arial", 11, "bold"),
                             bg="#c0392b", fg="white", cursor="hand2", padx=20, pady=5, command=self.close_chart)
        btn_back.pack(side=tk.LEFT, padx=20)

        tk.Label(self.chart_frame, text="BẢNG TỔNG HỢP 12 CHỈ TIÊU KHOA HỌC - 9 MÔN THI THPT QUỐC GIA 2025",
                 font=("Arial", 14, "bold"), bg="#1a5276", fg="white", pady=10).pack(fill=tk.X)

        # 4. Tạo bộ khung cho Bảng Lưới (Treeview)
        table_frame = tk.Frame(self.chart_frame, padx=15, pady=15, bg="#f4f6f7")
        table_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

        columns = list(df.columns)
        tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.config(command=tree.yview)
        scroll_x.config(command=tree.xview)

        # Cấu hình Bảng (ĐÃ XÓA TOÀN BỘ TAG TÔ MÀU SỌC ĐỂ TRÁNH LỖI TÀNG HÌNH CỦA WINDOWS)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), foreground="black")
        style.configure("Treeview", font=("Arial", 10), rowheight=30, foreground="black")

        for col in columns:
            tree.heading(col, text=col.upper())
            width = 130 if col == "Môn thi" else 95
            tree.column(col, width=width, anchor=tk.CENTER)

        # 5. ĐỔ DỮ LIỆU (Cách nguyên thủy và an toàn tuyệt đối nhất)
        for index, row in df.iterrows():
            # Bước này ép cứng mọi giá trị Toán/Văn thành CHUỖI VĂN BẢN (String)
            safe_values = [str(x) for x in row.values]

            # Đưa dữ liệu thẳng vào bảng, KHÔNG dùng tag tô màu nữa
            tree.insert("", "end", values=safe_values)

        # Hiển thị lên màn hình
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    dummy_admin = {"role": "ADMIN", "username": "admin", "full_name": "Quản Trị Viên Hệ Thống"}
    app = AdminDashboard(root, admin_info=dummy_admin)
    root.mainloop()
