"""TaiKhoanService — UC10 Quản lý tài khoản đơn vị xử lý (module M6). BR16: không xóa tài khoản, chỉ khóa."""
import re
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from .common import bam, text_req, yeu_cau


def ds_tai_khoan(db: Session, tu_khoa=None):
    """Danh sách tài khoản đơn vị xử lý (hệ thống chỉ có một cán bộ quản lý, không quản lý tài khoản cán bộ ở đây)."""
    s = select(M.TaiKhoan).where(M.TaiKhoan.LoaiTaiKhoan == TT.TK_DON_VI).order_by(M.TaiKhoan.TenDangNhap)
    if tu_khoa:
        s = s.where(M.TaiKhoan.TenDangNhap.like("%%%s%%" % tu_khoa.strip().lower()))
    return db.scalars(s).all()


def _tk_don_vi(db: Session, ma_tk):
    tk = db.get(M.TaiKhoan, int(ma_tk))
    yeu_cau(tk and tk.LoaiTaiKhoan == TT.TK_DON_VI, "Không tìm thấy tài khoản đơn vị.")
    return tk


def _mat_khau_tam():
    chu = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz"
    so = "23456789"
    mk = [secrets.choice(chu) for _ in range(6)] + [secrets.choice(so) for _ in range(2)]
    secrets.SystemRandom().shuffle(mk)
    return "".join(mk)


def them(db: Session, ten_dang_nhap, ma_don_vi):
    """Cấp tài khoản cho một đơn vị xử lý. Trả về (tài khoản, mật khẩu tạm)."""
    ten = text_req(ten_dang_nhap, "tên đăng nhập", 50).lower()
    yeu_cau(re.fullmatch(r"[a-z0-9._]{3,50}", ten), "Tên đăng nhập chỉ gồm chữ thường không dấu, số, dấu chấm, gạch dưới (3–50 ký tự).")
    yeu_cau(not db.scalar(select(M.TaiKhoan).where(M.TaiKhoan.TenDangNhap == ten)), "Tên đăng nhập đã tồn tại.")
    dv = db.get(M.DonViXuLy, int(ma_don_vi)) if ma_don_vi else None
    yeu_cau(dv, "Vui lòng chọn đơn vị sở hữu tài khoản.")
    mk = _mat_khau_tam()
    tk = M.TaiKhoan(TenDangNhap=ten, MatKhauBam=bam(mk), LoaiTaiKhoan=TT.TK_DON_VI, MaDonVi=dv.MaDonVi,
                    TrangThai=TT.TK_HOAT_DONG, PhaiDoiMatKhau=True)
    db.add(tk)
    db.commit()
    return tk, mk


def doi_trang_thai(db: Session, ma_tk, tk_dang_nhap):
    tk = _tk_don_vi(db, ma_tk)
    tk.TrangThai = TT.TK_BI_KHOA if tk.TrangThai == TT.TK_HOAT_DONG else TT.TK_HOAT_DONG
    db.commit()
    return tk


def dat_lai_mat_khau(db: Session, ma_tk):
    tk = _tk_don_vi(db, ma_tk)
    mk = _mat_khau_tam()
    tk.MatKhauBam, tk.PhaiDoiMatKhau = bam(mk), True
    db.commit()
    return tk, mk
