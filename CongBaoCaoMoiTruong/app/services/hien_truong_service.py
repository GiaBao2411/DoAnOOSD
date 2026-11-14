import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from . import luu_tru_tep_service as LT
from .common import chuyen_trang_thai, phan_trang, text_req, yeu_cau


def nhiem_vu_cua_don_vi(db: Session, tk: M.TaiKhoan, chi_dang_lam=True, trang=1):
    P = M.PhanCongXuLy
    stmt = select(P).where(P.MaDonVi == tk.MaDonVi)
    if chi_dang_lam:
        stmt = stmt.where(P.TrangThai.in_(TT.PC_HIEU_LUC))
    return phan_trang(db, stmt.order_by(P.NgayPhanCong, P.MaPhanCong), trang)


def nhiem_vu_dang_xu_ly(db: Session, tk: M.TaiKhoan):
    P = M.PhanCongXuLy
    return db.scalars(select(P).where(P.MaDonVi == tk.MaDonVi, P.TrangThai == TT.PC_DANG_XU_LY)
                      .order_by(P.NgayPhanCong, P.MaPhanCong)).all()


def lay_nhiem_vu(db: Session, ma_pc, tk: M.TaiKhoan) -> M.PhanCongXuLy:
    pc = db.get(M.PhanCongXuLy, int(ma_pc))
    yeu_cau(pc and pc.MaDonVi == tk.MaDonVi, "Nhiệm vụ không thuộc đơn vị của bạn.")
    return pc


def nhan_nhiem_vu(db: Session, ma_pc, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_CHO_TIEP_NHAN, "Nhiệm vụ không ở trạng thái Chờ tiếp nhận.")
    pc.TrangThai, pc.NgayTiepNhan = TT.PC_DANG_XU_LY, now()
    chuyen_trang_thai(db, pc.bao_cao, TT.BC_DANG_XU_LY, tk.MaTaiKhoan, "%s nhận nhiệm vụ" % pc.don_vi.TenDonVi)
    db.commit()


def tra_lai(db: Session, ma_pc, ly_do, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_CHO_TIEP_NHAN, "Chỉ trả lại nhiệm vụ khi chưa nhận.")
    pc.LyDoTraLai = text_req(ly_do, "lý do trả lại", 500)
    pc.TrangThai = TT.PC_BI_TRA_LAI
    chuyen_trang_thai(db, pc.bao_cao, TT.BC_CHO_PHAN_CONG, tk.MaTaiKhoan,
                      "%s trả lại: %s" % (pc.don_vi.TenDonVi, pc.LyDoTraLai))
    db.commit()


def _so(s):
    try:
        return round(float(s), 6) if s not in (None, "") else None
    except ValueError:
        return None


def khoang_cach_m(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return int(2 * r * math.asin(math.sqrt(a)))


def luu_cap_nhat(db: Session, pc, tk, loai, noi_dung, tep_tai_len, giai_doan, phan_tram=None, vi_do=None, kinh_do=None):
    teps = LT.tai_len_tam(db, tep_tai_len)
    da_chuyen = []
    try:
        t = now()
        cn = M.CapNhatXuLy(MaPhanCong=pc.MaPhanCong, MaTaiKhoan=tk.MaTaiKhoan, LoaiCapNhat=loai, ThoiGian=t,
                           PhanTramTienDo=phan_tram, NoiDung=noi_dung, ViDo=_so(vi_do), KinhDo=_so(kinh_do))
        db.add(cn)
        db.flush()
        for tep in teps:
            p = LT.chuyen_sang_lau_dai(tep)
            da_chuyen.append(p)
            db.add(M.MinhChungXuLy(MaCapNhat=cn.MaCapNhat, GiaiDoan=giai_doan, TenTep=tep.ten_goc, LoaiTep=tep.loai,
                                   DuongDan=p, NgayTaiLen=t))
        return cn, teps, da_chuyen
    except Exception:
        LT.xoa_tam(teps)
        LT.xoa_lau_dai(da_chuyen)
        raise


def ghi_nhan_hien_truong(db: Session, ma_pc, nhan_xet, vi_do, kinh_do, tep_tai_len, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_DANG_XU_LY, "Hãy nhận nhiệm vụ trước khi ghi nhận hiện trường.")
    nhan_xet = text_req(nhan_xet, "nhận xét hiện trường")
    _, teps, da = luu_cap_nhat(db, pc, tk, TT.CN_GHI_NHAN, nhan_xet, tep_tai_len, TT.GD_TRUOC, vi_do=vi_do, kinh_do=kinh_do)
    try:
        db.commit()
    except Exception:
        db.rollback()
        LT.xoa_lau_dai(da)
        raise


def bao_khong_co_su_co(db: Session, ma_pc, nhan_xet, vi_do, kinh_do, tep_tai_len, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_DANG_XU_LY, "Hãy nhận nhiệm vụ trước.")
    nhan_xet = text_req(nhan_xet, "nhận xét hiện trường")
    yeu_cau([u for u in (tep_tai_len or []) if getattr(u, "filename", "")],
            "Báo không có sự cố phải kèm ít nhất một ảnh tại địa điểm (BR10).")
    _, teps, da = luu_cap_nhat(db, pc, tk, TT.CN_KHONG_SU_CO, nhan_xet, tep_tai_len, TT.GD_TRUOC, vi_do=vi_do, kinh_do=kinh_do)
    try:
        pc.TrangThai = TT.PC_CHO_NGHIEM_THU
        chuyen_trang_thai(db, pc.bao_cao, TT.BC_CHO_NGHIEM_THU, tk.MaTaiKhoan, "Đơn vị báo không có sự cố")
        db.commit()
    except Exception:
        db.rollback()
        LT.xoa_lau_dai(da)
        raise
