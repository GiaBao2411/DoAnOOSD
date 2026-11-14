"""DanhMucService — UC09 Quản lý danh mục (module M4). BR16: không xóa, chỉ ngừng sử dụng."""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import text_req, yeu_cau



def ds_loai(db, chi_dang_dung=False):
    s = select(M.LoaiSuCo).order_by(M.LoaiSuCo.MaLoai)
    return db.scalars(s.where(M.LoaiSuCo.DangSuDung == True) if chi_dang_dung else s).all()  # noqa


def ds_dia_ban(db, chi_dang_dung=False):
    s = select(M.DiaBan).order_by(M.DiaBan.TenDiaBan)
    return db.scalars(s.where(M.DiaBan.DangSuDung == True) if chi_dang_dung else s).all()  # noqa


def ds_don_vi(db, chi_dang_dung=False):
    s = select(M.DonViXuLy).order_by(M.DonViXuLy.TenDonVi)
    return db.scalars(s.where(M.DonViXuLy.DangSuDung == True) if chi_dang_dung else s).all()  # noqa


def ds_tham_so(db):
    return db.scalars(select(M.ThamSoHeThong).order_by(M.ThamSoHeThong.MaThamSo)).all()


def _trung(db, model, cot, gia_tri, ma_cot, ma):
    s = select(func.count()).select_from(model).where(func.lower(cot) == gia_tri.lower())
    if ma:
        s = s.where(ma_cot != int(ma))
    return db.scalar(s) > 0


def luu_loai(db: Session, ma, ten, mo_ta, dang_dung):
    ten = text_req(ten, "tên loại sự cố", 100)
    yeu_cau(not _trung(db, M.LoaiSuCo, M.LoaiSuCo.TenLoai, ten, M.LoaiSuCo.MaLoai, ma), "Tên loại sự cố đã tồn tại.")
    o = db.get(M.LoaiSuCo, int(ma)) if ma else M.LoaiSuCo()
    yeu_cau(o, "Không tìm thấy loại sự cố.")
    o.TenLoai, o.MoTa, o.DangSuDung = ten, (mo_ta or "").strip()[:500] or None, bool(dang_dung)
    db.add(o)
    db.commit()


def luu_dia_ban(db: Session, ma, ten, tinh, dang_dung):
    ten = text_req(ten, "tên phường/xã", 100)
    tinh = text_req(tinh, "tỉnh/thành phố", 100)
    yeu_cau(not _trung(db, M.DiaBan, M.DiaBan.TenDiaBan, ten, M.DiaBan.MaDiaBan, ma), "Phường/xã đã tồn tại.")
    o = db.get(M.DiaBan, int(ma)) if ma else M.DiaBan()
    yeu_cau(o, "Không tìm thấy địa bàn.")
    o.TenDiaBan, o.TinhThanh, o.DangSuDung = ten, tinh, bool(dang_dung)
    db.add(o)
    db.commit()


def luu_don_vi(db: Session, ma, ten, ma_dia_ban, dia_chi, sdt, dang_dung):
    ten = text_req(ten, "tên đơn vị", 150)
    yeu_cau(not _trung(db, M.DonViXuLy, M.DonViXuLy.TenDonVi, ten, M.DonViXuLy.MaDonVi, ma), "Tên đơn vị đã tồn tại.")
    o = db.get(M.DonViXuLy, int(ma)) if ma else M.DonViXuLy()
    yeu_cau(o, "Không tìm thấy đơn vị.")
    o.TenDonVi, o.MaDiaBan = ten, int(ma_dia_ban) if ma_dia_ban else None
    o.DiaChi, o.SoDienThoai = (dia_chi or "").strip()[:200] or None, (sdt or "").strip()[:15] or None
    o.DangSuDung = bool(dang_dung)
    db.add(o)
    db.commit()


def luu_tham_so(db: Session, ma, gia_tri, tk):
    ts = db.get(M.ThamSoHeThong, ma)
    yeu_cau(ts, "Không tìm thấy tham số.")
    try:
        v = int(str(gia_tri).strip())
    except ValueError:
        v = 0
    yeu_cau(v > 0, "Giá trị tham số phải là số nguyên dương.")
    ts.GiaTri, ts.MaCanBoCapNhat, ts.NgayCapNhat = str(v), tk.MaCanBo, now()
    db.commit()
