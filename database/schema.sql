-- ====================================================================
-- HỆ THỐNG TRA CỨU VÀ PHÂN TÍCH ĐIỂM THI THPT (CHUYÊN BIỆT CHO MYSQL)
-- File: database/schema.sql
-- ====================================================================

-- 1. Xóa bảng cũ nếu tồn tại
DROP TABLE IF EXISTS students; 
DROP TABLE IF EXISTS admins;

-- ====================================================================
-- BẢNG 1: ADMINS (Lưu tài khoản của Quản trị viên)
-- ====================================================================
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- Dùng AUTO_INCREMENT chuẩn của MySQL
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- BẢNG 2: STUDENTS (Lưu 1 triệu dòng dữ liệu thí sinh)
-- ====================================================================
CREATE TABLE students (
    sbd VARCHAR(15) PRIMARY KEY,
    ho_ten VARCHAR(100) NOT NULL,
    ngay_sinh VARCHAR(15),
    gioi_tinh VARCHAR(10),
    cccd VARCHAR(20),
    tinh_thanh VARCHAR(50) NOT NULL,
    
    -- Điểm các môn học
    toan FLOAT,
    ngu_van FLOAT,
    mon_tu_chon_1 VARCHAR(30),
    diem_tu_chon_1 FLOAT,
    mon_tu_chon_2 VARCHAR(30),
    diem_tu_chon_2 FLOAT,
    
    -- Thông tin ưu tiên & Khuyến khích
    khu_vuc_uu_tien VARCHAR(15),
    doi_tuong_uu_tien VARCHAR(10),
    diem_uu_tien FLOAT DEFAULT 0,
    diem_khuyen_khich FLOAT DEFAULT 0,
    
    -- Phân loại & Kết quả
    he_dao_tao VARCHAR(20),
    nam_tot_nghiep INT DEFAULT 2025,
    ma_hoi_dong VARCHAR(10),
    tong_diem FLOAT,
    diem_trung_binh FLOAT,
    trang_thai VARCHAR(30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 3. TẠO CHỈ MỤC (INDEX) - TỐI ƯU TỐC ĐỘ TRUY VẤN
-- ====================================================================
CREATE INDEX idx_student_cccd ON students(cccd);
CREATE INDEX idx_tinh_thanh ON students(tinh_thanh);
CREATE INDEX idx_phan_loai ON students(he_dao_tao, trang_thai);
CREATE INDEX idx_diem_tb ON students(diem_trung_binh DESC);

-- ====================================================================
-- 4. TẠO SẴN DỮ LIỆU MẪU CHO ADMIN
-- ====================================================================
INSERT INTO admins (username, password_hash, full_name, role) 
VALUES ('admin', 'admin123', 'Quản Trị Viên Hệ Thống', 'admin');