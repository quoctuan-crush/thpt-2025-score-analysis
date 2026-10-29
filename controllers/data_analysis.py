import sys
import os
# Thêm thư mục lớn (thư mục gốc của dự án) vào hệ thống để có thể import các module nội bộ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Cấu hình backend TkAgg để hiển thị cửa sổ biểu đồ (giao diện đồ họa) ổn định hơn
import matplotlib
matplotlib.use('TkAgg')
 
 # Import các thư viện phân tích dữ liệu và trực quan hóa chuyên dụng
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
# Import hàm kết nối cơ sở dữ liệu từ cấu trúc thư mục nội bộ của dự án
from database.db_connection import get_engine

# =====================================================================
# CẤU HÌNH GIAO DIỆN BIỂU ĐỒ CHUẨN KHOA HỌC & FONT TIẾNG VIỆT
# =====================================================================
# Ưu tiên các font hỗ trợ tốt hiển thị tiếng Việt không bị lỗi ô vuông
plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans', 'Times New Roman']
# Đảm bảo dấu trừ (-) trên trục tọa độ hiển thị đúng chuẩn, không bị lỗi font
plt.rcParams['axes.unicode_minus'] = False
# Thiết lập nền lưới trắng (whitegrid) và tone màu nhẹ nhàng (muted) cho biểu đồ chuẩn bộ nhận diện
sns.set_theme(style="whitegrid", palette="muted")

# Biến toàn cục dùng để lưu trữ dữ liệu tạm thời, tránh việc đọc/tải lại dữ liệu nhiều lần gây tốn hiệu năng
_CACHED_DF = None

def get_all_data(force_reload=False):
    """Nạp 1 triệu dòng vào RAM 1 lần duy nhất, chuẩn hóa và tính toán sẵn các trường phái sinh."""
    global _CACHED_DF
    # KIỂM TRA BỘ NHỚ ĐỆM (CACHE)
    # Nếu chưa có dữ liệu HOẶC ép buộc tải lại (force_reload=True) thì mới chạy tiếp
    if _CACHED_DF is None or force_reload:
        print("[SYSTEM] Đang nạp bộ nhớ đệm 1.000.000 thí sinh vào RAM...")
        # KẾT NỐI DATABASE
        engine = get_engine()
        if not engine:
            return pd.DataFrame()# Trả về bảng rỗng nếu mất kết nối
            
        try:
            # ĐỌC DỮ LIỆU THÔ
            df = pd.read_sql("SELECT * FROM students", con=engine)
            if df.empty:
                return pd.DataFrame()

            # CHUẨN HÓA TÊN CỘT: Viết thường + xóa khoảng trắng thừa ở 2 đầu    
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # CHUẨN HÓA ĐIỂM SỐ: Ép các cột điểm về dạng số
            score_cols = ['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2', 'diem_trung_binh', 'diem_uu_tien', 'diem_khuyen_khich', 'tong_diem']
            for col in score_cols:
                if col in df.columns:
                # errors='coerce': Ô nào lỗi hoặc trống sẽ tự động biến thành NaN (tránh crash code)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # DANH SÁCH ĐỒNG BỘ TÊN MÔN HỌC
            # Gom tất cả các cách viết (viết hoa/thường/sai font) về 1 từ khóa chuẩn duy nhất
            mapping_mons = {
                'vat_ly': ['Vật lý', 'Vật lí', 'vat_ly'],
                'hoa_hoc': ['Hóa học', 'Hóa', 'hoa_hoc'],
                'sinh_hoc': ['Sinh học', 'Sinh', 'sinh_hoc'],
                'lich_su': ['Lịch sử', 'Sử', 'lich_su'],
                'dia_ly': ['Địa lý', 'Địa lí', 'Địa', 'dia_ly'],
                'ngoai_ngu': ['Ngoại ngữ', 'Tiếng Anh', 'ngoai_ngu'],
                'gdcd': ['GDCD', 'Giáo dục công dân', 'gdcd']
            }
           # ĐỒNG BỘ ĐIỂM MÔN TỰ CHỌN
           # Do thí sinh chọn môn khác nhau (Lý/Hóa/Sử/Địa...) lưu rải rác ở cột 1 và cột 2.
           # Vòng lặp này quét qua bảng mapping để nhặt đúng điểm về cột môn học tương ứng.
            for col_target, names in mapping_mons.items():
                # Kiểm tra xem tên môn ở cột tự chọn 1 và 2 có khớp với danh sách mapping không
                cond1 = df['mon_tu_chon_1'].astype(str).str.strip().isin(names)
                cond2 = df['mon_tu_chon_2'].astype(str).str.strip().isin(names)
                # Nếu khớp ở cột nào thì lấy điểm cột đó, ngược lại gán NaN (trống)
                df[col_target] = np.where(cond1, df['diem_tu_chon_1'], np.where(cond2, df['diem_tu_chon_2'], np.nan))

            # TÍNH ĐIỂM TRUNG BÌNH: Tính trung bình cộng của 4 môn chính  
            # Tính điểm trung bình cộng của 4 môn thi chính theo từng dòng (axis=1)             
            df['diem_tb_4_mon'] = df[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']].mean(axis=1)
            
            # TÍNH TỔNG ĐIỂM THEO CÁC KHỐI XÉT TUYỂN ĐẠI HỌC
        # Tự động cộng điểm 3 môn theo tổ hợp truyền thống để phục vụ phân tích phổ điểm
            df['A00'] = df['toan'] + df['vat_ly'] + df['hoa_hoc']
            df['A01'] = df['toan'] + df['vat_ly'] + df['ngoai_ngu']
            df['B00'] = df['toan'] + df['hoa_hoc'] + df['sinh_hoc']
            df['C00'] = df['ngu_van'] + df['lich_su'] + df['dia_ly']
            df['D01'] = df['toan'] + df['ngu_van'] + df['ngoai_ngu']
            
            # PHÂN LOẠI ĐỐI TƯỢNG THÍ SINH
        # Tách lấy 4 chữ số năm sinh từ chuỗi ngày sinh để phân loại học sinh 12 hay thí sinh tự do
            if 'ngay_sinh' in df.columns:
                nam_sinh = df['ngay_sinh'].astype(str).str.extract(r'(\d{4})').astype(float)
                df['doi_tuong_thi'] = np.where(nam_sinh >= 2007, 'Thí sinh Lớp 12', 'Thí sinh Tự do')
            else:
                df['doi_tuong_thi'] = 'Thí sinh Lớp 12'# Mặc định nếu không có cột ngày sinh

            # XỬ LÝ DỮ LIỆU KHUYẾT (IMPUTATION)
        # Điền giá trị mặc định phổ biến nhất vào các ô trống (NaN/rỗng) để tránh lệch biểu đồ    
            df['he_dao_tao'] = df['he_dao_tao'].fillna('GDPT').replace({'': 'GDPT'})
            df['khu_vuc_uu_tien'] = df['khu_vuc_uu_tien'].fillna('KV3').replace({'': 'KV3'})

            # CẬP NHẬT BỘ NHỚ ĐỆM (CACHE)
        # Lưu dữ liệu sạch đã xử lý xong vào RAM để các hàm sau gọi lại ngay lập tức
            _CACHED_DF = df
            print(f"[SYSTEM] Nạp thành công {len(_CACHED_DF):,} thí sinh vào RAM! Sẵn sàng phân tích Tầng 1!")
        except Exception as e:
            # XỬ LÝ NGOẠI LỆ (ERROR HANDLING)
        # Bắt các lỗi phát sinh trong quá trình xử lý với Pandas (sai tên cột, sai kiểu dữ liệu...)
            print(f"[ERROR] Lỗi xử lý dữ liệu Pandas: {e}")
            return pd.DataFrame()# Trả về DataFrame rỗng để chương trình không bị sập hoàn toàn
        finally:
            engine.dispose()

    # TRẢ KẾT QUẢ ĐẦU RA        
    return _CACHED_DF

# =====================================================================
# NHÓM 1: SUPER DASHBOARD PHỔ ĐIỂM & 12 CHỈ TIÊU CHI TIẾT TỪNG MÔN THI
# =====================================================================

def analyze_group1_descriptive_stats():
    """Xuất bảng thống kê tổng hợp 9 môn ra Terminal (Dành cho việc copy số liệu vào báo cáo Word/Excel)."""
    # LẤY DỮ LIỆU SẠCH: Gọi hàm nạp/lấy dữ liệu từ bộ nhớ đệm RAM
    df = get_all_data()
    if df.empty: return
    print("\nĐang xuất Bảng Thống Kê Mô Tả 12 Chỉ Tiêu Cho 9 Môn Thi...")
    
    # KHỞI TẠO DANH SÁCH MÔN THI: Cặp giá trị (tên_cột_dataframe, tên_hiển_thị)
    subjects = [('toan', 'Toán'), ('ngu_van', 'Ngữ Văn'), ('vat_ly', 'Vật Lý'),
                ('hoa_hoc', 'Hóa Học'), ('sinh_hoc', 'Sinh Học'), ('lich_su', 'Lịch Sử'),
                ('dia_ly', 'Địa Lý'), ('ngoai_ngu', 'Ngoại Ngữ'), ('gdcd', 'GDCD')]
    stats_list = []
    # VÒNG LẶP TÍNH TOÁN: Duyệt qua từng môn để tính toán các chỉ số thống kê mô tả
    for col, name in subjects:
        if col not in df.columns: continue
        # Loại bỏ các giá trị trống (NaN) của môn đó để tính toán chính xác
        s = df[col].dropna()
        if len(s) == 0: continue
        # THỐNG KÊ CHI TIẾT: Lưu 12 chỉ tiêu định lượng và định tính vào danh sách
        stats_list.append({
            "Môn thi": name.upper(), "Số thí sinh": f"{len(s):,}", # Tổng số lượng thí sinh dự thi môn này
            "Điểm TB": round(s.mean(), 2), "Trung vị": round(s.median(), 2),
            # Các chỉ số xu hướng trung tâm & độ phân tán (Trung bình, Trung vị, Yếu vị, Độ lệch chuẩn)
            "Mode": round(s.mode().iloc[0], 2) if not s.mode().empty else 0, 
            # Khoảng điểm cực trị (Thấp nhất - Cao nhất) và số lượng điểm đặc biệt
            "Độ lệch (Std)": round(s.std(), 2), "Min - Max": f"{s.min()} - {s.max()}", 
            "Điểm 10": f"{(s == 10).sum():,}", "Điểm liệt (≤1)": f"{(s <= 1.0).sum():,}",
            # Phân loại học lực dựa trên tỷ lệ phần trăm (%) tổng số thí sinh môn đó 
            "Yếu (<5)": f"{round((s < 5).mean()*100, 1)}%", "TB (5-7)": f"{round(((s >= 5) & (s < 7)).mean()*100, 1)}%",
            "Khá (7-8)": f"{round(((s >= 7) & (s < 8)).mean()*100, 1)}%", "Giỏi (≥8)": f"{round((s >= 8).mean()*100, 1)}%"
        })
        # Gán danh sách kết quả thống kê vào DataFrame
    df_res = pd.DataFrame(stats_list)
    # In khoảng trống và đường kẻ phân tách để giao diện Terminal đẹp hơn
    print("\n" + "="*140)
    # Tiêu đề bảng thống kê chỉ tiêu 9 môn thi THPT Quốc gia 2025
    print("BẢNG TỔNG HỢP 12 CHỈ TIÊU KHOA HỌC - 9 MÔN THI THPT QUỐC GIA 2025")
    print("="*140)
    # Chuyển DataFrame thành dạng chuỗi và in ra, ẩn cột chỉ số (index) mặc định
    print(df_res.to_string(index=False))
    print("="*140 + "\n")
    return df_res
def plot_all_9_subjects_overview():
    """Vẽ toàn cảnh Phổ điểm đường cong KDE của cả 9 môn trên cùng 1 màn hình (3x3 Grid)."""
    # Lấy toàn bộ dữ liệu sạch
    df = get_all_data()
    if df.empty: return
    
    # Danh sách các môn học kèm theo nhãn hiển thị và mã màu Hex tương ứng để vẽ biểu đồ
    subjects = [('toan', 'Toán', '#1f77b4'), ('ngu_van', 'Ngữ Văn', '#c0392b'), ('vat_ly', 'Vật Lý', '#e67e22'),
                ('hoa_hoc', 'Hóa Học', '#27ae60'), ('sinh_hoc', 'Sinh Học', '#8e44ad'), ('lich_su', 'Lịch Sử', '#7f8c8d'),
                ('dia_ly', 'Địa Lý', '#16a085'), ('ngoai_ngu', 'Ngoại Ngữ', '#2980b9'), ('gdcd', 'GDCD', '#f39c12')]
    
    # Khởi tạo khung hình matplotlib kích thước 16x9 inch với lưới ô vuông 3 hàng 3 cột
    fig, axes = plt.subplots(3, 3, figsize=(16, 9))
    # Phẳng hóa ma trận axes 2 chiều thành mảng 1 chiều để dễ dàng lặp qua 9 ô
    axes = axes.flatten()
    
    # Duyệt qua từng môn học để vẽ biểu đồ điểm số
    for idx, (col, name, color) in enumerate(subjects):
        if col in df.columns:
            # Loại bỏ các giá trị rỗng (NaN) của môn hiện tại
            s = df[col].dropna()
            # Vẽ biểu đồ cột (Histogram) kết hợp đường cong mật độ (KDE) bằng Seaborn
            sns.histplot(s, bins=30, kde=True, ax=axes[idx], color=color, stat="count", edgecolor='white', alpha=0.6)
            # Thêm đường thẳng đứng màu đỏ đứt nét thể hiện giá trị Điểm Trung Bình (Mean)
            axes[idx].axvline(s.mean(), color='red', linestyle='--', linewidth=1.5, label=f'TB: {s.mean():.2f}')
            # Thiết lập tiêu đề cho từng đồ thị con (Tên môn in hoa, chữ đậm)
            axes[idx].set_title(f"MÔN {name.upper()}", fontweight='bold', fontsize=11, color='#2c3e50')
            axes[idx].set_xlabel(""); axes[idx].set_ylabel("") # Ẩn nhãn trục X và Y mặc định
            axes[idx].set_xlim(0, 10) # Giới hạn thang điểm trục X từ 0 đến 10
            axes[idx].legend(loc="upper right", fontsize=8) # Hiển thị chú thích ở góc trên bên phải

    # Đặt tiêu đề chung cho toàn bộ biểu đồ 9 môn        
    plt.suptitle("TOÀN CẢNH PHỔ ĐIỂM 9 MÔN THI THPT QUỐC GIA 2025", fontsize=16, fontweight='bold', color='#1a5276', y=0.98)
    # Tự động căn chỉnh các khoảng trống giữa các đồ thị con để không bị đè chữ
    plt.tight_layout()
    # Hiển thị cửa sổ biểu đồ lên màn hình
    plt.show()

def _plot_super_subject_dashboard(subject_col, subject_name, color_theme="#1f77b4"):
    """
    SUPER DASHBOARD: Hiển thị 2 biểu đồ + Bảng số liệu đồ họa 12 chỉ tiêu ngay trên giao diện Matplotlib!
    """
    # Gọi hàm lấy toàn bộ dữ liệu từ database/hệ thống
    df = get_all_data()
    # Kiểm tra điều kiện: Nếu DataFrame rỗng hoặc tên cột môn học không có trong df thì thoát
    if df.empty or subject_col not in df.columns: return
    # Lọc lấy cột điểm của môn tương ứng và loại bỏ các giá trị rỗng (NaN)
    s = df[subject_col].dropna()
    # Nếu sau khi lọc bỏ NaN mà không có dữ liệu điểm nào thì thoát
    if s.empty: return

    # 1. Tính toán chuẩn 12 chỉ tiêu khoa học 
    total_hs = len(s) # Tổng số lượng học sinh dự thi môn này
    mean_val = s.mean() # Điểm số trung bình (Mean)
    median_val = s.median() # Điểm trung vị (Mốc chính giữa danh sách điểm)
    mode_val = s.mode().iloc[0] if not s.mode().empty else 0 # Điểm số có nhiều thí sinh đạt được nhất
    std_val = s.std() # Độ lệch chuẩn (Đo mức độ phân tán của phổ điểm)
    min_val, max_val = s.min(), s.max() # Điểm số thấp nhất và điểm số cao nhất
    d10_count = (s == 10).sum() # Tổng số thí sinh đạt điểm tuyệt đối (Điểm 10)
    liet_count = (s <= 1.0).sum() # Tổng số thí sinh bị điểm liệt (Từ 1.0 trở xuống)
    
    # Tính toán tỷ lệ phần trăm các mức học lực dựa trên điểm số (Tính theo %):
    yeu_pct = (s < 5.0).mean() * 100 # Tỷ lệ phần trăm điểm Yếu / Dưới trung bình (< 5.0)
    tb_pct = ((s >= 5.0) & (s < 7.0)).mean() * 100 # Tỷ lệ phần trăm điểm Trung bình (Từ 5.0 đến dưới 7.0)
    kha_pct = ((s >= 7.0) & (s < 8.0)).mean() * 100 # Tỷ lệ phần trăm điểm Khá (Từ 7.0 đến dưới 8.0)
    gioi_pct = ((s >= 8.0) & (s < 9.0)).mean() * 100 # Tỷ lệ phần trăm điểm Giỏi (Từ 8.0 đến dưới 9.0)
    xs_pct = (s >= 9.0).mean() * 100 # Tỷ lệ điểm Xuất sắc (>= 9.0)

    # 2. Cấu hình khung hình lớn (GridSpec: 2 hàng, hàng dưới hiển thị Bảng số liệu)
    fig = plt.figure(figsize=(16, 9.5))
    # Chia khung lưới thành 2 hàng, 2 cột (Hàng dưới gộp dòng để hiện bảng số liệu)
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
    
    # Định nghĩa vị trí các biểu đồ con và bảng số liệu
    ax1 = fig.add_subplot(gs[0, 0]) # Phổ điểm KDE
    ax2 = fig.add_subplot(gs[0, 1]) # 10 Khoảng điểm
    ax_table = fig.add_subplot(gs[1, :]) # Bảng số liệu bao trọn hàng dưới
    ax_table.axis('off') # Ẩn trục tọa độ của bảng

    # -----------------------------------------------------------------
    # BIỂU ĐỒ TRÁI: PHỔ ĐIỂM ĐƯỜNG CONG MẬT ĐỘ (KDE)
    # -----------------------------------------------------------------
    # Vẽ biểu đồ cột histogram kèm đường cong mật độ KDE bằng Seaborn
    sns.histplot(s, bins=40, kde=True, ax=ax1, color=color_theme, stat="count", edgecolor='white', alpha=0.65)
    # Vẽ các đường thẳng đứng chỉ định mốc Điểm Trung Bình và Điểm Trung Vị
    ax1.axvline(mean_val, color='#c0392b', linestyle='--', linewidth=2.5, label=f'Điểm Trung Bình: {mean_val:.2f}')
    ax1.axvline(median_val, color='#27ae60', linestyle='-', linewidth=2, label=f'Điểm Trung Vị: {median_val:.2f}')
    # Tô màu nền một vùng (từ 0 đến 1.0 điểm) để cảnh báo vùng Điểm Liệt
    ax1.axvspan(0, 1.0, color='#e74c3c', alpha=0.15, label='Vùng Điểm Liệt (0 - 1đ)')
    
    # Cấu hình tiêu đề, nhãn trục và giới hạn của biểu đồ bên trái
    ax1.set_title(f'PHỔ ĐIỂM CHI TIẾT & ĐƯỜNG MẬT ĐỘ - {subject_name.upper()}', fontweight='bold', fontsize=13, color='#2c3e50')
    ax1.set_xlabel("Thang điểm thi (0 - 10)", fontweight='bold', fontsize=10)
    ax1.set_ylabel("Số lượng thí sinh", fontweight='bold', fontsize=10)
    ax1.set_xlim(0, 10)
    # Hiển thị bảng chú thích ở góc trên bên phải biểu đồ
    ax1.legend(loc="upper right", frameon=True, facecolor='white', edgecolor='#bdc3c7', fontsize=9)

    # -----------------------------------------------------------------
    # BIỂU ĐỒ PHẢI: PHÂN BỐ HỌC LỰC 10 KHOẢNG ĐIỂM
    # -----------------------------------------------------------------
    # Chia điểm số thành 10 khoảng từ 0 đến 10 kèm nhãn phân loại học lực
    bins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    labels = ['0-1\n(Liệt)', '1-2', '2-3', '3-4', '4-5\n(Yếu)', '5-6\n(TB)', '6-7', '7-8\n(Khá)', '8-9\n(Giỏi)', '9-10\n(X.Sắc)']
    # Đếm số lượng thí sinh rơi vào từng khoảng điểm
    counts = pd.cut(s, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()
    
    # Định nghĩa bảng màu sắc riêng cho từng cột học lực và vẽ biểu đồ cột (Barplot)
    palette_colors = ['#d62728', '#ff7f0e', '#ffbb78', '#ffbb78', '#ffbb78', '#2ca02c', '#2ca02c', '#1f77b4', '#1f77b4', '#9467bd']
    sns.barplot(x=counts.index, y=counts.values, ax=ax2, palette=palette_colors, edgecolor='black', linewidth=0.8)
    
    # Cấu hình tiêu đề và nhãn trục cho biểu đồ khoảng điểm
    ax2.set_title(f'PHÂN BỐ 10 KHOẢNG ĐIỂM HỌC LỰC - {subject_name.upper()}', fontweight='bold', fontsize=13, color='#2c3e50')
    ax2.set_xlabel("Khoảng điểm thi & Phân loại học lực", fontweight='bold', fontsize=10)
    ax2.set_ylabel("Số lượng thí sinh", fontweight='bold', fontsize=10)
    
    # Vòng lặp tính toán và hiển thị số lượng + tỷ lệ % trực tiếp trên đầu mỗi cột biểu đồ
    for p in ax2.patches:
        h = p.get_height()
        if h > 0:
            pct = (h / total_hs) * 100 # Tính tỷ lệ phần trăm tương ứng của cột
            # Hiển thị text dạng: "Số lượng \n (Tỷ lệ %)"
            ax2.annotate(f'{int(h):,}\n({pct:.1f}%)', (p.get_x() + p.get_width() / 2., h),
                         ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50', xytext=(0, 3), textcoords='offset points')
    # Giới hạn trục Y cao hơn cột cao nhất 20% để không bị che khuất chữ trên đầu cột
    ax2.set_ylim(0, counts.max() * 1.2)

    # -----------------------------------------------------------------
    # BẢNG SỐ LIỆU ĐỒ HỌA TRÊN MÀN HÌNH (12 CHỈ TIÊU KHOA HỌC)
    # -----------------------------------------------------------------
    # Chuẩn bị mảng 2 chiều chứa các cặp nhãn thông số và giá trị đã tính toán để vẽ bảng
    table_data = [
        ["Tổng thí sinh dự thi:", f"{total_hs:,} HS", "Điểm cao nhất (Max):", f"{max_val} điểm", "Học lực Yếu (< 5.0):", f"{yeu_pct:.2f}%"],
        ["Điểm Trung Bình (Mean):", f"{mean_val:.2f} điểm", "Điểm thấp nhất (Min):", f"{min_val} điểm", "Học lực TB (5.0 - 6.9):", f"{tb_pct:.2f}%"],
        ["Điểm Trung Vị (Median):", f"{median_val:.2f} điểm", "Số lượng Điểm 10:", f"{d10_count:,} HS", "Học lực Khá (7.0 - 7.9):", f"{kha_pct:.2f}%"],
        ["Điểm Phổ Biến (Mode):", f"{mode_val:.2f} điểm", "Số lượng Điểm Liệt (≤1):", f"{liet_count:,} HS", "Học lực Giỏi (8.0 - 8.9):", f"{gioi_pct:.2f}%"],
        ["Độ Lệch Chuẩn (Std Dev):", f"{std_val:.2f}", "Tỷ lệ đỗ Yêu cầu (≥5đ):", f"{(100 - yeu_pct):.2f}%", "Học lực Xuất Sắc (≥ 9.0):", f"{xs_pct:.2f}%"]
    ]
    
    col_widths = [0.18, 0.15, 0.18, 0.15, 0.18, 0.16] # Độ rộng từng cột
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths) 
    table.auto_set_font_size(False) # Tắt tự động chỉnh cỡ chữ
    table.set_fontsize(10) # Đặt cỡ chữ cố định là 10
    table.scale(1, 1.6) # Tăng chiều cao hàng cho thoáng
    
    # Trang trí màu sắc cho bảng số liệu
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7') # Đổi màu viền bảng thành xám nhạt
        if col in [0, 2, 4]: # Các cột tiêu đề
            cell.set_facecolor('#ecf0f1') # Nền xám xanh nhạt
            cell.set_text_props(weight='bold', color='#2c3e50') # Chữ đậm, màu tối
        else: # Các cột chứa con số
            cell.set_facecolor('#ffffff')
            # Chữ đậm, tự động đổi màu chữ theo từng cột để dễ nhìn
            cell.set_text_props(weight='bold', color='#16a085' if col==1 else ('#c0392b' if col==3 else '#2980b9'))
 
 # Thiết lập tiêu đề tổng cho Dashboard
    plt.suptitle(f"BẢNG ĐIỀU KHIỂN PHÂN TÍCH CHUYÊN SÂU MÔN {subject_name.upper()} - THPT QUỐC GIA 2025", 
                 fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show() # Hiển thị biểu đồ hoàn chỉnh

# --- 9 HÀM GỌI RIÊNG BIỆT CHO 9 MÔN (Dùng Super Dashboard mới) ---
def plot_toan(): _plot_super_subject_dashboard("toan", "Môn Toán", "#1f77b4")
def plot_ngu_van(): _plot_super_subject_dashboard("ngu_van", "Môn Ngữ Văn", "#c0392b")
def plot_vat_ly(): _plot_super_subject_dashboard("vat_ly", "Môn Vật Lý", "#e67e22")
def plot_hoa_hoc(): _plot_super_subject_dashboard("hoa_hoc", "Môn Hóa Học", "#27ae60")
def plot_sinh_hoc(): _plot_super_subject_dashboard("sinh_hoc", "Môn Sinh Học", "#8e44ad")
def plot_lich_su(): _plot_super_subject_dashboard("lich_su", "Môn Lịch Sử", "#7f8c8d")
def plot_dia_ly(): _plot_super_subject_dashboard("dia_ly", "Môn Địa Lý", "#16a085")
def plot_ngoai_ngu(): _plot_super_subject_dashboard("ngoai_ngu", "Môn Ngoại Ngữ", "#2980b9")
def plot_gdcd(): _plot_super_subject_dashboard("gdcd", "Môn GDCD", "#f39c12")
# =====================================================================
# NHÓM 2: PHÂN TÍCH ĐỊA LÝ & VÙNG MIỀN (CHỈ TIÊU 13, 14, 15 - CHI TIẾT)
# =====================================================================

def analyze_group2_geography(top_n=30):
    """
    SUPER DASHBOARD ĐỊA LÝ: Kết hợp Chỉ tiêu 13 (Xếp hạng Điểm TB) & Chỉ tiêu 15 (Tỷ lệ đỗ)
    kèm Bảng số liệu tổng hợp các tỉnh thành trên cùng 1 màn hình lớn!
    """
    df = get_all_data() # Lấy toàn bộ dữ liệu sạch
    # Kiểm tra tính hợp lệ: Nếu dữ liệu trống hoặc thiếu cột tỉnh thành thì thoát hàm
    if df.empty or 'tinh_thanh' not in df.columns: return
    print(f"\nĐang tổng hợp số liệu chất lượng giáo dục của các Tỉnh/Thành phố...")

    # 1. Tổng hợp dữ liệu theo từng tỉnh
    # Gom nhóm theo tỉnh và tính toán các chỉ số thống kê trung bình
    prov = df.groupby('tinh_thanh').agg(
        tong_hs=('sbd', 'count'), # Tổng số thí sinh của tỉnh (đếm số SBD)
        tb_4_mon=('diem_tb_4_mon', 'mean'), # Điểm trung bình cả 4 môn thi
        tb_toan=('toan', 'mean'), # Điểm trung bình môn Toán
        tb_van=('ngu_van', 'mean'), # Điểm trung bình môn Văn
        # Tính tỷ lệ % thí sinh đạt trạng thái 'đỗ tốt nghiệp'
        ty_le_do=('trang_thai', lambda x: (x.astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100)
    ).reset_index() # Chuyển cột gom nhóm 'tinh_thanh' quay lại thành một cột dữ liệu thông thường

    # Lọc bỏ các hội đồng có dưới 50 thí sinh (dữ liệu nhiễu)
    prov_valid = prov[prov['tong_hs'] > 50].copy()

    # 2. In bảng số liệu ra Terminal (Để copy vào báo cáo)
    prov_print = prov_valid.sort_values(by='tb_4_mon', ascending=False).copy()
    # Làm tròn số liệu hiển thị
    prov_print['tb_4_mon'] = prov_print['tb_4_mon'].round(2)
    prov_print['tb_toan'] = prov_print['tb_toan'].round(2)
    prov_print['tb_van'] = prov_print['tb_van'].round(2)
    prov_print['ty_le_do'] = prov_print['ty_le_do'].round(1).astype(str) + "%" # Thêm ký tự %
    prov_print['tong_hs'] = prov_print['tong_hs'].apply(lambda x: f"{x:,}") # Định dạng dấu phẩy 

    # In tiêu đề bảng ra giao diện Terminal
    print("\n" + "="*120)
    print("BẢNG XẾP HẠNG CHẤT LƯỢNG GIÁO DỤC TỈNH/THÀNH PHỐ - THPT QUỐC GIA 2025")
    print("="*120)
    # Đổi tên cột sang tiếng Việt trực quan và in toàn bộ bảng (ẩn index gốc)
    print(prov_print.rename(columns={
        'tinh_thanh': 'Tỉnh / Thành phố', 'tong_hs': 'Số Thí Sinh', 
        'tb_4_mon': 'Điểm TB 4 Môn', 'tb_toan': 'TB Toán', 'tb_van': 'TB Văn', 'ty_le_do': 'Tỷ Lệ Đỗ (%)'
    }).to_string(index=False))
    print("="*120 + "\n")

    # 3. Vẽ Super Dashboard (2 Biểu đồ + Bảng số liệu Top 5 & Bottom 3)
    fig = plt.figure(figsize=(16, 9.5))
    # Chia bố cục lưới: 2 hàng, 2 cột (Hàng dưới gộp dòng để làm bảng tóm tắt)
    gs = fig.add_gridspec(2, 2, height_ratios=[2.4, 1], hspace=0.35, wspace=0.25)

    # Định nghĩa các vùng vẽ đồ thị con
    ax1 = fig.add_subplot(gs[0, 0]) # Xếp hạng Điểm TB (Chỉ tiêu 13)
    ax2 = fig.add_subplot(gs[0, 1]) # Xếp hạng Tỷ lệ đỗ (Chỉ tiêu 15)
    ax_table = fig.add_subplot(gs[1, :]) # Bảng tóm tắt phía dưới
    ax_table.axis('off') # Ẩn hoàn toàn trục tọa độ của bảng

    # --- BIỂU ĐỒ TRÁI: TOP TỈNH ĐIỂM TB CAO NHẤT ---
    # Lấy ra top_n tỉnh có Điểm TB 4 môn cao nhất
    ranked_tb = prov_valid.sort_values(by='tb_4_mon', ascending=False).head(top_n)
    # Vẽ biểu đồ cột ngang bằng Seaborn (màu mako)
    sns.barplot(x='tb_4_mon', y='tinh_thanh', data=ranked_tb, ax=ax1, palette='mako', edgecolor='black', linewidth=0.7)
    # Cấu hình tiêu đề, nhãn trục và giới hạn thang điểm (0-10)
    ax1.set_title(f'TOP {top_n} TỈNH/THÀNH ĐIỂM TRUNG BÌNH CAO NHẤT [CHỈ TIÊU 13]', fontweight='bold', fontsize=12, color='#1a5276')
    ax1.set_xlabel("Điểm trung bình 4 môn thi", fontweight='bold', fontsize=10)
    ax1.set_ylabel("Tỉnh / Thành phố", fontweight='bold', fontsize=10)
    ax1.set_xlim(0, 10)
    
    # Kẻ đường trung bình toàn quốc
    nat_mean = df['diem_tb_4_mon'].mean()
    ax1.axvline(nat_mean, color='#c0392b', linestyle='--', linewidth=2, label=f'TB Toàn Quốc: {nat_mean:.2f}')
    ax1.legend(loc="lower right", frameon=True, facecolor='white')

    # Vòng lặp hiển thị giá trị số liệu cụ thể ở đầu mỗi thanh cột ngang
    for p in ax1.patches:
        w = p.get_width()
        if w > 0:
            ax1.annotate(f'{w:.2f}', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=8.5, fontweight='bold', xytext=(4, 0), textcoords='offset points')

    # --- BIỂU ĐỒ PHẢI: TOP TỈNH TỶ LỆ ĐỖ CAO NHẤT ---
    # Lấy ra top_n tỉnh có Tỷ lệ đỗ tốt nghiệp cao nhất
    ranked_do = prov_valid.sort_values(by='ty_le_do', ascending=False).head(top_n)
    # Vẽ biểu đồ cột ngang bằng Seaborn (màu rocket)
    sns.barplot(x='ty_le_do', y='tinh_thanh', data=ranked_do, ax=ax2, palette='rocket', edgecolor='black', linewidth=0.7)
    # Cấu hình tiêu đề, nhãn trục và giới hạn phần trăm (50% - 100% để biểu đồ rõ nét hơn)
    ax2.set_title(f'TOP {top_n} TỈNH/THÀNH TỶ LỆ ĐỖ TỐT NGHIỆP CAO NHẤT [CHỈ TIÊU 15]', fontweight='bold', fontsize=12, color='#922b21')
    ax2.set_xlabel("Tỷ lệ đỗ tốt nghiệp (%)", fontweight='bold', fontsize=10)
    ax2.set_ylabel("") # Ẩn nhãn trục Y vì dùng chung danh sách tỉnh với biểu đồ trái
    ax2.set_xlim(50, 106)
    
    # Kẻ đường thẳng đứt nét màu xanh hiển thị Tỷ Lệ Đỗ tốt nghiệp toàn quốc
    nat_do = (df['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
    ax2.axvline(nat_do, color='#27ae60', linestyle='--', linewidth=2, label=f'Đỗ Toàn Quốc: {nat_do:.1f}%')
    ax2.legend(loc="lower right", frameon=True, facecolor='white')

    # Vòng lặp hiển thị giá trị phần trăm cụ thể ở đầu mỗi thanh cột (biểu đồ phải)
    for p in ax2.patches:
        w = p.get_width()
        if w > 0:
            ax2.annotate(f'{w:.1f}%', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=8.5, fontweight='bold', xytext=(4, 0), textcoords='offset points')

    # --- BẢNG ĐỒ HỌA PHÍ DƯỚI: VINH DANH TOP 5 VÀ LƯU Ý BOTTOM 3 ---
    # Lấy ra 5 tỉnh có điểm cao nhất và 3 tỉnh có điểm thấp nhất
    top5 = prov_valid.sort_values(by='tb_4_mon', ascending=False).head(5)
    bot3 = prov_valid.sort_values(by='tb_4_mon', ascending=True).head(3)
    
    # Khởi tạo ma trận dữ liệu cho bảng và thêm hàng tiêu đề (Header)
    table_data = [
        ["Xếp Hạng", "Tỉnh / Thành Phố", "Số Thí Sinh", "Điểm TB 4 Môn", "Điểm TB Toán", "Điểm TB Văn", "Tỷ Lệ Đỗ (%)"]
    ]
    # Duyệt và thêm dữ liệu 5 tỉnh cao nhất vào bảng
    for idx, row in enumerate(top5.itertuples(), 1):
        table_data.append([f"Top {idx}", row.tinh_thanh, f"{row.tong_hs:,}", f"{row.tb_4_mon:.2f}", f"{row.tb_toan:.2f}", f"{row.tb_van:.2f}", f"{row.ty_le_do:.1f}%"])
        # Duyệt và thêm dữ liệu 3 tỉnh thấp nhất vào bảng (đảo ngược thứ tự để tỉnh thấp nhất xuống cuối)
    for idx, row in enumerate(bot3.iloc[::-1].itertuples(), 1):
        table_data.append([f"Thấp {idx}", row.tinh_thanh, f"{row.tong_hs:,}", f"{row.tb_4_mon:.2f}", f"{row.tb_toan:.2f}", f"{row.tb_van:.2f}", f"{row.ty_le_do:.1f}%"])

    col_widths = [0.12, 0.22, 0.13, 0.13, 0.13, 0.13, 0.14] # Tỷ lệ độ rộng các cột
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center', colWidths=col_widths)
    table.auto_set_font_size(False) # Tắt tự động chỉnh cỡ chữ
    table.set_fontsize(9.5) # Đặt cỡ chữ cố định là 9.5
    table.scale(1, 1.45) # Giãn khoảng cách chiều cao hàng (gấp 1.45 lần)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7') # Đổi màu viền bảng thành xám nhạt
        # Nếu là hàng tiêu đề (Hàng 0): Đổi màu nền tối, chữ trắng đậm
        if row == 0:
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(weight='bold', color='white')
            # Nếu là các hàng dữ liệu của nhóm Top 5: Đổ màu xen kẽ nhẹ nhàng để dễ nhìn
        elif row <= 5:
            cell.set_facecolor('#e8f8f5' if row%2==1 else '#d1f2eb')
            cell.set_text_props(weight='bold' if col in [0,1,3] else 'normal', color='#16a085' if col==3 else '#2c3e50')
        # Nếu là các hàng dữ liệu của nhóm Thấp 3 (Bottom 3)
        else:
            # Đổ màu đỏ/hồng xen kẽ để cảnh báo vùng điểm thấp
            cell.set_facecolor('#faded2' if row%2==1 else '#f5cba7')
            # Định dạng chữ đậm cho các cột chính, đổi màu chữ Điểm TB thành màu đỏ
            cell.set_text_props(weight='bold' if col in [0,1,3] else 'normal', color='#c0392b' if col==3 else '#2c3e50')

    # Thiết lập tiêu đề tổng cho Dashboard Địa lý và hiển thị biểu đồ
    plt.suptitle("BẢNG ĐIỀU KHIỂN PHÂN TÍCH CHẤT LƯỢNG GIÁO DỤC VÙNG MIỀN - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()


def _plot_ranking_by_single_subject(subject_col, subject_name, palette_theme="viridis", top_n=20):
    """
    Chỉ tiêu 14: Xếp hạng các địa phương theo TỪNG MÔN THI riêng biệt.
    Vẽ Top 20 tỉnh xuất sắc nhất, kẻ đường Trung bình toàn quốc.
    """
    df = get_all_data() # Lấy toàn bộ dữ liệu sạch
    # Kiểm tra điều kiện: Nếu dữ liệu trống hoặc thiếu cột môn học thì thoát hàm
    if df.empty or subject_col not in df.columns: return
    
    # Gom nhóm theo tỉnh/thành để tính Điểm TB ('mean') và Số lượng thí sinh ('count') của môn đó
    prov = df.groupby('tinh_thanh')[subject_col].agg(['mean', 'count']).reset_index()
    # Lọc bỏ các tỉnh có dưới 50 thí sinh dự thi môn này để tránh nhiễu
    prov_valid = prov[prov['count'] > 50].copy()
    # Sắp xếp giảm dần theo Điểm TB và lọc lấy ra top_n tỉnh dẫn đầu
    ranked = prov_valid.sort_values(by='mean', ascending=False).head(top_n)
    
    # Khởi tạo khung hình biểu đồ kích thước 14x8 inch
    plt.figure(figsize=(14, 8))
    # Vẽ biểu đồ cột ngang thể hiện điểm trung bình môn học của từng tỉnh
    bars = sns.barplot(x='mean', y='tinh_thanh', data=ranked, palette=palette_theme, edgecolor='black', linewidth=0.8)
    
    # Cấu hình tiêu đề, nhãn trục và giới hạn thang điểm (0-10) cho biểu đồ
    plt.title(f'TOP {top_n} TỈNH/THÀNH ĐIỂM TRUNG BÌNH {subject_name.upper()} CAO NHẤT [CHỈ TIÊU 14]', fontsize=14, fontweight='bold', color='#2c3e50', pad=15)
    plt.xlabel(f"Điểm trung bình {subject_name} (0 - 10)", fontweight='bold', fontsize=11)
    plt.ylabel("Tỉnh / Thành phố", fontweight='bold', fontsize=11)
    plt.xlim(0, 10)
    
    # Đường trung bình môn toàn quốc
    nat_sub_mean = df[subject_col].mean()
    plt.axvline(nat_sub_mean, color='red', linestyle='--', linewidth=2.5, label=f'TB {subject_name} Toàn Quốc: {nat_sub_mean:.2f}')
    plt.legend(loc="lower right", frameon=True, facecolor='white', edgecolor='#bdc3c7', fontsize=11)

    # Vòng lặp hiển thị giá trị số liệu ở đầu mỗi thanh cột ngang
    for p in bars.patches:
        w = p.get_width()
        if w > 0:
            plt.annotate(f'{w:.2f}', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50', xytext=(5, 0), textcoords='offset points')
            
    plt.tight_layout() # Tự động căn chỉnh khoảng cách
    plt.show() # Hiển thị biểu đồ

# --- 9 HÀM XẾP HẠNG TỈNH THÀNH THEO 9 MÔN THI (CHỈ TIÊU 14) ---
def rank_prov_toan(): _plot_ranking_by_single_subject("toan", "Môn Toán", "Blues_r")
def rank_prov_ngu_van(): _plot_ranking_by_single_subject("ngu_van", "Môn Ngữ Văn", "Reds_r")
def rank_prov_vat_ly(): _plot_ranking_by_single_subject("vat_ly", "Môn Vật Lý", "Oranges_r")
def rank_prov_hoa_hoc(): _plot_ranking_by_single_subject("hoa_hoc", "Môn Hóa Học", "Greens_r")
def rank_prov_sinh_hoc(): _plot_ranking_by_single_subject("sinh_hoc", "Môn Sinh Học", "Purples_r")
def rank_prov_lich_su(): _plot_ranking_by_single_subject("lich_su", "Môn Lịch Sử", "Greys_r")
def rank_prov_dia_ly(): _plot_ranking_by_single_subject("dia_ly", "Môn Địa Lý", "Teal_r" if 'Teal_r' in plt.colormaps() else "mako")
def rank_prov_ngoai_ngu(): _plot_ranking_by_single_subject("ngoai_ngu", "Môn Ngoại Ngữ", "crest")
def rank_prov_gdcd(): _plot_ranking_by_single_subject("gdcd", "Môn GDCD", "YlOrBr_r")
# =====================================================================
# NHÓM 3: KHỐI XÉT TUYỂN ĐẠI HỌC (CHỈ TIÊU 16 & 17 - CHI TIẾT SANG XỊN)
# =====================================================================

def analyze_group3_admission_blocks():
    """
    SUPER DASHBOARD KHỐI THI: So sánh toàn cảnh 5 khối A00, A01, B00, C00, D01
    (Biểu đồ Violin + Biểu đồ tỷ lệ ngưỡng điểm + Bảng số liệu Tổng hợp).
    """
    df = get_all_data() # Lấy toàn bộ dữ liệu sạch
    if df.empty: return # Nếu dữ liệu trống thì thoát hàm
    print("\nĐang phân tích dữ liệu 5 Tổ hợp xét tuyển Đại học truyền thống...")

    # Định nghĩa danh sách 5 khối thi và các môn thành phần tương ứng
    blocks = [
        ('A00', 'Toán - Lý - Hóa'), ('A01', 'Toán - Lý - Anh'),
        ('B00', 'Toán - Hóa - Sinh'), ('C00', 'Văn - Sử - Địa'),
        ('D01', 'Toán - Văn - Anh')
    ]
    # Lọc lại các khối thi thực sự có tồn tại cột điểm trong DataFrame
    valid_blocks = [(b, desc) for b, desc in blocks if b in df.columns]

    # 1. Tính toán số liệu thống kê cho bảng terminal & đồ họa
    stats_list = []
    # Duyệt qua từng khối thi hợp lệ để tính toán các chỉ số
    for b, desc in valid_blocks:
        s = df[b].dropna() # Loại bỏ các thí sinh không xét tuyển khối này (giá trị NaN)
        if len(s) == 0: continue # Nếu không có thí sinh nào thì bỏ qua
        # Thêm các thống kê chi tiết của khối thi vào danh sách
        stats_list.append({
            "Khối Thi": b, "Tổ Hợp Môn": desc, "Số Thí Sinh": len(s),
            "Điểm TB": s.mean(), "Trung Vị": s.median(),
            # Tính tỷ lệ phần trăm thí sinh đạt các ngưỡng điểm từ 15 đến 27 điểm
            "p15": (s >= 15.0).mean() * 100, "p20": (s >= 20.0).mean() * 100,
            "p24": (s >= 24.0).mean() * 100, "p27": (s >= 27.0).mean() * 100,
            "max_val": s.max() # Điểm số cao nhất của khối thi (Thủ khoa)
        })
    # Chuyển đổi danh sách kết quả thành một DataFrame để tiện xử lý và in ấn
    df_stats = pd.DataFrame(stats_list)
        # toàn toàn toa

    # In ra Terminal
    print("\n" + "="*130) # In đường kẻ ngang ngăn cách (130 dấu '=') 
    # In tiêu đề của bảng thống kê
    print(" BẢNG THỐNG KÊ CHUẨN QUỐC GIA - 5 TỔ HỢP XÉT TUYỂN ĐẠI HỌC TRUYỀN THỐNG 2025 (THANG 30 ĐIỂM)")
    print("="*130) # In thêm một đường kẻ ngang nữa
    df_print = df_stats.copy() # Tạo bản sao dữ liệu thống kê để không làm ảnh hưởng bản gốc
    # Thêm dấu phẩy phân cách hàng nghìn 
    df_print['Số Thí Sinh'] = df_print['Số Thí Sinh'].apply(lambda x: f"{x:,}") 
    # Làm tròn cột điểm trung bình và trung vị xuống 2 chữ số thập phân 
    for col in ['Điểm TB', 'Trung Vị']: df_print[col] = df_print[col].round(2)
    # Làm tròn tỷ lệ phần trăm (1 số thập phân) và thêm ký tự '%'
    for col in ['p15', 'p20', 'p24', 'p27']: df_print[col] = df_print[col].round(1).astype(str) + "%"
    # Đổi tên cột cho đẹp, sau đó in bảng ra, ẩn cột số thứ tự (index)
    print(df_print.rename(columns={'p15': '≥15đ (Sàn)', 'p20': '≥20đ (Khá)', 'p24': '≥24đ (Giỏi)', 'p27': '≥27đ (Top Cao)', 'max_val': 'Max'}).to_string(index=False))
    print("="*130 + "\n") # In đường kẻ kết thúc bảng

    # 2. Cấu hình Super Dashboard (GridSpec 2 hàng)
    fig = plt.figure(figsize=(16, 9.5)) # Tạo khung hình tổng với kích thước 16x9.5 
    # Chia khung làm lưới 2x2: Hàng 1 cao gấp 2.3 lần hàng 2, chỉnh khoảng cách giữa các biểu đồ
    gs = fig.add_gridspec(2, 2, height_ratios=[2.3, 1], hspace=0.35, wspace=0.2) 

    ax1 = fig.add_subplot(gs[0, 0]) # Tạo ô biểu đồ ở hàng 0, cột 0 (cho Violin plot)
    ax2 = fig.add_subplot(gs[0, 1]) # Tạo ô biểu đồ ở hàng 0, cột 1 (cho Bar chart)
    # Tạo ô biểu đồ kéo dài hết hàng 1 và # Tắt trục tọa độ (x, y) của ô này để nó trông như một bảng thuần túy
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off') 

    # --- BIỂU ĐỒ TRÁI: VIOLIN PLOT PHỔ ĐIỂM 5 KHỐI ---
    # Chuyển dữ liệu từ dạng bảng ngang sang dạng dọc để vẽ biểu đồ, loại bỏ dữ liệu trống
    melted = pd.melt(df, value_vars=[b for b, _ in valid_blocks], var_name='Khối thi', value_name='Tổng điểm').dropna()
    # Vẽ biểu đồ Violin trên ô ax1, dùng bảng màu Set2, hiển thị các vạch tứ phân vị bên trong
    sns.violinplot(x='Khối thi', y='Tổng điểm', data=melted, ax=ax1, palette='Set2', inner="quartile", linewidth=1.2)
    # Đặt tiêu đề cho biểu đồ, định dạng chữ đậm, kích thước 12, màu xanh
    ax1.set_title('[Chỉ tiêu 16] PHỔ ĐIỂM & ĐỘ PHÂN TÁN 5 KHỐI XÉT TUYỂN ĐẠI HỌC', fontweight='bold', fontsize=12, color='#1a5276')
    ax1.set_xlabel("Tổ hợp khối thi", fontweight='bold', fontsize=10) # Đặt tên trục ngang (x)
    ax1.set_ylabel("Tổng điểm 3 môn (0 - 30 điểm)", fontweight='bold', fontsize=10) # Đặt tên trục dọc (y)
    ax1.set_ylim(0, 31) # Giới hạn hiển thị trục y từ 0 đến 31 điểm

    # Kẻ các đường ngưỡng điểm quan trọng
    # Kẻ đường ngang tại mốc 24đ
    ax1.axhline(24.0, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, label='Ngüỡng Giỏi (24đ)')
    # Kẻ đường ngang tại mốc 27đ
    ax1.axhline(27.0, color='#e67e22', linestyle=':', linewidth=1.8, alpha=0.9, label='Ngưỡng Top Cao (27đ)')
    # Hiển thị bảng chú thích các đường ở góc dưới bên trái
    ax1.legend(loc="lower left", frameon=True, facecolor='white', fontsize=9)
    # Vòng lặp để ghi chú điểm trung bình cho từng khối
    for idx, row in df_stats.iterrows(): # Duyệt qua từng dòng dữ liệu trong bảng thống kê
        # Đặt chữ tại tọa độ (x=idx, y=29.2)
        ax1.text(idx, 29.2, f"TB: {row['Điểm TB']:.2f}đ", ha='center', va='center', 
                # Tạo hộp bao quanh chữ, màu nền vàng nhạt, viền vàng đậm , định dạng chữ đậm và kích thước 9        
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#fef9e7', edgecolor='#f1c40f'), fontweight='bold', fontsize=9)

    # --- BIỂU ĐỒ PHẢI: TỶ LỆ ĐẠT CÁC MỐC ĐIỂM XÉT TUYỂN ---
    # Chuyển dữ liệu từ dạng bảng ngang sang dọc, giữ lại cột 'Khối Thi' làm chuẩn
    df_thresh = pd.melt(df_stats, id_vars=['Khối Thi'], value_vars=['p20', 'p24', 'p27'], var_name='Mốc Điểm', value_name='Tỷ Lệ (%)')
    # Thay đổi tên mốc điểm trong dữ liệu thành chữ dễ đọc
    df_thresh['Mốc Điểm'] = df_thresh['Mốc Điểm'].replace({'p20': '≥ 20 điểm (Khá)', 'p24': '≥ 24 điểm (Giỏi)', 'p27': '≥ 27 điểm (Top ĐH Trọng điểm)'})
    # Vẽ biểu đồ cột trên ax2, dùng màu mako, phân nhóm theo 'Mốc Điểm'
    sns.barplot(x='Khối Thi', y='Tỷ Lệ (%)', hue='Mốc Điểm', data=df_thresh, ax=ax2, palette='mako', edgecolor='black', linewidth=0.7)
    # Đặt tiêu đề biểu đồ 
    ax2.set_title('[Chỉ tiêu 17] TỶ LỆ % THÍ SINH ĐẠT CÁC NGƯỠNG ĐIỂM CHUẨN ĐẠI HỌC', fontweight='bold', fontsize=12, color='#922b21')
    # Tên trục ngang và trục dọc
    ax2.set_xlabel("Tổ hợp khối thi", fontweight='bold', fontsize=10); ax2.set_ylabel("Tỷ lệ thí sinh đạt được (%)", fontweight='bold', fontsize=10)
    # Tạo bảng chú thích
    ax2.legend(title="Ngưỡng điểm xét tuyển", loc="upper right", frameon=True, facecolor='white', fontsize=9)

    for p in ax2.patches:
        h = p.get_height() # Lấy chiều cao của cột (đây chính là giá trị % cần hiển thị)
        # Cập nhật lại giới hạn trục Y để biểu đồ không bị "cụt" đầu do chữ nhãn quá cao
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=8, fontweight='bold', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, df_thresh['Tỷ Lệ (%)'].max() * 1.2)

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # Tạo bảng dữ liệu, dòng đầu tiên là tiêu đề các cột
    table_data = [["Khối Thi", "Tổ Hợp Môn Xét Tuyển", "Số Thí Sinh", "Điểm TB", "Trung Vị", "≥ 15đ (Sàn)", "≥ 20đ (Khá)", "≥ 24đ (Giỏi)", "≥ 27đ (Top Cao)"]]
    for _, r in df_stats.iterrows(): # Duyệt qua từng dòng 
        table_data.append([ # Thêm 1 dòng mới vào bảng, gồm các giá trị format sẵn
            # Cột Khối Thi, Tổ Hợp Môn (giữ nguyên), Số Thí Sinh (ép kiểu int + thêm dấu phẩy ngăn cách hàng nghìn)
            f"{r['Khối Thi']}", r['Tổ Hợp Môn'], f"{int(r['Số Thí Sinh']):,}", 
            # Điểm TB và Trung Vị: làm tròn 2 số thập phân
            f"{r['Điểm TB']:.2f}", f"{r['Trung Vị']:.2f}",
            # Các mốc phần trăm p15, p20, p24, p27: làm tròn 1 số thập phân + thêm ký hiệu %
            f"{r['p15']:.1f}%", f"{r['p20']:.1f}%", f"{r['p24']:.1f}%", f"{r['p27']:.2f}%"
        ])
    # Độ rộng của từng cột trong bảng
    col_widths = [0.09, 0.20, 0.12, 0.09, 0.09, 0.10, 0.10, 0.10, 0.11]
    # Tạo bảng từ dữ liệu table_data, căn giữa nội dung và bảng, áp độ rộng cột đã định nghĩa
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center', colWidths=col_widths)
    # Tắt tự động chỉnh cỡ chữ, đặt cỡ chữ = 10, phóng to bảng theo chiều cao 
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.55)

    for (row, col), cell in table.get_celld().items(): # Duyệt qua từng ô trong bảng theo (hàng, cột)
        cell.set_edgecolor('#bdc3c7')
        if row == 0:    #  tiêu đề 
            # Tô nền xanh đậm, chữ trắng in đậm cho tiêu đề
            cell.set_facecolor('#1f618d'); cell.set_text_props(weight='bold', color='white')
        else:
            # Tô màu xen kẽ: hàng lẻ màu xám nhạt, hàng chẵn màu trắng 
            cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff')
            # Cột 0,3,7,8 in đậm; cột 8 chữ đỏ, cột 7 chữ xanh lá, còn lại chữ xám đen
            cell.set_text_props(weight='bold' if col in [0, 3, 7, 8] else 'normal',
                                color='#c0392b' if col==8 else ('#27ae60' if col==7 else '#2c3e50'))
    # Đặt tiêu đề lớn cho toàn bộ hình, cỡ chữ 15, in đậm, màu xanh navy, vị trí gần sát mép trên
    plt.suptitle("BẢNG ĐIỀU KHIỂN TOÀN CẢNH 5 KHỐI XÉT TUYỂN ĐẠI HỌC TRUYỀN THỐNG - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show() # Hiển thị hình ra màn hình

 # Định nghĩa hàm vẽ dashboard cho 1 khối thi, nhận vào tên cột khối, tên khối, mô tả môn học
def _plot_single_block_dashboard(block_col, block_name, subjects_desc, color_theme="#1f77b4"):
    """
    SUPER DASHBOARD TỪNG KHỐI THI: Phổ điểm KDE + Phân bố 6 ngưỡng xét tuyển Đại học
    + Bảng số liệu 12 thông số chuyên sâu cho từng khối thi (A00, A01, B00, C00, D01).
    """
    df = get_all_data()  # Lấy toàn bộ dữ liệu
    if df.empty or block_col not in df.columns: return # Nếu dữ liệu rỗng hoặc không có cột khối thi này trong bảng thì thoát hàm luôn
    s = df[block_col].dropna() # Lấy cột điểm của khối thi này, bỏ các giá trị rỗng 
    if s.empty: return # Nếu sau khi lọc không còn dữ liệu thì thoát hàm luôn

    total_hs = len(s) # Tổng số học sinh 
    mean_val, median_val = s.mean(), s.median()  # Tính điểm trung bình và điểm trung vị
    # Tính mode (giá trị xuất hiện nhiều nhất); nếu không có mode thì gán = 0
    mode_val = s.mode().iloc[0] if not s.mode().empty else 0
    std_val = s.std() # Tính độ lệch chuẩn
    min_val, max_val = s.min(), s.max()  # Lấy điểm thấp nhất và điểm cao nhất
    top27_count = (s >= 27.0).sum() # Đếm số học sinh có điểm >= 27
    top24_count = (s >= 24.0).sum() # Đếm số học sinh có điểm >= 24

    # Phân khúc 6 ngưỡng xét tuyển
    bins = [0, 15, 18, 21, 24, 27, 30] # Các mốc điểm để chia nhóm (0-15, 15-18, 18-21, 21-24, 24-27, 27-30)
    # Tên nhãn tương ứng cho từng khoảng điểm ở trên
    labels = ['< 15đ\n(Dưới sàn)', '15 - 18đ\n(TB - Khá)', '18 - 21đ\n(Khá)', '21 - 24đ\n(Giỏi)', '24 - 27đ\n(Top Trọng điểm)', '27 - 30đ\n(Top Thủ khoa)']
    # Chia điểm s vào các khoảng (bins), gán nhãn, đếm số lượng mỗi nhóm rồi sắp xếp theo thứ tự khoảng
    counts = pd.cut(s, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()

    fig = plt.figure(figsize=(16, 9.5))    # Tạo hình vẽ tổng
    # Chia hình thành lưới 2 hàng x 2 cột, hàng trên cao gấp 2.2 lần hàng dưới, khoảng cách giữa hàng/cột
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
    # Tạo 2 biểu đồ con ở hàng trên: ax1 (cột trái), ax2 (cột phải)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    # Tạo 1 vùng ở hàng dưới (chiếm cả 2 cột) dùng để đặt bảng, tắt hiển thị trục (vì đây là bảng, không phải biểu đồ)
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # BIỂU ĐỒ TRÁI: KDE PHỔ ĐIỂM KHỐI THI
    # Vẽ histogram
    sns.histplot(s, bins=45, kde=True, ax=ax1, color=color_theme, stat="count", edgecolor='white', alpha=0.65)
    ax1.axvline(mean_val, color='#c0392b', linestyle='--', linewidth=2.5, label=f'Điểm TB: {mean_val:.2f}đ')
    ax1.axvline(median_val, color='#27ae60', linestyle='-', linewidth=2, label=f'Trung vị: {median_val:.2f}đ')

    # Tô màu dải điểm đỗ Đại học trọng điểm
    ax1.axvspan(24.0, 27.0, color='#2ecc71', alpha=0.18, label='Vùng Giỏi (24 - 27đ)')
    ax1.axvspan(27.0, 30.0, color='#f1c40f', alpha=0.25, label='Vùng Top Thủ Khoa (27 - 30đ)')

    ax1.set_title(f'PHỔ ĐIỂM CHI TIẾT & VÙNG ĐIỂM CHUẨN - {block_name.upper()} ({subjects_desc})', fontweight='bold', fontsize=13, color='#2c3e50')
    ax1.set_xlabel("Thang điểm xét tuyển Đại học (0 - 30 điểm)", fontweight='bold', fontsize=10)
    ax1.set_ylabel("Số lượng thí sinh", fontweight='bold', fontsize=10); ax1.set_xlim(0, 30)
    ax1.legend(loc="upper right", frameon=True, facecolor='white', edgecolor='#bdc3c7', fontsize=9)

    # BIỂU ĐỒ PHẢI: 6 PHÂN KHÚC NGƯỠNG ĐIỂM XÉT TUYỂN
    palette_colors = ['#95a5a6', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
    sns.barplot(x=counts.index, y=counts.values, ax=ax2, palette=palette_colors, edgecolor='black', linewidth=0.8)
    # Tiêu đề biểu đồ
    ax2.set_title(f'PHÂN BỐ 6 NGƯỠNG ĐIỂM XÉT TUYỂN ĐẠI HỌC - {block_name.upper()}', fontweight='bold', fontsize=13, color='#2c3e50')
    ax2.set_xlabel("Phân khúc điểm thi & Cơ hội đỗ Đại học", fontweight='bold', fontsize=10)
    ax2.set_ylabel("Số lượng thí sinh", fontweight='bold', fontsize=10)

    for p in ax2.patches:
        h = p.get_height() # Lấy chiều cao cột hiện tại
        if h > 0:  # Chỉ ghi chú nếu cột có giá trị > 0 
            pct = (h / total_hs) * 100  # Tính phần trăm của nhóm này so với tổng số học sinh
             # Ghi 2 dòng lên đỉnh cột: số lượng (có dấu phẩy ngăn cách nghìn) và % tương ứng
            ax2.annotate(f'{int(h):,}\n({pct:.1f}%)', (p.get_x() + p.get_width() / 2., h),
            # Căn giữa theo x, căn đáy chữ theo y, chữ đậm màu xám đen, dịch lên 3 point cho khỏi dính cột

                         ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, counts.max() * 1.2) # Giới hạn trục Y từ 0 đến 120% giá trị lớn nhất, để chừa khoảng trống cho chú thích phía trên

    # BẢNG SỐ LIỆU PHÍA DƯỚI
    table_data = [
        ["Tổ hợp xét tuyển:", f"{block_name} ({subjects_desc})", "Điểm cao nhất (Max):", f"{max_val} điểm", "Dưới sàn (< 15đ):", f"{(counts.iloc[0]/total_hs*100):.1f}%"],
        ["Tổng thí sinh dự thi:", f"{total_hs:,} HS", "Điểm thấp nhất (Min):", f"{min_val} điểm", "Mức Khá (18 - 21đ):", f"{(counts.iloc[2]/total_hs*100):.1f}%"],
        ["Điểm Trung Bình (Mean):", f"{mean_val:.2f} điểm", "Thí sinh ≥ 24.0 điểm:", f"{top24_count:,} HS", "Mức Giỏi (21 - 24đ):", f"{(counts.iloc[3]/total_hs*100):.1f}%"],
        ["Điểm Trung Vị (Median):", f"{median_val:.2f} điểm", "Thí sinh ≥ 27.0 điểm:", f"{top27_count:,} HS", "Top Trọng điểm (24-27):", f"{(counts.iloc[4]/total_hs*100):.1f}%"],
        ["Điểm Phổ Biến (Mode):", f"{mode_val:.2f} điểm", "Độ Lệch Chuẩn (Std Dev):", f"{std_val:.2f}", "Top Thủ Khoa (27-30):", f"{(counts.iloc[5]/total_hs*100):.2f}%"]
    ]

    col_widths = [0.18, 0.16, 0.18, 0.14, 0.18, 0.16] # Độ rộng từng cột trong bảng
    # Vẽ bảng từ table_data, căn trái nội dung, áp độ rộng cột
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths) 
    # Tắt tự động chỉnh cỡ chữ, đặt cỡ chữ = 10, phóng to bảng theo chiều cao
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.6)

    for (row, col), cell in table.get_celld().items(): # Duyệt qua từng ô trong bảng
        cell.set_edgecolor('#bdc3c7')
        if col in [0, 2, 4]:
            cell.set_facecolor('#ecf0f1'); cell.set_text_props(weight='bold', color='#2c3e50')
        else:
            cell.set_facecolor('#ffffff')
            cell.set_text_props(weight='bold', color='#2980b9' if col==1 else ('#27ae60' if col==3 else '#8e44ad'))
    # Tiêu đề lớn cho toàn bộ hình
    plt.suptitle(f"BẢNG ĐIỀU KHIỂN CHUYÊN SÂU KHỐI XÉT TUYỂN {block_name.upper()} - THPT QUỐC GIA 2025",
                 fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show() # Hiển thị hình

# --- 5 HÀM GỌI RIÊNG BIỆT CHO 5 KHỐI XÉT TUYỂN ĐẠI HỌC ---
def plot_block_a00(): _plot_single_block_dashboard("A00", "Khối A00", "Toán - Lý - Hóa", "#1f77b4")  # Xanh dương
def plot_block_a01(): _plot_single_block_dashboard("A01", "Khối A01", "Toán - Lý - Anh", "#ff7f0e")  # Cam
def plot_block_b00(): _plot_single_block_dashboard("B00", "Khối B00", "Toán - Hóa - Sinh", "#2ca02c") # Xanh lá
def plot_block_c00(): _plot_single_block_dashboard("C00", "Khối C00", "Văn - Sử - Địa", "#d62728")   # Đỏ
def plot_block_d01(): _plot_single_block_dashboard("D01", "Khối D01", "Toán - Văn - Anh", "#8e44ad")  # Tím
# =====================================================================
# NHÓM 4: ĐÁNH GIÁ ĐỀ THI & TƯƠNG QUAN SƯ PHẠM (CHỈ TIÊU 18, 19, 20)
# =====================================================================
#  đánh giá độ khó & tương quan sư phạm của đề thi
def analyze_group4_exam_evaluation():
    """
    SƯ PHẠM: Kết hợp Đánh giá Độ khó & Độ phân hóa CV%
    với 2 biểu đồ chuẩn đứt nét ngưỡng và Bảng số liệu tổng hợp 9 môn!
    """
      # Docstring: mô tả chức năng hàm
    df = get_all_data()   # Lấy toàn bộ dữ liệu
    if df.empty: return  # Nếu dữ liệu rỗng thì thoát hàm
    # In thông báo đang xử lý
    print("\nĐang phân tích Sư phạm: Độ khó & Khả năng phân hóa 9 môn thi...")
    # Danh sách 9 môn thi: (tên cột trong data, tên hiển thị tiếng Việt)    
    subjects = [('toan', 'Toán'), ('ngu_van', 'Ngữ Văn'), ('vat_ly', 'Vật Lý'),
                ('hoa_hoc', 'Hóa Học'), ('sinh_hoc', 'Sinh Học'), ('lich_su', 'Lịch Sử'),
                ('dia_ly', 'Địa Lý'), ('ngoai_ngu', 'Ngoại Ngữ'), ('gdcd', 'GDCD')]
    
    # 1. Tính toán số liệu thống kê sư phạm
    eval_list = []  # Danh sách rỗng để chứa kết quả từng môn
    for col, name in subjects:# Duyệt qua từng môn (tên cột, tên hiển thị)
        if col not in df.columns: continue # Nếu cột không tồn tại trong data → bỏ qua môn này
        s = df[col].dropna() # Lấy điểm môn đó, bỏ giá trị rỗng
        if len(s) == 0: continue  # Nếu không còn dữ liệu → bỏ qua môn này
        mean_val, std_val = s.mean(), s.std() # Tính điểm trung bình và độ lệch chuẩn
        # Tính hệ số biến thiên CV% = (độ lệch chuẩn / trung bình) * 100 — đo độ phân hóa điểm
        cv_val = (std_val / mean_val) * 100 if mean_val > 0 else 0
        
        # Phân loại độ khó (Chỉ tiêu 18)
        # Xếp loại đề thi khó/dễ/trung bình dựa vào điểm trung bình, kèm màu tương ứng
        if mean_val < 5.5: diff_label = "Khó (< 5.5đ)"; diff_color = "#e74c3c" # Đỏ
        elif mean_val > 7.0: diff_label = "Dễ (> 7.0đ)"; diff_color = "#27ae60" # Xanh lá
        else: diff_label = "Trung Bình (5.5 - 7đ)"; diff_color = "#f39c12"     # Vàng
        
        # Phân loại độ phân hóa (Chỉ tiêu 19)
        # Đánh giá khả năng phân hóa thí sinh dựa vào CV%, kèm màu tương ứng
        if cv_val >= 25.0: diff_diff = "Tốt (CV ≥ 25%)"; diff_diff_color = "#2980b9" # Xanh dương
        else: diff_diff = "Kém (CV < 25%)"; diff_diff_color = "#95a5a6"              # Xám
        # Gom tất cả kết quả tính được của môn này thành 1 dict, thêm vào danh sách eval_list
        eval_list.append({
            "col": col, "Môn Thi": name.upper(), "Điểm TB": mean_val, "Độ Lệch Chuẩn": std_val,
            "CV (%)": cv_val, "Độ Khó": diff_label, "Phân Hóa": diff_diff,
            "color_diff": diff_color, "color_cv": diff_diff_color
        })
    df_eval = pd.DataFrame(eval_list)  # Chuyển danh sách kết quả thành DataFrame để dễ xử lý/hiển thị tiếp

    # In ra Terminal
    print("\n" + "="*120)
    # In tiêu đề bảng
    print("BẢNG ĐÁNH GIÁ SƯ PHẠM CHUẨN QUỐC GIA: ĐỘ KHÓ & KHẢ NĂNG PHÂN HÓA ĐỀ THI 2025")
    print("="*120) # In tiếp 1 dòng kẻ ngăn cách
    # Lấy ra các cột cần thiết từ df_eval để in (bỏ các cột màu color_diff, color_cv), tạo bản sao riêng
    df_print = df_eval[['Môn Thi', 'Điểm TB', 'Độ Lệch Chuẩn', 'CV (%)', 'Độ Khó', 'Phân Hóa']].copy()
    # Làm tròn 2 số thập phân cho cột Điểm TB và Độ Lệch
    for c in ['Điểm TB', 'Độ Lệch Chuẩn']: df_print[c] = df_print[c].round(2)
    # Làm tròn 1 số thập phân cho cột CV%, chuyển thành chuỗi và thêm ký hiệu %
    df_print['CV (%)'] = df_print['CV (%)'].round(1).astype(str) + "%"
    # In bảng ra terminal dạng chuỗi, không hiển thị cột index
    print(df_print.to_string(index=False))
    print("="*120 + "\n") # In dòng kẻ ngăn cách + xuống dòng kết thúc

    # 2. Cấu hình Super Dashboard (GridSpec 2 hàng)
    fig = plt.figure(figsize=(16, 9.5))  # Tạo hình tổng
    # Chia lưới 2 hàng x 2 cột, hàng trên cao gấp 2.3 lần hàng dưới, khoảng cách hàng/cột
    gs = fig.add_gridspec(2, 2, height_ratios=[2.3, 1], hspace=0.35, wspace=0.2)

    ax1 = fig.add_subplot(gs[0, 0]) # Biểu đồ cột 1: đặt ở hàng trên, cột trái
    ax2 = fig.add_subplot(gs[0, 1]) # Biểu đồ cột 2: đặt ở hàng trên, cột phải
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off') # Vùng bảng: chiếm cả hàng dưới, tắt hiển thị trục

    # --- BIỂU ĐỒ TRÁI: ĐIỂM TRUNG BÌNH & ĐÁNH GIÁ ĐỘ KHÓ ---
    # Vẽ biểu đồ cột: trục X là tên môn, trục Y là điểm trung bình, mỗi cột tô màu riêng theo độ khó
    sns.barplot(x='Môn Thi', y='Điểm TB', data=df_eval, ax=ax1, palette=df_eval['color_diff'].tolist(), edgecolor='black', linewidth=0.8)
    # Tiêu đề biểu đồ
    ax1.set_title('ĐÁNH GIÁ ĐỘ KHÓ ĐỀ THI THEO ĐIỂM TRUNG BÌNH', fontweight='bold', fontsize=12, color='#1a5276') 
    # Nhãn trục X và trục Y
    ax1.set_xlabel("Môn thi tốt nghiệp THPT", fontweight='bold', fontsize=10); ax1.set_ylabel("Điểm trung bình (0 - 10 điểm)", fontweight='bold', fontsize=10)
    # Giới hạn trục Y từ 0-10, xoay nhãn trục X 15 độ cho dễ đọc
    ax1.set_ylim(0, 10); ax1.tick_params(axis='x', rotation=15)

    # Kẻ 2 đường ngưỡng phân loại độ khó
    # Hiển thị chú thích ở góc trên phải
    ax1.axhline(5.5, color='#c0392b', linestyle='--', linewidth=1.8, label='Ngưỡng Khó (5.5đ)')
    ax1.axhline(7.0, color='#27ae60', linestyle='--', linewidth=1.8, label='Ngưỡng Dễ (7.0đ)')
    ax1.legend(loc="upper right", frameon=True, facecolor='white', fontsize=9)

    for p in ax1.patches:  # Duyệt qua từng cột trong biểu đồ ax1
        h = p.get_height() # Lấy chiều cao cột (giá trị điểm TB)
        # Nếu cột có giá trị > 0, ghi số điểm (2 số thập phân) lên đỉnh cột, căn giữa, dịch lên 3 point
        if h > 0: ax1.annotate(f'{h:.2f}đ', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9, fontweight='bold', xytext=(0, 3), textcoords='offset points')

    # --- BIỂU ĐỒ PHẢI: HỆ SỐ PHÂN TÁN CV% & KHẢ NĂNG PHÂN HÓA ---
    # Vẽ biểu đồ cột: trục X là môn thi, trục Y là CV%, tô màu theo mức phân hóa (color_cv)
    sns.barplot(x='Môn Thi', y='CV (%)', data=df_eval, ax=ax2, palette=df_eval['color_cv'].tolist(), edgecolor='black', linewidth=0.8)
    # Tiêu đề biểu đồ
    ax2.set_title('KHẢ NĂNG PHÂN HÓA HỌC SINH THEO HỆ SỐ CV%', fontweight='bold', fontsize=12, color='#922b21')
    # Nhãn trục X và Y
    ax2.set_xlabel("Môn thi tốt nghiệp THPT", fontweight='bold', fontsize=10); ax2.set_ylabel("Hệ số phân tán CV (%)", fontweight='bold', fontsize=10)
     # Xoay nhãn trục X 15 độ cho dễ đọc
    ax2.tick_params(axis='x', rotation=15)

    # Kẻ đường ngưỡng phân hóa chuẩn Bộ Giáo dục (25%)
    # Kẻ đường ngang tại y=25 — ngưỡng chuẩn để đánh giá đề thi phân hóa tốt
    ax2.axhline(25.0, color='#2980b9', linestyle='-', linewidth=2.2, label='Ngưỡng Phân Hóa Tốt (CV ≥ 25%)')
    # Chú thích góc trên phải
    ax2.legend(loc="upper right", frameon=True, facecolor='white', fontsize=9)

    for p in ax2.patches:  # Duyệt từng cột trong ax2
        h = p.get_height() # Lấy chiều cao cột (giá trị CV%)
        # Ghi giá trị CV% lên đỉnh cột nếu > 0
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9, fontweight='bold', xytext=(0, 3), textcoords='offset points')
        # Giới hạn trục Y = 120% giá trị CV% lớn nhất, chừa khoảng trống cho chú thích
    ax2.set_ylim(0, df_eval['CV (%)'].max() * 1.2)

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # Dòng tiêu đề bảng
    table_data = [["Môn Thi", "Điểm Trung Bình", "Độ Lệch Chuẩn (Std)", "Hệ Số CV (%)", "Đánh Giá Độ Khó", "Khả Năng Phân Hóa"]]
    for _, r in df_eval.iterrows():  # Duyệt từng dòng dữ liệu môn thi
        # Thêm 1 dòng vào bảng: tên môn, điểm TB, độ lệch, CV%, đánh giá độ khó, đánh giá phân hóa
        table_data.append([
            f"{r['Môn Thi']}", f"{r['Điểm TB']:.2f} điểm", f"{r['Độ Lệch (Std)']:.2f}",
            f"{r['CV (%)']:.1f}%", r['Độ Khó'], r['Phân Hóa]']
        ])

    col_widths = [0.15, 0.16, 0.18, 0.15, 0.18, 0.18]
    # Vẽ bảng từ table_data, căn giữa nội dung, áp độ rộng cột
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center', colWidths=col_widths)
    # Tắt tự động chỉnh cỡ chữ, đặt cỡ chữ = 10, phóng to bảng theo chiều cao
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.55)

    for (row, col), cell in table.get_celld().items():  # Duyệt qua từng ô trong bảng
        cell.set_edgecolor('#bdc3c7')
        if row == 0:  # Hàng tiêu đề
            cell.set_facecolor('#2c3e50'); cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff')
            # Cột 0,4,5 in đậm; nếu nội dung ô chứa chữ "Khó" → chữ đỏ, chứa "Dễ" hoặc "Tốt" → chữ xanh lá, còn lại → xám đen
            cell.set_text_props(weight='bold' if col in [0, 4, 5] else 'normal',
                                color='#c0392b' if 'Khó' in str(cell.get_text().get_text()) else ('#27ae60' if 'Dễ' in str(cell.get_text().get_text()) or 'Tốt' in str(cell.get_text().get_text()) else '#2c3e50'))
    # Tiêu đề lớn cho toàn bộ hình
    plt.suptitle("BẢNG ĐIỀU KHIỂN ĐÁNH GIÁ SƯ PHẠM ĐỀ THI - THPT QUỐC GIA 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show() # Hiển thị hình


def plot_group4_correlation_matrix(): # Định nghĩa hàm vẽ ma trận tương quan
    """
    Ma trận tương quan môn học (Correlation Matrix).
    Vẽ Heatmap siêu đẹp chứng minh mối liên hệ học lực giữa 9 môn thi!
    """
    df = get_all_data()  # Lấy toàn bộ dữ liệu
    if df.empty: return # Nếu rỗng thì thoát hàm
    # In thông báo đang xử lý
    print("\nĐang tính toán Ma Trận Tương Quan Pearson giữa 9 môn thi...")
    # Danh sách 9 môn: (tên cột data, tên hiển thị)
    subjects = [('toan', 'Toán'), ('ngu_van', 'Ngữ Văn'), ('vat_ly', 'Vật Lý'),
                ('hoa_hoc', 'Hóa Học'), ('sinh_hoc', 'Sinh Học'), ('lich_su', 'Lịch Sử'),
                ('dia_ly', 'Địa Lý'), ('ngoai_ngu', 'Ngoại Ngữ'), ('gdcd', 'GDCD')]
    # Lọc chỉ giữ lại các cột môn thực sự tồn tại trong df            
    valid_cols = [c for c, _ in subjects if c in df.columns]

    # Tính ma trận tương quan Pearson
    corr_matrix = df[valid_cols].rename(columns=dict(subjects)).corr()

    # Cấu hình biểu đồ Heatmap lớn, sang trọng
    plt.figure(figsize=(12, 9))
    
    # Sử dụng bảng màu coolwarm (Đỏ = tương quan dương mạnh, Xanh = tương quan âm/yếu)
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1, 
                linewidths=0.8, linecolor='white', cbar_kws={'label': 'Hệ số tương quan Pearson (r)'},
                annot_kws={"size": 10, "weight": "bold"})
     # Tiêu đề biểu đồ, có ghi chú cách đọc 
    plt.title('[Chỉ tiêu 20] MA TRẬN TƯƠNG QUAN HỌC LỰC GIỮA 9 MÔN THI THPT 2025\n(r > 0.5: Tương quan đồng biến mạnh | r gần 0: Độc lập)', 
              fontsize=14, fontweight='bold', color='#1a5276', pad=18)
    plt.xticks(rotation=25, fontweight='bold', fontsize=11)
    plt.yticks(fontweight='bold', fontsize=11)
    
    plt.tight_layout() # Tự động canh chỉnh layout cho không bị cắt chữ
    plt.show() # Hiển thị hình
# =====================================================================
# NHÓM 5: PHÂN TÍCH ĐỐI TƯỢNG & HỆ ĐÀO TẠO 
# =====================================================================

def analyze_group5_demographics():
    """
    (So sánh chi tiết Lớp 12 vs Tự do & GDPT vs GDTX).
    """
    df = get_all_data() # Lấy toàn bộ dữ liệu
    if df.empty: return # Nếu rỗng thì thoát hàm
     # In thông báo đang xử lý
    print("\nĐang tổng hợp số liệu 10 Chỉ tiêu Nhóm 5: Đối tượng & Hệ đào tạo...")

    def get_group_stats(mask, label): # Hàm con: tính thống kê cho 1 nhóm đối tượng
        sub = df[mask]  # Lọc dữ liệu theo điều kiện mask
        total = len(sub)  # Đếm số lượng thí sinh trong nhóm
        if total == 0: return {} # Nếu nhóm rỗng thì trả về dict rỗng
        tb = sub['diem_tb_4_mon'].mean() # Điểm trung bình 4 môn của nhóm
        # Tỉ lệ % thí sinh có trạng thái "đỗ tốt nghiệp
        do_rate = (sub['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
        # Đếm tổng số điểm 10 xuất hiện trong 4 môn (Toán, Văn, 2 môn tự chọn)
        d10 = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] == 10).sum().sum()
        # Tỉ lệ % thí sinh có ít nhất 1 môn bị điểm liệt (≤ 1.0)
        liet_rate = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] <= 1.0).any(axis=1).mean() * 100
        return { # Trả về dict tổng hợp các chỉ số của nhóm: quy mô, điểm TB, tỉ lệ đỗ, số điểm 10, tỉ lệ điểm liệt
            "Phân Loại Nhóm": label, "Quy Mô (HS)": f"{total:,}", "Tỷ Lệ Quy Mô": f"{(total/len(df)*100):.1f}%",
            "Điểm TB 4 Môn": round(tb, 2), "Tỷ Lệ Đỗ (%)": f"{do_rate:.1f}%",
            "Tổng Điểm 10": f"{d10:,}", "Tỷ Lệ Điểm Liệt (%)": f"{liet_rate:.2f}%"
        }

    stats_list = [  # Gọi hàm get_group_stats cho 4 nhóm đối tượng khác nhau, gom kết quả vào 1 danh sách
        get_group_stats(df['doi_tuong_thi'] == 'Thí sinh Lớp 12', "1. Thí sinh Lớp 12 (Đúng tuổi 2007)"),
        get_group_stats(df['doi_tuong_thi'] == 'Thí sinh Tự do', "2. Thí sinh Tự do (Thi lại/Tự do)"),
        get_group_stats(df['he_dao_tao'] == 'GDPT', "3. Hệ Phổ Thông (GDPT)"),
        get_group_stats(df['he_dao_tao'] == 'GDTX', "4. Hệ Thường Xuyên (GDTX)")
    ]
    
    print("\n" + "="*130) 
    print("BẢNG THỐNG KÊ CHUẨN QUỐC GIA - ĐỐI TƯỢNG DỰ THI & HỆ ĐÀO TẠO THPT 2025")
    print("="*130)
    # Chuyển stats_list (kết quả 4 nhóm) thành DataFrame rồi in ra, không hiện cột index
    print(pd.DataFrame(stats_list).to_string(index=False))
    print("="*130 + "\n") # Dòng kẻ ngăn cách + xuống dòng kết thúc


def plot_group5_target_comparison_dashboard(): # Định nghĩa hàm vẽ dashboard    
    """
    THÍ SINH LỚP 12 vs THÍ SINH TỰ DO
    (Biểu đồ KDE Phổ điểm chồng mờ + Biểu đồ Tỷ lệ đỗ/liệt + Bảng số liệu chuẩn).
    """
    df = get_all_data() # Lấy toàn bộ dữ liệu
    # Nếu dữ liệu rỗng hoặc thiếu cột 'doi_tuong_thi' → thoát hàm
    if df.empty or 'doi_tuong_thi' not in df.columns: return

    fig = plt.figure(figsize=(16, 9.5)) # Tạo hình tổng, kích thước
    # Chia lưới 2 hàng x 2 cột, hàng trên cao gấp 2.2 lần hàng dưới
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)  
    # 2 biểu đồ ở hàng trên: ax1 (trái), ax2 (phải)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    # Vùng bảng ở hàng dưới, tắt trục
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: KDE PHỔ ĐIỂM CHỒNG MỜ 
    sns.kdeplot(data=df, x='diem_tb_4_mon', hue='doi_tuong_thi', fill=True, palette=['#2980b9', '#e67e22'], 
                ax=ax1, common_norm=False, alpha=0.45, linewidth=2.5)
    # Tiêu đề biểu đồ
    ax1.set_title('SO SÁNH PHỔ ĐIỂM: THÍ SINH LỚP 12 vs THÍ SINH TỰ DO', fontweight='bold', fontsize=12, color='#1a5276')
    # Nhãn trục X, Y và giới hạn trục X (0-10)
    ax1.set_xlabel("Điểm trung bình 4 môn thi (0 - 10 điểm)", fontweight='bold', fontsize=10)
    ax1.set_ylabel("Mật độ phân bố thí sinh", fontweight='bold', fontsize=10); ax1.set_xlim(0, 10)
    # Tính điểm trung bình riêng cho nhóm Lớp 12 và nhóm Tự do
    mean_12 = df[df['doi_tuong_thi']=='Thí sinh Lớp 12']['diem_tb_4_mon'].mean()
    mean_td = df[df['doi_tuong_thi']=='Thí sinh Tự do']['diem_tb_4_mon'].mean()
    # Kẻ đường đứng đánh dấu điểm TB của từng nhóm
    ax1.axvline(mean_12, color='#2980b9', linestyle='--', linewidth=2, label=f'TB Lớp 12: {mean_12:.2f}đ')
    ax1.axvline(mean_td, color='#e67e22', linestyle=':', linewidth=2, label=f'TB Tự do: {mean_td:.2f}đ')
    # Chú thích góc trên trái
    ax1.legend(loc="upper left", frameon=True, facecolor='white', fontsize=9.5)

    # --- BIỂU ĐỒ PHẢI: SO SÁNH TỶ LỆ ĐỖ & TỶ LỆ ĐIỂM LIỆT  ---
    comp_data = [] # Danh sách rỗng chứa dữ liệu so sánh 
     # Duyệt qua 2 nhóm
    for grp, color in [('Thí sinh Lớp 12', '#2980b9'), ('Thí sinh Tự do', '#e67e22')]:
        sub = df[df['doi_tuong_thi'] == grp] # Lọc dữ liệu theo nhóm
         # Tính % thí sinh đỗ tốt nghiệp trong nhóm
        do_pct = (sub['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
         # Tính % thí sinh có ít nhất 1 môn bị điểm liệt (≤1.0) trong nhóm
        liet_pct = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] <= 1.0).any(axis=1).mean() * 100
        # Thêm 2 dòng dữ liệu (tỉ lệ đỗ và tỉ lệ điểm liệt) cho nhóm này vào danh sách

        comp_data.append({"Nhóm": grp, "Chỉ Số": "Tỷ Lệ Đỗ Tốt Nghiệp (%)\n", "Tỷ Lệ (%)": do_pct})
        comp_data.append({"Nhóm": grp, "Chỉ Số": "Tỷ Lệ Dính Điểm Liệt (%)\n[", "Tỷ Lệ (%)": liet_pct})
    df_comp = pd.DataFrame(comp_data)  # Chuyển danh sách thành DataFrame để vẽ biểu đồ tiếp
    # Vẽ biểu đồ cột nhóm (grouped bar): trục X là loại chỉ số, trục Y là %, tách màu theo Nhóm
    sns.barplot(x='Chỉ Số', y='Tỷ Lệ (%)', hue='Nhóm', data=df_comp, ax=ax2, palette=['#2980b9', '#e67e22'], edgecolor='black', linewidth=0.8)
    # Tiêu đề, ẩn nhãn trục X (vì đã rõ qua nhãn cột), đặt nhãn trục Y
    ax2.set_title('SO SÁNH TỶ LỆ ĐỖ TỐT NGHIỆP & NGUY CƠ ĐIỂM LIỆT', fontweight='bold', fontsize=12, color='#922b21')
    ax2.set_xlabel(""); ax2.set_ylabel("Tỷ lệ phần trăm (%)", fontweight='bold', fontsize=10)
    # Chú thích, có tiêu đề "Đối tượng dự thi"
    ax2.legend(title="Đối tượng dự thi", loc="upper right", frameon=True, facecolor='white', fontsize=9)

    for p in ax2.patches:  # Duyệt từng cột
        h = p.get_height()  # Lấy chiều cao (giá trị %)
        # Ghi % lên đỉnh cột nếu > 0    
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9.5, fontweight='bold', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, 115)

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # Lọc riêng dữ liệu 2 nhóm để tính toán cho bảng
    sub_12 = df[df['doi_tuong_thi'] == 'Thí sinh Lớp 12']; sub_td = df[df['doi_tuong_thi'] == 'Thí sinh Tự do']
    table_data = [
        ["Chỉ Tiêu Phân Tích", "Thí Sinh Lớp 12 (Chính quy)", "Thí Sinh Tự Do (Thi lại)", "Chênh Lệch / Đánh Giá Sư Phạm"],
        ["Quy mô dự thi :", f"{len(sub_12):,} HS ({len(sub_12)/len(df)*100:.1f}%)", f"{len(sub_td):,} HS ({len(sub_td)/len(df)*100:.1f}%)", "HS Lớp 12 chiếm đa số tuyệt đối trong kỳ thi"],
        ["Điểm TB 4 môn :", f"{mean_12:.2f} điểm", f"{mean_td:.2f} điểm", f"Chênh lệch: {abs(mean_12 - mean_td):.2f} điểm ({'Lớp 12 cao hơn' if mean_12>mean_td else 'Tự do cao hơn'})"],
        ["Tỷ lệ Đỗ tốt nghiệp :", f"{(sub_12['trang_thai'].astype(str).str.lower()=='đỗ tốt nghiệp').mean()*100:.1f}%", f"{(sub_td['trang_thai'].astype(str).str.lower()=='đỗ tốt nghiệp').mean()*100:.1f}%", "Khả năng hoàn thành chương trình THPT"],
        ["Tỷ lệ dính Điểm liệt (≤1đ):", f"{(sub_12[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", f"{(sub_td[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", "Nguy cơ bị hủy kết quả tốt nghiệp do môn liệt"]
    ]

    col_widths = [0.22, 0.23, 0.23, 0.32] # Độ rộng cột
    # Vẽ bảng, tắt auto cỡ chữ, đặt cỡ 10, phóng to chiều cao
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.6)

    for (row, col), cell in table.get_celld().items(): # Duyệt từng ô
        cell.set_edgecolor('#bdc3c7')
         # Hàng tiêu đề
        if row == 0: cell.set_facecolor('#1f618d'); cell.set_text_props(weight='bold', color='white')
         # Hàng dữ liệu
        else: cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1,2] else 'normal', color='#2980b9' if col==1 else ('#e67e22' if col==2 else '#2c3e50'))

    plt.suptitle("BẢNG ĐIỀU KHIỂN PHÂN TÍCH ĐỐI TƯỢNG DỰ THI (LỚP 12 vs TỰ DO) - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show() # Tiêu đề tổng cho toàn dashboard, hiển thị hình


def plot_group5_education_system_dashboard(): # Hàm mới: dashboard so sánh hệ đào tạo GDPT vs GDTX
    """
    HỆ PHỔ THÔNG (GDPT) vs HỆ THƯỜNG XUYÊN (GDTX) 
    (Biểu đồ KDE Phổ điểm + Biểu đồ 3 Chỉ số cốt lõi + Bảng số liệu chuẩn).
    """
    df = get_all_data()   # Lấy dữ liệu
    if df.empty or 'he_dao_tao' not in df.columns: return  # Nếu rỗng hoặc thiếu cột 'he_dao_tao' → thoát

    fig = plt.figure(figsize=(16, 9.5)) # Tạo hình tổng
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
     # 2 biểu đồ trên + bảng dưới (giống cấu trúc các dashboard trước)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: KDE PHỔ ĐIỂM HỆ ĐÀO TẠO  ---
    #QUÝ-QUÝ-
    # Vẽ biểu đồ mật độ (KDE) cho điểm TB, phân màu theo 'hệ đào tạo', tô màu nền dưới đường cong
    sns.kdeplot(data=df, x='diem_tb_4_mon', hue='he_dao_tao', fill=True, palette=['#27ae60', '#8e44ad'], 
                ax=ax1, common_norm=False, alpha=0.45, linewidth=2.5)  
    # Đặt tiêu đề cho biểu đồ trái (in đậm, cỡ chữ 12, màu xanh đậm)
    ax1.set_title('SO SÁNH PHỔ ĐIỂM: HỆ GDPT vs HỆ GDTX', fontweight='bold', fontsize=12, color='#1a5276')
    # Đặt tên cho trục ngang (trục x) là khoảng điểm
    ax1.set_xlabel("Điểm trung bình 4 môn thi (0 - 10 điểm)", fontweight='bold', fontsize=10)
    # Đặt tên trục dọc (trục y) là Mật độ; Đồng thời ép trục x chỉ hiển thị từ 0 đến 10
    ax1.set_ylabel("Mật độ phân bố thí sinh", fontweight='bold', fontsize=10); ax1.set_xlim(0, 10)
    
    # Tính điểm trung bình chung của nhóm 'GDPT'
    mean_gdpt = df[df['he_dao_tao']=='GDPT']['diem_tb_4_mon'].mean()
    # Tính điểm trung bình chung của nhóm 'GDTX'
    mean_gdtx = df[df['he_dao_tao']=='GDTX']['diem_tb_4_mon'].mean()
    # Kẻ đường thẳng đứng (nét đứt, màu xanh) tại điểm trung bình của GDPT
    ax1.axvline(mean_gdpt, color='#27ae60', linestyle='--', linewidth=2, label=f'TB GDPT: {mean_gdpt:.2f}đ')
    # Kẻ đường thẳng đứng (nét chấm bi, màu tím) tại điểm trung bình của GDTX
    ax1.axvline(mean_gdtx, color='#8e44ad', linestyle=':', linewidth=2, label=f'TB GDTX: {mean_gdtx:.2f}đ')
    # Hiển thị bảng chú giải góc trên bên trái biểu đồ
    ax1.legend(loc="upper left", frameon=True, facecolor='white', fontsize=9.5)

    # --- BIỂU ĐỒ PHẢI: SO SÁNH TỶ LỆ ĐỖ & TỶ LỆ ĐIỂM 10 / ĐIỂM LIỆT
    # Tạo một danh sách rỗng để gom các kết quả tính toán bên dưới
    comp_data = []
    # Vòng lặp chạy qua 2 nhóm: GDPT (màu xanh) và GDTX (màu tím)
    for grp, color in [('GDPT', '#27ae60'), ('GDTX', '#8e44ad')]:
        # Lọc lấy dữ liệu riêng của từng nhóm tương ứng
        sub = df[df['he_dao_tao'] == grp]
        # Chuyển trạng thái sang chữ thường, tìm ai 'đỗ tốt nghiệp', tính tỷ lệ trung bình rồi nhân 100 để ra %
        do_pct = (sub['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
        # Kiểm tra 4 môn thi, tìm ai có ít nhất 1 môn (any) <= 1.0 (điểm liệt), tính tỷ lệ %
        liet_pct = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] <= 1.0).any(axis=1).mean() * 100
        # Lưu kết quả tỷ lệ Đỗ Tốt Nghiệp vào danh sách comp_data
        comp_data.append({"Hệ Đào Tạo": grp, "Chỉ Số": "Tỷ Lệ Đỗ Tốt Nghiệp (%)\n", "Tỷ Lệ (%)": do_pct})
        # Lưu kết quả tỷ lệ Nguy cơ Điểm Liệt vào danh sách comp_data
        comp_data.append({"Hệ Đào Tạo": grp, "Chỉ Số": "Nguy Cơ Dính Điểm Liệt (%)\n", "Tỷ Lệ (%)": liet_pct})
        # Chuyển đổi danh sách dữ liệu vừa gom được thành một bảng dữ liệu DataFrame của Pandas
    df_comp = pd.DataFrame(comp_data)
    # Vẽ biểu đồ cột (barplot) để so sánh các tỷ lệ, phân màu theo Hệ đào tạo, có viền đen mỏng quanh cột
    sns.barplot(x='Chỉ Số', y='Tỷ Lệ (%)', hue='Hệ Đào Tạo', data=df_comp, ax=ax2, palette=['#27ae60', '#8e44ad'], edgecolor='black', linewidth=0.8)
    # Đặt tiêu đề cho biểu đồ phải (in đậm, cỡ chữ 12, màu đỏ sậm)
    ax2.set_title('HIỆU QUẢ ĐÀO TẠO: TỶ LỆ ĐỖ vs NGUY CƠ ĐIỂM LIỆT', fontweight='bold', fontsize=12, color='#922b21')
    # Xóa tên trục ngang (để trống); Đặt tên trục dọc là "Tỷ lệ phần trăm (%)"
    ax2.set_xlabel(""); ax2.set_ylabel("Tỷ lệ phần trăm (%)", fontweight='bold', fontsize=10)
    # Hiển thị bảng chú giải ở góc trên bên phải, đặt tiêu đề chú giải là "Mô hình học"
    ax2.legend(title="Mô hình học", loc="upper right", frameon=True, facecolor='white', fontsize=9)
    # Tự động ghi số phần trăm (%) lên đỉnh các cột của biểu đồ
    for p in ax2.patches:
        h = p.get_height()
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9.5, fontweight='bold', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, 115)# Kéo dài trục Y thêm một chút để không bị cắt mất chữ

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # 1. Chuẩn bị data: Tách riêng 2 hệ và đếm tổng số điểm 10 của 4 môn thi
    sub_gdpt = df[df['he_dao_tao'] == 'GDPT']; sub_gdtx = df[df['he_dao_tao'] == 'GDTX']
    d10_gdpt = (sub_gdpt[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] == 10).sum().sum()
    d10_gdtx = (sub_gdtx[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] == 10).sum().sum()
    # 2. Xây dựng nội dung bảng: Mỗi list nhỏ là một hàng (Gồm: Tên chỉ số, Giá trị GDPT, Giá trị GDTX, Nhận xét)
    table_data = [
        ["Chỉ Tiêu Phân Tích", "Hệ Phổ Thông (Trường THPT chuẩn)", "Hệ Thường Xuyên (Trung tâm GDTX)", "Chênh Lệch / Đánh Giá Sư Phạm"],
        ["Quy mô đào tạo:", f"{len(sub_gdpt):,} HS ({len(sub_gdpt)/len(df)*100:.1f}%)", f"{len(sub_gdtx):,} HS ({len(sub_gdtx)/len(df)*100:.1f}%)", "Hệ GDPT chiếm đa số trong hệ thống giáo dục"],
        ["Điểm TB 4 môn:", f"{mean_gdpt:.2f} điểm", f"{mean_gdtx:.2f} điểm", f"Chênh lệch: {abs(mean_gdpt - mean_gdtx):.2f} điểm ({'GDPT cao hơn' if mean_gdpt>mean_gdtx else 'GDTX cao hơn'})"],
        ["Tỷ lệ Đỗ tốt nghiệp:", f"{(sub_gdpt['trang_thai'].astype(str).str.lower()=='đỗ tốt nghiệp').mean()*100:.1f}%", f"{(sub_gdtx['trang_thai'].astype(str).str.lower()=='đỗ tốt nghiệp').mean()*100:.1f}%", "Hiệu quả đầu ra giữa 2 mô hình trường học"],
        ["Tổng ca Điểm 10:", f"{d10_gdpt:,} lượt đạt điểm 10", f"{d10_gdtx:,} lượt đạt điểm 10", f"Tỷ lệ điểm xuất sắc cực hạn của từng hệ"],
        ["Tỷ lệ dính Điểm liệt:", f"{(sub_gdpt[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", f"{(sub_gdtx[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", "Nguy cơ rớt tốt nghiệp do môn liệt"]
    ]
    # 3. Vẽ và căn chỉnh bảng lên khung ax_table
    col_widths = [0.22, 0.23, 0.23, 0.32] # Cố định độ rộng 4 cột
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.5) # Chỉnh cỡ chữ và giãn dòng
    # 4. Trang trí bảng: Tô màu nền tiêu đề, làm xen kẽ màu các hàng và đổi màu chữ cho dễ nhìn
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7')
        if row == 0: cell.set_facecolor('#1f618d'); cell.set_text_props(weight='bold', color='white')
        else: cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1,2] else 'normal', color='#27ae60' if col==1 else ('#8e44ad' if col==2 else '#2c3e50'))
# Đặt tiêu đề lớn nhất cho toàn bộ hình ảnh và xuất biểu đồ ra màn hình
    plt.suptitle("BẢNG ĐIỀU KHIỂN PHÂN TÍCH HỆ ĐÀO TẠO (GDPT vs GDTX) - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()
# =====================================================================
# NHÓM 6: CHÍNH SÁCH ƯU TIÊN & NGUYÊN NHÂN TRƯỢT
# =====================================================================

def analyze_group6_policies_and_failures():
    """
    CHÍNH SÁCH: Phân tích Khu vực ưu tiên,
    Tác động "Cứu rỗi" điểm cộng & Bóc tách Nguyên nhân trượt.
    """
    df = get_all_data() # Lấy dữ liệu tổng
    if df.empty: return # Thoát hàm nếu dữ liệu trống
    print("\nĐang phân tích chuyên sâu Nhóm 6: Chính sách ưu tiên & Nguyên nhân trượt...")

    # 1. PHÂN TÍCH NGUYÊN NHÂN TRƯỢT TỐT NGHIỆP (CHỈ TIÊU 33)
    # Lọc ra danh sách học sinh bị "trượt tốt nghiệp" và đếm tổng số lượng
    truot_df = df[df['trang_thai'].astype(str).str.lower() == 'trượt tốt nghiệp'].copy()
    total_truot = len(truot_df)
    
    if total_truot > 0:
        # Đếm số HS trượt do dính "điểm liệt" (có ít nhất 1 môn <= 1.0)
        dinh_liet = truot_df[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']].apply(lambda r: (r <= 1.0).any(), axis=1)
        truot_do_liet = dinh_liet.sum()
        # Số HS trượt do điểm TB thấp = Tổng số trượt trừ đi số bị điểm liệt
        truot_do_tb_thap = total_truot - truot_do_liet
    else:
        truot_do_liet = 0; truot_do_tb_thap = 0

    # 2. PHÂN TÍCH TÁC ĐỘNG "CỨU RỖI" CỦA ĐIỂM ƯU TIÊN 
    # Điều kiện 1: Không có môn nào bị điểm liệt
    no_liet = ~df[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']].apply(lambda r: (r <= 1.0).any(), axis=1)
    # Điều kiện 2: Điểm trung bình gốc (chưa cộng) dưới 5.0
    tb_thuc_te_thap = df['diem_tb_4_mon'] < 5.0
    # Tính tổng điểm cộng (Ưu tiên + Khuyến khích), gán bằng 0 nếu dữ liệu trống (NaN)
    tong_diem_cong = df['diem_uu_tien'].fillna(0) + df['diem_khuyen_khich'].fillna(0)
    # Tính điểm trung bình mới (cộng thêm điểm ưu tiên đã chia đều cho 4 môn)
    tb_sau_cong = df['diem_tb_4_mon'] + (tong_diem_cong / 4.0)
    # Lọc ra các HS "được cứu": Không liệt & TB gốc < 5.0 & TB mới >= 5.0
    duoc_cuu_df = df[no_liet & tb_thuc_te_thap & (tb_sau_cong >= 5.0)]
    so_hs_duoc_cuu = len(duoc_cuu_df)

    # In báo cáo ra Terminal
    print("\n" + "="*125)
    print("BẢNG BÓC TÁCH NGUYÊN NHÂN TRƯỢT & TÁC ĐỘNG CHÍNH SÁCH ƯU TIÊN THPT 2025")
    print("="*125)
    print(f"TỔNG SỐ THÍ SINH TRƯỢT TỐT NGHIỆP: {total_truot:,} HS ({total_truot/len(df)*100:.2f}% toàn quốc)")
    print(f"    1. Trượt do DÍNH ĐIỂM LIỆT (≤ 1.0 điểm):       {truot_do_liet:,} HS ({truot_do_liet/max(1,total_truot)*100:.1f}%) -> Nguyên nhân tử huyệt!")
    print(f"    2. Trượt do ĐIỂM TB TOÀN KHÓA KHÔNG ĐẠT 5.0:   {truot_do_tb_thap:,} HS ({truot_do_tb_thap/max(1,total_truot)*100:.1f}%) -> Học lực yếu toàn diện.")
    print("-"*125)
    print(f"TÁC ĐỘNG 'CỨU RỖI': Có đúng [{so_hs_duoc_cuu:,} thí sinh] (điểm TB thực tế < 5.0) ")
    print(f"đã chuyển trạng thái từ TRƯỢT thành ĐỖ TỐT NGHIỆP nhờ được cộng Điểm ưu tiên & Khuyến khích!")
    print("="*125 + "\n")

    # 3. Cấu hình Super Dashboard (GridSpec 2 hàng)
    # Tạo khung ảnh lớn và chia layout 2 hàng x 2 cột (Hàng trên cao gấp 2.2 lần hàng dưới)
    fig = plt.figure(figsize=(16, 9.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
    # Thiết lập vị trí cho biểu đồ trái (ax1), phải (ax2) và bảng dữ liệu (ax_table)
    ax1 = fig.add_subplot(gs[0, 0]) # Boxplot Khu vực ưu tiên (Chỉ tiêu 31)
    ax2 = fig.add_subplot(gs[0, 1]) # Donut chart Nguyên nhân trượt (Chỉ tiêu 33)
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: PHÂN BỐ ĐIỂM THEO KHU VỰC ƯU TIÊN [CHỈ TIÊU 31] ---
    # Thiết lập thứ tự ưu tiên hiển thị trên biểu đồ và chỉ giữ lại các khu vực có thật trong data
    kv_order = ['KV1', 'KV2-NT', 'KV2', 'KV3']
    valid_kv = [k for k in kv_order if k in df['khu_vuc_uu_tien'].unique()]
    # Vẽ biểu đồ hộp (boxplot) so sánh phổ điểm các khu vực, kèm dấu chấm đỏ thể hiện giá trị trung bình (mean)
    sns.boxplot(x='khu_vuc_uu_tien', y='diem_tb_4_mon', data=df, order=valid_kv, palette='Set3', ax=ax1, linewidth=1.5,
                showmeans=True, meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"red", "markersize": 8})
    # Cài đặt tiêu đề, nhãn trục X (tên khu vực) và trục Y (điểm số) cho Boxplot
    ax1.set_title('PHÂN BỐ ĐIỂM TRUNG BÌNH THEO KHU VỰC ƯU TIÊN', fontweight='bold', fontsize=12, color='#1a5276')
    ax1.set_xlabel("Khu vực (KV1: Miền núi/Vùng sâu -> KV3: Nội thành TP lớn)", fontweight='bold', fontsize=10)
    ax1.set_ylabel("Điểm trung bình 4 môn thi (0 - 10 điểm)", fontweight='bold', fontsize=10); ax1.set_ylim(0, 10)
    
    # Ghi chú giá trị Mean lên từng cột Boxplot
    # Tính điểm trung bình của từng khu vực và tạo nhãn text hiển thị trực tiếp lên biểu đồ Boxplot
    means_kv = df.groupby('khu_vuc_uu_tien')['diem_tb_4_mon'].mean()
    for idx, kv in enumerate(valid_kv):
        if kv in means_kv:
            ax1.text(idx, 9.2, f"TB: {means_kv[kv]:.2f}đ", ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.25', facecolor='#fef9e7', edgecolor='#e67e22'), fontweight='bold', fontsize=9)

    # --- BIỂU ĐỒ PHẢI: BIỂU ĐỒ TRÒN DONUT NGUYÊN NHÂN TRƯỢT [CHỈ TIÊU 33] ---
    # Khởi tạo nhãn, tỷ lệ và màu sắc (Đỏ cho liệt, Cam cho điểm thấp)
    if total_truot > 0:
        labels_pie = [f'Trượt do Điểm Liệt (≤ 1đ)\n({truot_do_liet:,} HS)', f'Trượt do Điểm TB < 5.0\n({truot_do_tb_thap:,} HS)']
        sizes_pie = [truot_do_liet, truot_do_tb_thap]
        colors_pie = ['#e74c3c', '#f39c12']
        # Vẽ biểu đồ tròn. Thuộc tính width=0.45 đục lỗ ở giữa để tạo thành biểu đồ Nhẫn (Donut)
        wedges, texts, autotexts = ax2.pie(sizes_pie, labels=labels_pie, autopct='%1.1f%%', startangle=140, 
                                           colors=colors_pie, wedgeprops=dict(width=0.45, edgecolor='w', linewidth=2),
                                           textprops=dict(fontweight='bold', fontsize=10))
        # Đổi màu chữ tỷ lệ % bên trong lõi thành màu trắng cho dễ đọc
        for autotext in autotexts: autotext.set_color('white'); autotext.set_fontsize(11)
        ax2.set_title('BÓC TÁCH TỶ LỆ NGUYÊN NHÂN TRƯỢT TỐT NGHIỆP', fontweight='bold', fontsize=12, color='#922b21')
    else:
        # Nếu dữ liệu không có ai trượt thì in ra thông báo chúc mừng thay vì vẽ biểu đồ trống
        ax2.text(0.5, 0.5, "Tuyệt vời!\nKhông có thí sinh nào trượt tốt nghiệp!", ha='center', va='center', fontsize=14, fontweight='bold', color='#27ae60')
        ax2.set_title('BÓC TÁCH NGUYÊN NHÂN TRƯỢT', fontweight='bold', fontsize=12)

    # --- BẢNG ĐỒ HỌA PHÍ DƯỚI [TỔNG HỢP CHÍNH SÁCH] ---
    # Tạo dữ liệu bảng. (Mình đã bổ sung các chuỗi text bị cắt ngang trong ảnh để code không bị lỗi)
    table_data = [
        ["Phân Tích Chính Sách Ưu Tiên", "Số Liệu Thống Kê Thực Tế", "Tỷ Lệ / Tác Động", "Đánh Giá Ý Nghĩa Xã Hội & Sư Phạm"],
        ["KV1 (Miền núi / Vùng đặc biệt khó khăn):", f"{len(df[df['khu_vuc_uu_tien']=='KV1']):,} HS", f"TB: {means_kv.get('KV1', 0):.2f} điểm", "Được cộng mức điểm ưu tiên cao nhất (+0.75đ) để bù đắp điều kiện học tập"],
        ["KV2-NT (Nông thôn) & KV2 (Thị xã/TP tỉnh):", f"{len(df[df['khu_vuc_uu_tien'].isin(['KV2-NT','KV2'])]):,} HS", f"TB: {(means_kv.get('KV2-NT',0)+means_kv.get('KV2',0))/2:.2f} điểm", "Vùng trung du và ngoại thành, được cộng ưu tiên +0.25đ đến +0.5đ"],
        ["KV3 (Nội thành các TP lớn - Không ưu tiên):", f"{len(df[df['khu_vuc_uu_tien']=='KV3']):,} HS", f"TB: {means_kv.get('KV3', 0):.2f} điểm", "Sở hữu điều kiện học tập tốt nhất, điểm trung bình thực tế dẫn đầu cả nước"],
        ["Tác động 'CỨU RỖI' của Điểm ưu tiên:", f"{so_hs_duoc_cuu:,} thí sinh", f"{(so_hs_duoc_cuu/max(1, len(df))*100):.2f}% toàn quốc", f"Chính sách đã giúp {so_hs_duoc_cuu:,} học sinh chuyển từ TRƯỢT sang ĐỖ tốt nghiệp!"]
    ]
    # Đặt độ rộng 4 cột và đưa bảng dữ liệu vào khung đồ họa ax_table
    col_widths = [0.25, 0.18, 0.18, 0.39]
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.55)
    # Trang trí bảng: Tô màu xanh đậm cho hàng tiêu đề, các hàng dưới tô màu xám/trắng xen kẽ
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7')
        if row == 0: cell.set_facecolor('#1f618d'); cell.set_text_props(weight='bold', color='white')
        else: cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1,2] else 'normal', color='#27ae60' if col==2 and row==4 else ('#c0392b' if col==1 and row==4 else '#2c3e50'))
    # Hoàn thiện phần xuất đồ họa của bảng điều khiển
    plt.suptitle("BẢNG ĐIỀU KHIỂN CHÍNH SÁCH ƯU TIÊN & NGUYÊN NHÂN TRƯỢT - THPT QUỐC GIA 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()
    # =====================================================================
# TẦNG 2: PHÂN TÍCH CHUYÊN SÂU & HÀNH VI 
# =====================================================================

# --- NHÓM 7: PHÂN TÍCH GIỚI TÍNH 
def analyze_group7_gender_dashboard():
    """
    GIỚI TÍNH
    Tỷ lệ Điểm 10/Điểm & Tỷ lệ Đỗ tốt nghiệp chung.
    """
    df = get_all_data()
    if df.empty or 'gioi_tinh' not in df.columns: return
    print("\nĐang phân tích chuyên sâu Nhóm 7: Thế mạnh tri thức & Học lực theo Giới tính...")
    # Tiền xử lý data: Lọc lấy các hàng có chữ Nam/Nữ, cắt khoảng trắng và viết hoa chữ cái đầu (VD: 'nam' -> 'Nam')
    df_g = df[df['gioi_tinh'].astype(str).str.strip().isin(['Nam', 'Nữ', 'nam', 'nữ'])].copy()
    df_g['gioi_tinh'] = df_g['gioi_tinh'].astype(str).str.capitalize()

    # 1. Tính toán số liệu thống kê
    stats_list = []
    for g in ['Nam', 'Nữ']:
        sub = df_g[df_g['gioi_tinh'] == g]
        total = len(sub)
        if total == 0: continue
        # Tính các chỉ số cơ bản: Điểm TB, Tỷ lệ đỗ, Số lượng điểm 10, Tỷ lệ dính điểm liệt
        tb_4m = sub['diem_tb_4_mon'].mean()
        do_rate = (sub['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
        d10 = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] == 10).sum().sum()
        liet_rate = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] <= 1.0).any(axis=1).mean() * 100
        # Đóng gói kết quả tính được vào 1 danh sách
        stats_list.append({
            "Giới Tính": g, "Số Thí Sinh": f"{total:,} ({total/len(df_g)*100:.1f}%)",
            "Điểm TB 4 Môn": round(tb_4m, 2), "Tỷ Lệ Đỗ (%)": f"{do_rate:.1f}%",
            "Tổng Ca Điểm 10": f"{d10:,}", "Tỷ Lệ Điểm Liệt (%)": f"{liet_rate:.2f}%"
        })
    # In bảng thống kê chi tiết Nam vs Nữ ra màn hình Terminal
    print("\n" + "="*120)
    print(" BẢNG THỐNG KÊ CHUYÊN SÂU THEO GIỚI TÍNH (NAM vs NỮ) - THPT 2025")
    print("="*120)
    print(pd.DataFrame(stats_list).to_string(index=False))
    print("="*120 + "\n")

    # 2. Vẽ Super Dashboard
    # Thiết lập khung vẽ tổng: 2 hàng, 2 cột. Hàng trên chiếm diện tích gấp 2.2 lần hàng dưới.
    fig = plt.figure(figsize=(16, 9.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: BẢN ĐỒ THẾ MẠNH TRI THỨC NAM vs NỮ [CT 34] ---
    # Tạo danh sách tra cứu để đổi mã cột (VD: 'toan') thành Tên hiển thị (VD: 'Toán')
    subjects = [('toan', 'Toán'), ('ngu_van', 'Ngữ Văn'), ('vat_ly', 'Vật Lý'),
                ('hoa_hoc', 'Hóa Học'), ('sinh_hoc', 'Sinh Học'), ('lich_su', 'Lịch Sử'),
                ('dia_ly', 'Địa Lý'), ('ngoai_ngu', 'Ngoại Ngữ'), ('gdcd', 'GDCD')]
    # Lọc lấy những môn học có tồn tại trong bộ dữ liệu
    valid_subs = [c for c, _ in subjects if c in df_g.columns]
    # Gom nhóm theo Giới tính và tính Điểm trung bình của tất cả các môn học
    mean_by_g = df_g.groupby('gioi_tinh')[valid_subs].mean().reset_index()
    #Dùng hàm 'melt' để bẻ bảng dữ liệu từ dạng "Rộng" (mỗi môn 1 cột) sang dạng "Dài" (gom tất cả môn vào 1 cột tên là 'col') để Seaborn vẽ được
    melted = pd.melt(mean_by_g, id_vars=['gioi_tinh'], value_vars=valid_subs, var_name='col', value_name='Điểm TB')
    # Áp dụng danh sách tra cứu 'subjects' ở trên để đổi mã môn thành tên Tiếng Việt cho đẹp
    melted['Môn Thi'] = melted['col'].map(dict(subjects))
    # Vẽ biểu đồ cột đôi so sánh điểm số các môn học giữa Nam (Màu xanh) và Nữ (Màu hồng)
    sns.barplot(x='Môn Thi', y='Điểm TB', hue='gioi_tinh', data=melted, ax=ax1, palette=['#1f77b4', '#e377c2'], edgecolor='black', linewidth=0.7)
    # Căn chỉnh biểu đồ: Tiêu đề, tên trục X/Y, giới hạn trục Y từ 0-10, bảng chú giải giới tính
    ax1.set_title('[Chỉ tiêu 34] BẢN ĐỒ THẾ MẠNH TRI THỨC TỪNG MÔN: NAM vs NỮ', fontweight='bold', fontsize=12, color='#1a5276')
    ax1.set_xlabel("Môn thi tốt nghiệp THPT", fontweight='bold', fontsize=10); ax1.set_ylabel("Điểm trung bình (0 - 10)", fontweight='bold', fontsize=10)
    ax1.set_ylim(0, 10); ax1.legend(title="Giới tính", loc="upper right", frameon=True, facecolor='white')
    # Nghiêng chữ ở trục X (tên môn học) 15 độ để các chữ không bị đè lên nhau
    ax1.tick_params(axis='x', rotation=15)
    # Tự động ghi số điểm lên đỉnh các cột của biểu đồ bên trái (Bản đồ thế mạnh)
    for p in ax1.patches:
        h = p.get_height()
        if h > 0: ax1.annotate(f'{h:.2f}', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=8.5, fontweight='bold', xytext=(0, 2), textcoords='offset points')

    # --- BIỂU ĐỒ PHẢI: TỶ LỆ ĐIỂM 10 CỰC HẠN & ĐIỂM LIỆT [CT 35 & 36] ---
    comp_data = []
    # Tính toán 3 chỉ số: Tỷ lệ đỗ, Tỷ lệ điểm liệt, Mật độ điểm 10 cho từng giới tính
    for g in ['Nam', 'Nữ']:
        sub = df_g[df_g['gioi_tinh'] == g]
        do_pct = (sub['trang_thai'].astype(str).str.lower() == 'đỗ tốt nghiệp').mean() * 100
        liet_pct = (sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] <= 1.0).any(axis=1).mean() * 100
        # Mật độ điểm 10 = (Tổng số môn đạt 10 / Tổng số thí sinh) * 10
        d10_pct = ((sub[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']] == 10).sum().sum() / max(1, len(sub))) * 10
        # Gom dữ liệu vào danh sách
        comp_data.append({"Giới Tính": g, "Chỉ Số": "Tỷ Lệ Đỗ Tốt Nghiệp (%)\n", "Giá Trị": do_pct})
        comp_data.append({"Giới Tính": g, "Chỉ Số": "Mật Độ Đạt Điểm 10\n", "Giá Trị": d10_pct})
        comp_data.append({"Giới Tính": g, "Chỉ Số": "Nguy Cơ Dính Điểm Liệt (%)\n", "Giá Trị": liet_pct})
    df_comp = pd.DataFrame(comp_data)
    # Vẽ biểu đồ cột đôi so sánh các chỉ số giữa Nam và Nữ
    sns.barplot(x='Chỉ Số', y='Giá Trị', hue='Giới Tính', data=df_comp, ax=ax2, palette=['#1f77b4', '#e377c2'], edgecolor='black', linewidth=0.7)
    # Căn chỉnh tiêu đề, tên trục và bảng chú giải cho biểu đồ phải
    ax2.set_title('ĐỐI CHIẾU TỶ LỆ ĐỖ, ĐIỂM 10 CỰC HẠN & ĐIỂM LIỆT', fontweight='bold', fontsize=12, color='#922b21')
    ax2.set_xlabel(""); ax2.set_ylabel("Tỷ lệ % / Mật độ tương đối", fontweight='bold', fontsize=10)
    ax2.legend(title="Giới tính", loc="upper right", frameon=True, facecolor='white')
    # Tự động ghi số % lên đỉnh các cột của biểu đồ bên phải
    for p in ax2.patches:
        h = p.get_height()
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9, fontweight='bold', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, 115)

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # Tách riêng tập dữ liệu Nam và Nữ để đưa vào bảng
    sub_nam = df_g[df_g['gioi_tinh']=='Nam']; sub_nu = df_g[df_g['gioi_tinh']=='Nữ']
    # Khởi tạo dữ liệu bảng (Đã bọc lại hoàn chỉnh các chuỗi text bị thiếu)
    table_data = [
        ["Góc Nhìn Phân Tích Xã Hội Học", "Thí Sinh Nam (Male)", "Thí Sinh Nữ (Female)", "Kiểm Chứng Định Kiến & Đánh Giá Thực Tế"],
        ["Thế mạnh tri thức :", "Trội ở môn Toán, Vật Lý, Hóa Học", "Trội ở Ngữ Văn, Ngoại Ngữ, GDCD, Sử, Địa", "Đúng định kiến: Nam giỏi Khoa học Tự nhiên - Nữ áp đảo Ngôn ngữ & Xã hội!"],
        ["Điểm TB 4 môn thi :", f"{sub_nam['diem_tb_4_mon'].mean():.2f} điểm", f"{sub_nu['diem_tb_4_mon'].mean():.2f} điểm", f"Mặt bằng chung học lực Nữ giới nhỉnh hơn và vững vàng hơn Nam giới"],
        ["Mật độ Điểm 10 tuyệt đối [CT 35]:", f"{(sub_nam[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]==10).sum().sum():,} ca điểm 10", f"{(sub_nu[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]==10).sum().sum():,} ca điểm 10", "Nữ giới chiếm ưu thế trong các môn trắc nghiệm Xã hội và Ngoại ngữ"],
        ["Tỷ lệ dính Điểm liệt :", f"{(sub_nam[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", f"{(sub_nu[['toan','ngu_van','diem_tu_chon_1','diem_tu_chon_2']]<=1.0).any(axis=1).mean()*100:.2f}%", "Nam giới có tỷ lệ học lệch và rơi vào điểm liệt cao hơn Nữ giới đáng kể"]
    ]
    # Cài đặt bố cục và đưa dữ liệu vào khung đồ họa ax_table
    col_widths = [0.23, 0.22, 0.22, 0.33]
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.55)
    # Tô màu trang trí bảng: Hàng đầu màu đậm, các hàng sau đổi màu xám/trắng xen kẽ
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7')
        if row == 0: cell.set_facecolor('#2c3e50'); cell.set_text_props(weight='bold', color='white')
        else: cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1,2] else 'normal', color='#1f77b4' if col==1 else ('#e377c2' if col==2 else '#2c3e50'))
    # Đặt tiêu đề lớn nhất cho toàn bộ hình ảnh và xuất biểu đồ ra màn hình
    plt.suptitle("PHÂN TÍCH  GIỚI TÍNH (NAM vs NỮ) - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()


# --- NHÓM 8: XU HƯỚNG CHỌN MÔN TỰ CHỌN [CHỈ TIÊU 37, 38, 39] ---
def analyze_group8_electives_dashboard():
    """
    XU HƯỚNG CHỌN MÔN: Top 10 Tổ hợp Tự chọn Hot nhất ,
    Xu hướng Tự nhiên/Xã hội theo Vùng miền  & Chiến lược của Hệ GDTX vs GDPT .
    """
    df = get_all_data()
    # Bỏ qua nếu dữ liệu trống hoặc không có cột ghi nhận môn tự chọn
    if df.empty or 'mon_tu_chon_1' not in df.columns: return
    print("\nĐang phân tích Nhóm 8: Xu hướng đăng ký môn Tự chọn & Chiến lược làm bài...")
    # Lọc bỏ các học sinh bị thiếu dữ liệu (không chọn đủ 2 môn tự chọn)
    df_tc = df.dropna(subset=['mon_tu_chon_1', 'mon_tu_chon_2']).copy()
    # Ghép 2 môn tự chọn thành 1 chuỗi (VD: "Hóa học + Vật lý"). tránh bị lặp ngược thứ tự
    df_tc['combo'] = df_tc[['mon_tu_chon_1', 'mon_tu_chon_2']].apply(
        lambda x: " + ".join(sorted([str(x[0]).strip(), str(x[1]).strip()])), axis=1
    )
    # Đếm số lượng và lấy ra Top 10 tổ hợp được đăng ký nhiều nhất
    combo_counts = df_tc['combo'].value_counts().head(10)

    # Phân loại hướng Khối KHTN (Lý, Hóa, Sinh) vs KHXH (Sử, Địa, GDCD)
    khtn_names = ['Vật lý', 'Vật lí', 'Hóa học', 'Hóa', 'Sinh học', 'Sinh']
    khxh_names = ['Lịch sử', 'Sử', 'Địa lý', 'Địa lí', 'Địa', 'GDCD', 'Giáo dục công dân']
    
    # Kiểm tra xem cả 2 môn tự chọn của thí sinh có hoàn toàn nằm trong nhóm KHTN (hoặc KHXH) hay không
    df_tc['is_khtn'] = df_tc['mon_tu_chon_1'].isin(khtn_names) & df_tc['mon_tu_chon_2'].isin(khtn_names)
    df_tc['is_khxh'] = df_tc['mon_tu_chon_1'].isin(khxh_names) & df_tc['mon_tu_chon_2'].isin(khxh_names)

    # 1. In báo cáo Top 10 Combo ra Terminal
    print("\n" + "="*90)
    print("TOP 10 CẶP MÔN TỰ CHỌN 'HOT' NHẤT ĐƯỢC THÍ SINH ĐĂNG KÝ THPT 2025")
    print("="*90)
    # Gom dữ liệu thành bảng DataFrame, tạo thêm cột Tỷ lệ % và định dạng số lượng cho đẹp trước khi in ra
    df_combo_print = pd.DataFrame({"Tổ Hợp Cặp Môn Tự Chọn": combo_counts.index, "Số Thí Sinh": combo_counts.values})
    df_combo_print['Tỷ Lệ (%)'] = (df_combo_print['Số Thí Sinh'] / len(df_tc) * 100).round(1).astype(str) + "%"
    df_combo_print['Số Thí Sinh'] = df_combo_print['Số Thí Sinh'].apply(lambda x: f"{x:,}")
    print(df_combo_print.to_string(index=False))
    print("="*90 + "\n")

    # 2. Vẽ Super Dashboard
    # Khởi tạo khung hình và chia lưới 2 hàng x 2 cột
    fig = plt.figure(figsize=(16, 9.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.35, wspace=0.2)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: TOP 10 COMBO TỰ CHỌN HOT NHẤT [CT 37] ---
    # Vẽ biểu đồ thanh ngang (barplot) đếm số lượng Top 10 combo, dùng dải màu 'cubehelix'
    sns.barplot(x=combo_counts.values, y=combo_counts.index, ax=ax1, palette='cubehelix', edgecolor='black', linewidth=0.7)
    ax1.set_title('TOP 10 TỔ HỢP CẶP MÔN TỰ CHỌN ĐƯỢC YÊU THÍCH NHẤT', fontweight='bold', fontsize=12, color='#1a5276')
    ax1.set_xlabel("Số lượng thí sinh đăng ký", fontweight='bold', fontsize=10); ax1.set_ylabel("Tổ hợp 2 môn tự chọn", fontweight='bold', fontsize=10)
    ax1.set_xlim(0, combo_counts.max() * 1.3)

    # Tự động ghi số lượng và phần trăm vào đuôi mỗi thanh ngang
    for p in ax1.patches:
        w = p.get_width()
        if w > 0: ax1.annotate(f'{int(w):,} HS ({w/len(df_tc)*100:.1f}%)', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=9, fontweight='bold', xytext=(5, 0), textcoords='offset points')

    # --- BIỂU ĐỒ PHẢI: CHIẾN LƯỢC CHỌN MÔN HỆ GDTX vs GDPT [CT 39] ---
    # Tính tỷ lệ % thí sinh chọn khối KHTN và KHXH theo từng Hệ đào tạo
    sys_strat = df_tc.groupby('he_dao_tao').agg(
        khtn_pct=('is_khtn', lambda x: x.mean() * 100),
        khxh_pct=('is_khxh', lambda x: x.mean() * 100)
    ).reset_index()
    # Kỹ thuật bẻ bảng (melt): Ép 2 cột tỷ lệ thành 1 cột chung để Seaborn có thể vẽ biểu đồ cột đôi
    melted_strat = pd.melt(sys_strat, id_vars=['he_dao_tao'], value_vars=['khtn_pct', 'khxh_pct'], var_name='Khối', value_name='Tỷ Lệ (%)')
    melted_strat['Khối'] = melted_strat['Khối'].replace({'khtn_pct': 'Chuyên Tự Nhiên (Lý, Hóa, Sinh)', 'khxh_pct': 'Chuyên Xã Hội (Sử, Địa, GDCD)'})

    # Vẽ biểu đồ cột đứng so sánh chiến lược chọn môn
    sns.barplot(x='he_dao_tao', y='Tỷ Lệ (%)', hue='Khối', data=melted_strat, ax=ax2, palette=['#2980b9', '#e67e22'], edgecolor='black', linewidth=0.7)
    ax2.set_title('CHIẾN LƯỢC CHỌN MÔN: HỆ GDPT vs HỆ GDTX', fontweight='bold', fontsize=12, color='#922b21')
    ax2.set_xlabel("Mô hình hệ đào tạo", fontweight='bold', fontsize=10); ax2.set_ylabel("Tỷ lệ thí sinh lựa chọn (%)", fontweight='bold', fontsize=10)
    ax2.legend(title="Xu hướng khối thi", loc="upper right", frameon=True, facecolor='white', fontsize=9)
    # Tự động ghi số % lên đỉnh các cột
    for p in ax2.patches:
        h = p.get_height()
        if h > 0: ax2.annotate(f'{h:.1f}%', (p.get_x() + p.get_width() / 2., h), ha='center', va='bottom', fontsize=9.5, fontweight='bold', xytext=(0, 3), textcoords='offset points')
    ax2.set_ylim(0, 115)

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI [XU HƯỚNG VÙNG MIỀN - CT 38] ---
    # Nhóm dữ liệu theo Tỉnh/Thành, đếm tổng số thí sinh và tính tỷ lệ % chọn khối Tự nhiên (KHTN) / Xã hội (KHXH)
    prov_trend = df_tc.groupby('tinh_thanh').agg(
        tong=('sbd', 'count'), khtn=('is_khtn', lambda x: x.mean()*100), khxh=('is_khxh', lambda x: x.mean()*100)
    ).reset_index()
    # Tìm ra Tỉnh/Thành chuộng khối Tự nhiên nhất và chuộng khối Xã hội nhất 
    # (Lưu ý: Chỉ xét tỉnh có > 50 thí sinh để tránh bị nhiễu số liệu, sau đó xếp giảm dần và lấy vị trí số 0)
    top_khtn = prov_trend[prov_trend['tong']>50].sort_values(by='khtn', ascending=False).iloc[0]
    top_khxh = prov_trend[prov_trend['tong']>50].sort_values(by='khxh', ascending=False).iloc[0]
    
    # Khởi tạo dữ liệu bảng tổng hợp nhận định xu hướng chọn môn
    table_data = [
        ["Phân Tích Hành Vi Chọn Môn", "Số Liệu Thực Tế / Tỉ Lệ", "Nhận Định Xu hướng Xã hội & Giáo dục"],
        ["Cặp môn 'Quốc dân' Top 1 :", f"{combo_counts.index[0]} ({combo_counts.values[0]:,} HS)", "Tổ hợp dễ học, dễ đỗ tốt nghiệp và có phổ điểm ổn định nhất năm nay"],
        ["Tỉnh chuộng KHTN nhất :", f"Tỉnh {top_khtn['tinh_thanh']} ({top_khtn['khtn']:.1f}% học sinh chọn KHTN)", "Các địa phương truyền thống công nghiệp, chuộng các khối kỹ thuật, công nghệ (A00, A01, B00)"],
        ["Tỉnh chuộng KHXH nhất :", f"Tỉnh {top_khxh['tinh_thanh']} ({top_khxh['khxh']:.1f}% học sinh chọn KHXH)", "Các địa phương ưu tiên khối sư phạm, luật, hành chính, văn hóa xã hội (C00, D01)"],
        ["Chiến lược của học sinh GDTX :", f"{sys_strat[sys_strat['he_dao_tao']=='GDTX']['khxh_pct'].values[0]:.1f}% chọn thi trọn gói Khối Xã Hội", "Học sinh GDTX có xu hướng chọn Sử + Địa + GDCD để dễ học thuộc lòng, tối ưu cơ hội đỗ tốt nghiệp!"]
    ]

    # Vẽ bảng, căn chỉnh độ rộng cột và định dạng màu sắc xen kẽ
    col_widths = [0.26, 0.32, 0.42]
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='left', colWidths=col_widths)
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.55)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7')
        if row == 0: cell.set_facecolor('#1f618d'); cell.set_text_props(weight='bold', color='white')
        else: cell.set_facecolor('#f4f6f7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1] else 'normal', color='#d35400' if col==1 and row==1 else ('#27ae60' if col==1 and row==4 else '#2c3e50'))

    plt.suptitle("BẢNG ĐIỀU KHIỂN XU HƯỚNG CHỌN MÔN TỰ CHỌN & CHIẾN LƯỢC HỌC TẬP - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()

# --- NHÓM 9: CHÂN DUNG THỦ KHOA & ĐỈNH CAO TRI THỨC  ---
def analyze_group9_valedictorians_dashboard():
    """
    THỦ KHOA: Top 15 Thủ khoa 4 môn ,
    Thủ khoa 5 Khối Đại học .
    """
    df = get_all_data()
    if df.empty: return
    print("\nĐang tìm kiếm những Đỉnh cao Tri thức: Thủ khoa & Siêu nhân Đa điểm 10...")

    # 1. Thủ khoa thực lực 4 môn
    df['tong_4m_thuc_te'] = df[['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']].sum(axis=1)
    top_4m = df.sort_values(by='tong_4m_thuc_te', ascending=False).head(15)

    print("\n" + "="*125)
    print(" TOP 15 THỦ KHOA THỰC LỰC XUẤT SẮC NHẤT TOÀN QUỐC")
    print("="*125)
    cols_print = ['sbd', 'ho_ten', 'tinh_thanh', 'toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2', 'tong_4m_thuc_te']
    valid_cols = [c for c in cols_print if c in top_4m.columns]
    print(top_4m[valid_cols].rename(columns={'sbd':'SBD', 'ho_ten':'Họ và Tên', 'tinh_thanh':'Tỉnh/Thành', 'toan':'Toán', 'ngu_van':'Văn', 'diem_tu_chon_1':'TC 1', 'diem_tu_chon_2':'TC 2', 'tong_4m_thuc_te':'Tổng 4 Môn'}).to_string(index=False))
    print("="*125 + "\n")

    # 2. Vinh danh & 3. Siêu nhân Đa điểm 10 (Giữ nguyên in ra Terminal)
    score_cols = ['toan', 'ngu_van', 'diem_tu_chon_1', 'diem_tu_chon_2']
    valid_scores = [c for c in score_cols if c in df.columns]
    df['so_diem_10'] = (df[valid_scores] == 10.0).sum(axis=1)
    siu_nhan = df[df['so_diem_10'] >= 2].sort_values(by='so_diem_10', ascending=False)
    
    print(f" THÍ SINH 'SIÊU NHÂN' : Toàn quốc ghi nhận đúng [{len(siu_nhan):,} thí sinh] đạt từ 2 MÔN ĐIỂM 10 TRỞ LÊN!")
    if len(siu_nhan) > 0:
        print("     Top 5 bạn xuất sắc nhất: " + ", ".join([f"{r['ho_ten']} ({r['so_diem_10']} điểm 10 - {r['tinh_thanh']})" for _, r in siu_nhan.head(5).iterrows()]))
    print("\n")

    # 4. Vẽ Super Dashboard
    fig = plt.figure(figsize=(16, 9.5))
    # ĐÃ TĂNG hspace LÊN 0.45 ĐỂ BẢNG KHÔNG BỊ DÍNH VÀO BIỂU ĐỒ TRÊN NỮA
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1], hspace=0.45, wspace=0.55)
    ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :]); ax_table.axis('off')

    # --- BIỂU ĐỒ TRÁI: BẢN ĐỒ LÒ LUYỆN THỦ KHOA ---
    top_1000 = df.sort_values(by='diem_tb_4_mon', ascending=False).head(1000)
    prov_cradle = top_1000['tinh_thanh'].value_counts().head(15)

    # ĐÃ SỬA LỖI CẢNH BÁO SEABORN: Thêm hue và legend=False
    sns.barplot(x=prov_cradle.values, y=prov_cradle.index, ax=ax1, hue=prov_cradle.index, legend=False, palette='Reds_r', edgecolor='black', linewidth=0.7)
    ax1.set_title('BẢN ĐỒ "LÒ LUYỆN": TOP 15 TỈNH CÓ NHIỀU HS TRONG TOP 1.000 QG', fontweight='bold', fontsize=12, color='#922b21')
    ax1.set_xlabel("Số học sinh lọt vào Top 1.000 điểm cao nhất cả nước", fontweight='bold', fontsize=10); ax1.set_ylabel("Tỉnh / Thành phố", fontweight='bold', fontsize=10)
    ax1.set_xlim(0, prov_cradle.max() * 1.25)

    for p in ax1.patches:
        w = p.get_width()
        if w > 0: ax1.annotate(f'{int(w)} HS', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=9, fontweight='bold', xytext=(4, 0), textcoords='offset points')

    # --- BIỂU ĐỒ PHẢI: TOP 10 THỦ KHOA THỰC LỰC ---
    top10_plot = top_4m.head(10).copy()
    top10_plot['nhan'] = top10_plot['ho_ten'] + " (" + top10_plot['tinh_thanh'] + ")"

    # ĐÃ SỬA LỖI CẢNH BÁO SEABORN: Thêm hue và legend=False
    sns.barplot(x='tong_4m_thuc_te', y='nhan', data=top10_plot, ax=ax2, hue='nhan', legend=False, palette='viridis', edgecolor='black', linewidth=0.7)
    ax2.set_title('TOP 10 THỦ KHOA THỰC LỰC XUẤT SẮC NHẤT TOÀN QUỐC', fontweight='bold', fontsize=12, color='#1a5276')
    ax2.set_xlabel("Tổng điểm thực tế 4 môn thi (Thang 40 điểm)", fontweight='bold', fontsize=10); ax2.set_ylabel("")
    ax2.set_xlim(30, 40.5)
    ax2.tick_params(axis='y', labelsize=9)
    for p in ax2.patches:
        w = p.get_width()
        if w > 0: ax2.annotate(f'{w:.2f}đ', (w, p.get_y() + p.get_height() / 2.), ha='left', va='center', fontsize=9, fontweight='bold', xytext=(4, 0), textcoords='offset points')

    # --- BẢNG ĐỒ HỌA PHÍA DƯỚI ---
    # ĐÃ THÊM TIÊU ĐỀ CHO BẢNG SỐ LIỆU ĐỂ NHÌN KHÔNG BỊ TRỐNG TRƠN
    ax_table.set_title('VINH DANH THỦ KHOA CÁC KHỐI XÉT TUYỂN ĐẠI HỌC TRUYỀN THỐNG', fontweight='bold', fontsize=13, color='#d35400', pad=10)
    
    table_data = [["Khối Đại Học", "Thủ Khoa Toàn Quốc (Họ và Tên)", "Số Báo Danh", "Tỉnh / Thành Phố", "Tổng Điểm Khối (Max 30)"]]
    for b, desc in [('A00', 'Toán-Lý-Hóa'), ('A01', 'Toán-Lý-Anh'), ('B00', 'Toán-Hóa-Sinh'), ('C00', 'Văn-Sử-Địa'), ('D01', 'Toán-Văn-Anh')]:
        if b in df.columns:
            r = df.sort_values(by=b, ascending=False).iloc[0]
            # ĐÃ SỬA LỖI MẤT SỐ 0 Ở ĐẦU CỦA SỐ BÁO DANH
            try:
                sbd_str = str(int(float(r['sbd']))).zfill(8)
            except:
                sbd_str = str(r['sbd'])
            table_data.append([f"Khối {b} ({desc})", r['ho_ten'], sbd_str, r['tinh_thanh'], f"{r[b]:.2f} điểm"])

    col_widths = [0.20, 0.28, 0.14, 0.18, 0.20]
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center', colWidths=col_widths)
    # Giảm scale nhẹ lại từ 1.55 xuống 1.45 để giao diện gọn gàng hơn
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.45) 

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#bdc3c7')
        if row == 0: cell.set_facecolor('#d35400'); cell.set_text_props(weight='bold', color='white')
        else: cell.set_facecolor('#fef9e7' if row%2==1 else '#ffffff'); cell.set_text_props(weight='bold' if col in [0,1,4] else 'normal', color='#922b21' if col==4 else '#2c3e50')

    plt.suptitle("THỦ KHOA - THPT 2025", fontsize=15, fontweight='bold', color='#1a5276', y=0.98)
    plt.show()
