"""Nhãn cảnh báo cho cơ sở dữ liệu minh họa được xác định rõ nguồn."""
import tkinter as tk

from database.db_connection import is_sample_data


def show_sample_banner(parent):
    if is_sample_data():
        tk.Label(parent, text="DỮ LIỆU MẪU GIẢ LẬP — KHÔNG PHẢI KẾT QUẢ THI THẬT",
                 font=("Arial", 10, "bold"), bg="#fff3cd", fg="#7a4c00",
                 pady=5).pack(fill=tk.X)
