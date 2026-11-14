"""BoSungService — UC03 Bổ sung thông tin (module M1, M3, M6). BR05, BR14."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from . import luu_tru_tep_service as LT
from .common import (NghiepVuError, bi_khoa_tam, chuyen_trang_thai, ghi_sai, so_lan_con, text_req,
                     xoa_sai, yeu_cau)
from .tra_cuu_service import tim_theo_ma


def xac_minh(db: Session, ma_tra_cuu: str, ip: str) -> M.BaoCaoSuCo:
    """Tìm báo cáo theo mã báo cáo. Nhập sai mã quá 5 lần thì khóa tạm theo địa chỉ IP (chống dò mã)."""
    khoa = "bs:%s" % ip
    yeu_cau(not bi_khoa_tam(khoa), "Bạn đã nhập sai quá 5 lần. Vui lòng thử lại sau 15 phút.")
    bc = tim_theo_ma(db, ma_tra_cuu)
    if not bc:
        ghi_sai(khoa)
        raise NghiepVuError("Không tìm thấy báo cáo có mã này (còn %d lần thử)." % max(so_lan_con(khoa), 0))
    xoa_sai(khoa)
    return bc


def yeu_cau_dang_cho(db: Session, ma_bao_cao: int):
    return db.scalar(select(M.YeuCauBoSung).where(M.YeuCauBoSung.MaBaoCao == ma_bao_cao,
                                                  M.YeuCauBoSung.TrangThai == TT.YC_CHO)
                     .order_by(M.YeuCauBoSung.MaYeuCau.desc()))


def gui_bo_sung(db: Session, bc: M.BaoCaoSuCo, noi_dung: str, tep_tai_len):
    yc = yeu_cau_dang_cho(db, bc.MaBaoCao)
    yeu_cau(yc and bc.TrangThai == TT.BC_CHO_BO_SUNG, "Báo cáo này hiện không có yêu cầu bổ sung.")
    yeu_cau(yc.HanBoSung >= now(), "Yêu cầu bổ sung đã quá hạn, không thể gửi. Bạn có thể gửi báo cáo mới.")
    noi_dung = text_req(noi_dung, "nội dung bổ sung")
    teps = LT.tai_len_tam(db, tep_tai_len)
    da_chuyen = []
    try:
        t = now()
        yc.NoiDungPhanHoi = noi_dung
        yc.NgayPhanHoi = t
        yc.TrangThai = TT.YC_DA_PHAN_HOI
        for tep in teps:
            p = LT.chuyen_sang_lau_dai(tep)
            da_chuyen.append(p)
            db.add(M.MinhChungBaoCao(MaBaoCao=bc.MaBaoCao, MaYeuCau=yc.MaYeuCau, TenTep=tep.ten_goc, LoaiTep=tep.loai,
                                     KichThuoc=tep.kich_thuoc, DuongDan=p, NgayTaiLen=t))
        chuyen_trang_thai(db, bc, TT.BC_DANG_XEM_XET, None, "Người dân đã bổ sung thông tin")
        db.commit()
    except Exception:
        db.rollback()
        LT.xoa_tam(teps)
        LT.xoa_lau_dai(da_chuyen)
        raise
