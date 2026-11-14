"""XacThucService — UC04 Đăng nhập, đổi mật khẩu (module M6)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import NghiepVuError, bam, bi_khoa_tam, ghi_sai, kiem_tra_bam, so_lan_con, xoa_sai, yeu_cau


def dang_nhap(db: Session, ten: str, mat_khau: str) -> M.TaiKhoan:
    ten = (ten or "").strip().lower()
    khoa = "dn:" + ten
    yeu_cau(not bi_khoa_tam(khoa), "Đăng nhập sai quá 5 lần. Vui lòng thử lại sau 15 phút.")
    tk = db.scalar(select(M.TaiKhoan).where(M.TaiKhoan.TenDangNhap == ten))
    if not tk or not kiem_tra_bam(mat_khau or "", tk.MatKhauBam):
        ghi_sai(khoa)
        raise NghiepVuError("Sai tên đăng nhập hoặc mật khẩu (còn %d lần thử)." % max(so_lan_con(khoa), 0))
    yeu_cau(tk.TrangThai == TT.TK_HOAT_DONG, "Tài khoản đang bị khóa. Vui lòng liên hệ cán bộ quản lý.")
    xoa_sai(khoa)
    tk.LanDangNhapCuoi = now()
    db.commit()
    return tk


def doi_mat_khau(db: Session, tk: M.TaiKhoan, cu: str, moi: str, nhap_lai: str):
    yeu_cau(kiem_tra_bam(cu or "", tk.MatKhauBam), "Mật khẩu hiện tại không đúng.")
    yeu_cau(moi and len(moi) >= 8, "Mật khẩu mới phải có ít nhất 8 ký tự.")
    yeu_cau(any(c.isdigit() for c in moi) and any(c.isalpha() for c in moi), "Mật khẩu mới phải có cả chữ và số.")
    yeu_cau(moi == nhap_lai, "Nhập lại mật khẩu không khớp.")
    yeu_cau(moi != cu, "Mật khẩu mới phải khác mật khẩu cũ.")
    tk.MatKhauBam = bam(moi)
    tk.PhaiDoiMatKhau = False
    db.commit()


def ten_hien_thi(tk: M.TaiKhoan) -> str:
    if tk.MaCanBo:
        return tk.can_bo.HoTen
    return tk.don_vi.TenDonVi
