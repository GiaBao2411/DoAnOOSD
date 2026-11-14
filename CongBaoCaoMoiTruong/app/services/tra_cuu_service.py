from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from .common import phan_trang


def tim_theo_ma(db: Session, ma_tra_cuu: str):
    ma = (ma_tra_cuu or "").strip().upper()
    if not ma:
        return None
    return db.scalar(select(M.BaoCaoSuCo).where(M.BaoCaoSuCo.MaTraCuu == ma))


def ban_cong_khai(db: Session, ma_bao_cao: int):
    return db.scalar(select(M.KiemDuyet).where(M.KiemDuyet.MaBaoCao == ma_bao_cao, M.KiemDuyet.DangHienThi == True))


def anh_cong_khai(bc: M.BaoCaoSuCo):
    out = [("Ảnh người dân gửi", "bc", m.MaMinhChung, m.LoaiTep) for m in bc.minh_chung if m.DuocCongKhai]
    for pc in bc.phan_cong:
        for cn in pc.cap_nhat:
            for m in cn.minh_chung:
                if m.DuocCongKhai:
                    out.append(("Ảnh %s xử lý" % m.GiaiDoan.lower(), "xl", m.MaMinhChung, m.LoaiTep))
    return out


def du_lieu_cong_khai(db: Session, bc: M.BaoCaoSuCo):
    kd = ban_cong_khai(db, bc.MaBaoCao) if bc.TrangThai == TT.BC_HOAN_TAT else None
    trang_thai_hien_thi = bc.TrangThai
    if bc.TrangThai == TT.BC_CHO_BO_SUNG:
        trang_thai_hien_thi = TT.BC_DANG_XEM_XET + " (đang chờ người gửi bổ sung)"
    buoc_hien_tai = TT.BC_BUOC.index(bc.TrangThai) if bc.TrangThai in TT.BC_BUOC else (
        1 if bc.TrangThai == TT.BC_CHO_BO_SUNG else -1)
    cap_nhat_cuoi = bc.lich_su[-1].ThoiGian if bc.lich_su else bc.NgayGui
    return dict(bc=bc, kd=kd, anh=anh_cong_khai(bc) if kd else [], trang_thai=trang_thai_hien_thi,
                buoc=TT.BC_BUOC, buoc_hien_tai=buoc_hien_tai, cap_nhat_cuoi=cap_nhat_cuoi,
                ket_thuc=bc.TrangThai in (TT.BC_BI_TU_CHOI, TT.BC_DA_DONG))


def ban_do_cong_khai(db: Session, ma_loai=None, ma_dia_ban=None):
    stmt = (select(M.BaoCaoSuCo, M.KiemDuyet)
            .join(M.KiemDuyet, (M.KiemDuyet.MaBaoCao == M.BaoCaoSuCo.MaBaoCao) & (M.KiemDuyet.DangHienThi == True))
            .where(M.BaoCaoSuCo.TrangThai == TT.BC_HOAN_TAT))
    if ma_loai:
        stmt = stmt.where(M.BaoCaoSuCo.MaLoai == int(ma_loai))
    if ma_dia_ban:
        stmt = stmt.where(M.BaoCaoSuCo.MaDiaBan == int(ma_dia_ban))
    return db.execute(stmt.order_by(M.KiemDuyet.ThoiGian.desc())).all()


def tim_noi_bo(db: Session, ma=None, trang_thai=None, ma_loai=None, ma_dia_ban=None, tu=None, den=None, trang=1):
    stmt = select(M.BaoCaoSuCo)
    if ma:
        stmt = stmt.where(or_(M.BaoCaoSuCo.MaTraCuu.like("%%%s%%" % ma.strip().upper()),
                              M.BaoCaoSuCo.MoTa.like("%%%s%%" % ma.strip())))
    if trang_thai == TT.LOC_O_DON_VI:
        stmt = stmt.where(M.BaoCaoSuCo.TrangThai.in_([TT.BC_DA_PHAN_CONG, TT.BC_DANG_XU_LY]))
    elif trang_thai:
        stmt = stmt.where(M.BaoCaoSuCo.TrangThai == trang_thai)
    if ma_loai:
        stmt = stmt.where(M.BaoCaoSuCo.MaLoai == int(ma_loai))
    if ma_dia_ban:
        stmt = stmt.where(M.BaoCaoSuCo.MaDiaBan == int(ma_dia_ban))
    if tu:
        stmt = stmt.where(M.BaoCaoSuCo.NgayGui >= tu)
    if den:
        stmt = stmt.where(M.BaoCaoSuCo.NgayGui < den)
    return phan_trang(db, stmt.order_by(M.BaoCaoSuCo.NgayGui.desc(), M.BaoCaoSuCo.MaBaoCao.desc()), trang)
