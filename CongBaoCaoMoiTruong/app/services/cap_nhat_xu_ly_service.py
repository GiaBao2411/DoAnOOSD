"""CapNhatXuLyService — UC12 Cập nhật tiến độ và kết quả (module M5, M3). BR10, BR11."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from . import luu_tru_tep_service as LT
from .common import chuyen_trang_thai, text_req, yeu_cau
from .hien_truong_service import lay_nhiem_vu, luu_cap_nhat


def luu_tien_do(db: Session, ma_pc, phan_tram, noi_dung, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_DANG_XU_LY, "Chỉ cập nhật tiến độ khi nhiệm vụ đang xử lý.")
    try:
        pt = int(phan_tram)
    except (TypeError, ValueError):
        pt = -1
    yeu_cau(0 <= pt <= 100, "Phần trăm tiến độ phải từ 0 đến 100.")
    noi_dung = text_req(noi_dung, "nội dung công việc")
    luu_cap_nhat(db, pc, tk, TT.CN_TIEN_DO, noi_dung, [], TT.GD_SAU, phan_tram=pt)
    db.commit()


def gui_ket_qua(db: Session, ma_pc, ket_qua, tep_tai_len, tk):
    pc = lay_nhiem_vu(db, ma_pc, tk)
    yeu_cau(pc.TrangThai == TT.PC_DANG_XU_LY, "Chỉ gửi kết quả khi nhiệm vụ đang xử lý.")
    ket_qua = text_req(ket_qua, "kết quả xử lý")
    yeu_cau([u for u in (tep_tai_len or []) if getattr(u, "filename", "")],
            "Gửi kết quả phải kèm ít nhất một ảnh sau xử lý (BR10).")
    _, teps, da = luu_cap_nhat(db, pc, tk, TT.CN_KET_QUA, ket_qua, tep_tai_len, TT.GD_SAU, phan_tram=100)
    try:
        pc.TrangThai = TT.PC_CHO_NGHIEM_THU   # BR11: chờ cán bộ duyệt kết quả
        chuyen_trang_thai(db, pc.bao_cao, TT.BC_CHO_NGHIEM_THU, tk.MaTaiKhoan, "Đơn vị gửi kết quả xử lý")
        db.commit()
    except Exception:
        db.rollback()
        LT.xoa_lau_dai(da)
        raise

