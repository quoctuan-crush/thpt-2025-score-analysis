import pymysql # Nhập thư viện để làm việc và giao tiếp với cơ sở dữ liệu MySQL
from database.db_connection import get_connection

class AuthController:
    @staticmethod
    def login_student(sbd, cccd_or_dob=None):
        """
        Tra cứu thí sinh bằng SBD.
        QUAN TRỌNG: Dùng 'SELECT *' để hút TOÀN BỘ điểm số và thông tin từ MySQL
        gửi lên cho StudentDashboard hiển thị!
        """
        #. KẾT NỐI CƠ SỞ DỮ LIỆU
        # Gọi hàm kết nối DB, nếu lỗi mạng/DB sập thì báo lỗi và thoát luôn
        conn = get_connection() # Gọi hàm để mở kết nối đến Database
        if not conn:# Kiểm tra xem kết nối có thành công không (nếu conn bị rỗng)
            print("[AUTH ERROR] Không thể kết nối cơ sở dữ liệu!")
            return None # Trả về None báo hiệu đăng nhập thất bại
            
        try:
            with conn.cursor() as cursor:
                # TRUY VẤN TÌM KIẾM THÍ SINH
                # Quét bảng 'students', tìm người có Số báo danh (sbd) khớp với dữ liệu nhập vào. Chỉ lấy 1 người (LIMIT 1)
                # Dùng SELECT * để lấy sạch không sót một cột điểm nào (Toán, Văn, Tự chọn...)
                query = "SELECT * FROM students WHERE sbd = %s LIMIT 1"
                cursor.execute(query, (str(sbd).strip(),))
                student = cursor.fetchone()
                
                if student:
                    # CẤP QUYỀN TRUY CẬP CHO HỌC SINH
                    # Chuyển dữ liệu lấy được thành dạng Từ điển (Dict) để dễ xài, sau đó dán nhãn quyền là 'STUDENT'
                    # Chuyển đổi dữ liệu thành Dict và gán nhãn vai trò là STUDENT
                    student_data = dict(student)
                    student_data['role'] = 'STUDENT'
                    return student_data
                else:
                    return None
        except Exception as e:
            # Bắt và in ra lỗi nếu câu lệnh SQL chạy sai
            print(f"[AUTH ERROR] Lỗi tra cứu SQL: {e}")
            return None
        finally:
            # Luôn luôn đóng cửa kết nối Database sau khi làm xong để giải phóng bộ nhớ
            conn.close()

    @staticmethod
    def login_admin(username, password):
        """
        Đăng nhập dành cho Quản trị viên (Admin)
        """
        # KIỂM TRA TÀI KHOẢN "CỨNG" (MẶC ĐỊNH)
        # Cho phép đăng nhập nhanh bằng tài khoản admin/admin123 mà không cần chọc vào Database
        # Kiểm tra tài khoản mặc định (admin / admin123)
        if str(username).strip() == "admin" and str(password).strip() == "admin123":
            return {
                "role": "ADMIN",
                "username": "admin",
                "full_name": "Quản Trị Viên Hệ Thống"
            }
            
        # KIỂM TRA TÀI KHOẢN TRONG DATABASE
        # Nếu nhập không đúng tài khoản mặc định, tiến hành dò tiếp trong bảng 'admins' của MySQL
        # Nếu muốn kiểm tra thêm trong bảng 'admins' của MySQL (nếu có)
        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Tìm kiếm chính xác dòng có chứa cả username và password vừa nhập
                    query = "SELECT * FROM admins WHERE username = %s AND password_hash = %s LIMIT 1"
                    cursor.execute(query, (str(username).strip(), str(password).strip()))
                    admin = cursor.fetchone()
                    if admin:
                        # Cấp quyền đăng nhập: Dán nhãn vai trò là 'ADMIN'
                        admin_data = dict(admin)
                        admin_data['role'] = 'ADMIN'
                        return admin_data
            except Exception:
                pass # Bỏ qua nếu có lỗi ngầm
            finally:
                conn.close() # Đóng kết nối

        # Trả về Không có gì (None) nếu sai cả 2 bước trên (Tức là đăng nhập thất bại)        
        return None
