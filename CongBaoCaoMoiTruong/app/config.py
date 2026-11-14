"""Cấu hình hệ thống, đọc từ tệp .env ở thư mục gốc dự án."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env():
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if v.strip():  # bỏ qua dòng để trống giá trị -> dùng mặc định
            os.environ.setdefault(k.strip(), v.strip())


_load_env()

# Chuỗi kết nối SQLAlchemy. Mặc định: SQL Server Express trên máy, đăng nhập bằng Windows.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mssql+pyodbc://@localhost\\SQLEXPRESS/CongBaoCaoMoiTruong"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes",
)
SECRET_KEY = os.environ.get("SECRET_KEY", "doi-chuoi-bi-mat-nay-khi-trien-khai")

UPLOAD_DIR = BASE_DIR / os.environ.get("UPLOAD_DIR", "uploads")
UPLOAD_TMP = UPLOAD_DIR / "tam"          # vùng tải lên tạm (M3)
UPLOAD_EVIDENCE = UPLOAD_DIR / "bang_chung"  # vùng bằng chứng lâu dài (M3)


# Gửi email mã báo cáo (Gmail). Để trống SMTP_USER/SMTP_PASSWORD thì hệ thống không gửi thư.
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_TLS = os.environ.get("SMTP_TLS", "1") not in ("0", "false", "False")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")   # mật khẩu ứng dụng Google có thể dán kèm dấu cách
SMTP_TEN_GUI = os.environ.get("SMTP_TEN_GUI", "Cổng báo cáo sự cố môi trường")
DIA_CHI_WEB = os.environ.get("DIA_CHI_WEB", "http://localhost:8000")   # gắn vào đường dẫn tra cứu trong thư

# Bản đồ (M2)
MAP_CENTER_LAT = float(os.environ.get("MAP_CENTER_LAT", "10.7500"))
MAP_CENTER_LNG = float(os.environ.get("MAP_CENTER_LNG", "106.6500"))

PAGE_SIZE = 10   # số dòng mỗi trang cho mọi danh sách
