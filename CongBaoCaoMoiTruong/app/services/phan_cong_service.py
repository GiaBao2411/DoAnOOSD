"""PhanCongService — UC06 Phân công xử lý (module M4, M2). BR07, BR08."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import (chuyen_trang_thai, kiem_tra_phien_ban, phan_trang, text_req, yeu_cau)


def danh_sach_cho(db: Session, trang=1):
    B = M.BaoCaoSuCo
    return phan_trang(db, select(B).where(B.TrangThai == TT.BC_CHO_PHAN_CONG).order_by(B.NgayGui, B.MaBaoCao), trang)


def phan_cong_hieu_luc(db: Session, ma_bao_cao):
    return db.scalar(select(M.PhanCongXuLy).where(M.PhanCongXuLy.MaBaoCao == ma_bao_cao,
                                                  M.PhanCongXuLy.TrangThai.in_(TT.PC_HIEU_LUC)))


def goi_y_don_vi(db: Session, bc: M.BaoCaoSuCo):
    """Gợi ý đơn vị theo địa bàn (M2): đơn vị phụ trách đúng phường/xã xếp trước."""
    ds = db.scalars(select(M.DonViXuLy).where(M.DonViXuLy.DangSuDung == True).order_by(M.DonViXuLy.TenDonVi)).all()  # noqa
    return sorted(ds, key=lambda d: (d.MaDiaBan != bc.MaDiaBan, d.TenDonVi))


def giao_nhiem_vu(db: Session, ma_bao_cao, ma_don_vi, noi_dung, tk, rv=None):
    bc = db.get(M.BaoCaoSuCo, int(ma_bao_cao))
    yeu_cau(bc, "Không tìm thấy báo cáo.")
    kiem_tra_phien_ban(bc, rv)
    yeu_cau(bc.TrangThai in (TT.BC_CHO_PHAN_CONG, TT.BC_DA_PHAN_CONG, TT.BC_DANG_XU_LY),
            "Chỉ giao nhiệm vụ cho báo cáo đã hợp lệ (Chờ phân công) hoặc giao lại khi đang có phân công.")
    dv = db.get(M.DonViXuLy, int(ma_don_vi)) if ma_don_vi else None
    yeu_cau(dv and dv.DangSuDung, "Vui lòng chọn đơn vị xử lý.")
    noi_dung = text_req(noi_dung, "nội dung nhiệm vụ", 1000)
    t = now()

    cu = phan_cong_hieu_luc(db, bc.MaBaoCao)
    if cu:  # giao lại: phân công cũ chuyển Đã thay thế trong cùng giao dịch
        yeu_cau(cu.TrangThai != TT.PC_CHO_NGHIEM_THU, "Đơn vị đã gửi kết quả, hãy duyệt kết quả thay vì giao lại.")
        cu.TrangThai = TT.PC_DA_THAY_THE
        db.flush()
    pc = M.PhanCongXuLy(MaBaoCao=bc.MaBaoCao, MaCanBo=tk.MaCanBo, MaDonVi=dv.MaDonVi, NoiDungNhiemVu=noi_dung,
                        NgayPhanCong=t, TrangThai=TT.PC_CHO_TIEP_NHAN)
    db.add(pc)
    db.flush()
    ghi_chu = ("Giao lại cho " if cu else "Giao cho ") + dv.TenDonVi
    chuyen_trang_thai(db, bc, TT.BC_DA_PHAN_CONG, tk.MaTaiKhoan, ghi_chu)
    db.refresh(pc)
    db.commit()
    return pc
