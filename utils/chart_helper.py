import os
import matplotlib.pyplot as plt
import pandas as pd
 
class ChartHelper:
    @staticmethod
    def setup_vietnamese_font():
        """Cấu hình Font chữ chuẩn tiếng Việt cho Matplotlib."""
        # Fix lỗi hiển thị ô vuông khi gõ tiếng Việt có dấu trên tiêu đề/trục biểu đồ
        plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans', 'Times New Roman']
        # Fix lỗi tàng hình dấu trừ (-) của số âm trên trục tọa độ
        plt.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def add_value_labels_to_bars(ax, is_percentage=False, float_decimals=2):
        """Tự động ghi số liệu lên đỉnh các cột trong biểu đồ Bar Chart."""
        for p in ax.patches: # Quét qua từng hình khối (cột) đang vẽ trong biểu đồ
            height = p.get_height() # Lấy chiều cao của cột (chính là giá trị số cần ghi)
            if height > 0: # Chỉ ghi số lên những cột có giá trị thực tế > 0
                # Định dạng chữ số: Thêm % nếu là phần trăm, hoặc định dạng dấu phẩy hàng nghìn, số thập phân
                val_str = f"{height:.{float_decimals}f}%" if is_percentage else f"{int(height):,}" if float_decimals==0 else f"{height:.{float_decimals}f}"
                ax.annotate(val_str,
                            xy=(p.get_x() + p.get_width() / 2, height), # Tọa độ mục tiêu: Nằm giữa chiều ngang và đúng trên đỉnh cột
                            xytext=(0, 5),  # Dịch chữ nhích lên trên 5 pixel cho thoáng, tránh đè lên vạch cột
                            textcoords="offset points", # Tính tọa độ dịch chuyển bằng đơn vị pixel
                            ha='center', va='bottom', fontweight='bold', fontsize=10) # Căn giữa, neo đáy chữ, in đậm, cỡ chữ 10

    @staticmethod
    def export_dataframe_to_csv(df, file_name, folder="output_report"):
        """Xuất bảng dữ liệu Pandas ra file CSV report để lưu trữ hoặc gửi báo cáo."""
        if not os.path.exists(folder): # Kiểm tra xem thư mục đã tồn tại trên máy chưa
            os.makedirs(folder) # Nếu chưa có thì tự động tạo thư mục mới
        # Nối tên thư mục và tên file thành đường dẫn hoàn chỉnh (VD: output_report\ten_file.csv)
        
        file_path = os.path.join(folder, f"{file_name}.csv")
        try:
            # Xuất file CSV. index=False để bỏ cột số thứ tự. 
            # ĐẶC BIỆT: utf-8-sig giúp mở file bằng Excel không bị lỗi font tiếng Việt!
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"Đã xuất báo cáo thành công tại: {file_path}")
            return True
        except Exception as e:
            print(f"Lỗi khi xuất báo cáo: {e}") # Bắt lỗi nếu quá trình lưu bị cản trở (VD: file đang mở ở phần mềm khác, đầy ổ cứng)
            return False