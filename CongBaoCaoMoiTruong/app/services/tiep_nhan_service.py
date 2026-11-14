"""TiepNhanService — UC05 Tiếp nhận và kiểm tra báo cáo (module M4, M3). BR05, BR06."""
from datetime import timedelta

from sqlalchemy import select, exists, and_
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import chuyen_trang_thai, kiem_tra_phien_ban, parse_dt, phan_trang, tham_so, text_req, yeu_cau

TAB_MOI, TAB_DA_BO_SUNG, TAB_QUA_HAN = "moi", "da-bo-sung", "qua-han"


def _yc_qua_han():
    return exists().where(and_(M.YeuCauBoSung.MaBaoCao == M.BaoCaoSuCo.MaBaoCao,
                               M.YeuCauBoSung.TrangThai == TT.YC_CHO, M.YeuCauBoSung.HanBoSung < now()))


def hang_doi(db: Session, tab: str, trang: int = 1):
    B = M.BaoCaoSuCo
    if tab == TAB_DA_BO_SUNG:
        da_ph = exists().where(and_(M.YeuCauBoSung.MaBaoCao == B.MaBaoCao, M.YeuCauBoSung.TrangThai == TT.YC_DA_PHAN_HOI))
        stmt = select(B).where(B.TrangThai == TT.BC_DANG_XEM_XET, da_ph)
    elif tab == TAB_QUA_HAN:
        stmt = select(B).where(B.TrangThai == TT.BC_CHO_BO_SUNG, _yc_qua_han())
    else:
        stmt = select(B).where(B.TrangThai.in_([TT.BC_MOI_GUI, TT.BC_DANG_XEM_XET]))
    return phan_trang(db, stmt.order_by(B.NgayGui, B.MaBaoCao), trang)


def dem_hang_doi(db: Session):
    return {t: hang_doi(db, t).tong for t in (TAB_MOI, TAB_DA_BO_SUNG, TAB_QUA_HAN)}


def _bc(db, ma_bao_cao) -> M.BaoCaoSuCo:
    bc = db.get(M.BaoCaoSuCo, int(ma_bao_cao))
    yeu_cau(bc, "Không tìm thấy báo cáo.")
    return bc


def tiep_nhan(db: Session, ma_bao_cao, tk: M.TaiKhoan):
    """Cán bộ mở báo cáo mới để kiểm tra: Mới gửi → Đang xem xét."""
    bc = _bc(db, ma_bao_cao)
    yeu_cau(bc.TrangThai == TT.BC_MOI_GUI, "Báo cáo không ở trạng thái Mới gửi.")
    bc.MaCanBoTiepNhan = tk.MaCanBo
    chuyen_trang_thai(db, bc, TT.BC_DANG_XEM_XET, tk.MaTaiKhoan, "Cán bộ tiếp nhận, bắt đầu kiểm tra")
    db.commit()
    return bc


def xac_nhan_hop_le(db: Session, ma_bao_cao, ma_loai, uu_tien, tk, rv=None):
    bc = _bc(db, ma_bao_cao)
    kiem_tra_phien_ban(bc, rv)
    yeu_cau(bc.TrangThai == TT.BC_DANG_XEM_XET, "Chỉ xác nhận hợp lệ khi báo cáo đang được xem xét.")
    loai = db.get(M.LoaiSuCo, int(ma_loai)) if ma_loai else None
    yeu_cau(loai and loai.DangSuDung, "Vui lòng chọn loại sự cố.")
    yeu_cau(uu_tien in TT.UU_TIEN, "Vui lòng chọn mức độ ưu tiên.")
    bc.MaLoai, bc.MucDoUuTien = loai.MaLoai, uu_tien
    bc.MaCanBoTiepNhan = bc.MaCanBoTiepNhan or tk.MaCanBo
    chuyen_trang_thai(db, bc, TT.BC_CHO_PHAN_CONG, tk.MaTaiKhoan, "Hợp lệ — %s, ưu tiên %s" % (loai.TenLoai, uu_tien))
    db.commit()
    return bc


def yeu_cau_bo_sung(db: Session, ma_bao_cao, noi_dung, han, tk, rv=None):
    bc = _bc(db, ma_bao_cao)
    kiem_tra_phien_ban(bc, rv)
    yeu_cau(bc.TrangThai == TT.BC_DANG_XEM_XET, "Chỉ yêu cầu bổ sung khi báo cáo đang được xem xét.")
    noi_dung = text_req(noi_dung, "nội dung yêu cầu bổ sung", 1000)
    t = now()
    han_dt = parse_dt(han, "hạn bổ sung", bat_buoc=False) or (t + timedelta(days=tham_so(db, "HAN_BO_SUNG_NGAY")))
    yeu_cau(han_dt > t, "Hạn bổ sung phải sau thời điểm hiện tại.")
    yc = M.YeuCauBoSung(MaBaoCao=bc.MaBaoCao, MaCanBo=tk.MaCanBo, NoiDungYeuCau=noi_dung, NgayYeuCau=t,
                        HanBoSung=han_dt, TrangThai=TT.YC_CHO)
    db.add(yc)
    chuyen_trang_thai(db, bc, TT.BC_CHO_BO_SUNG, tk.MaTaiKhoan, "Yêu cầu bổ sung: " + noi_dung)
    db.commit()
    return yc


def tu_choi(db: Session, ma_bao_cao, ly_do, tk, rv=None):
    bc = _bc(db, ma_bao_cao)
    kiem_tra_phien_ban(bc, rv)
    yeu_cau(bc.TrangThai == TT.BC_DANG_XEM_XET, "Chỉ từ chối khi báo cáo đang được xem xét.")
    bc.LyDoKetThuc = text_req(ly_do, "lý do từ chối", 500)
    chuyen_trang_thai(db, bc, TT.BC_BI_TU_CHOI, tk.MaTaiKhoan, bc.LyDoKetThuc)
    db.commit()


def dong_ho_so_qua_han(db: Session, ma_bao_cao, tk):
    bc = _bc(db, ma_bao_cao)
    yeu_cau(bc.TrangThai == TT.BC_CHO_BO_SUNG, "Báo cáo không ở trạng thái Chờ bổ sung.")
    yc = db.scalar(select(M.YeuCauBoSung).where(M.YeuCauBoSung.MaBaoCao == bc.MaBaoCao,
                                                M.YeuCauBoSung.TrangThai == TT.YC_CHO))
    yeu_cau(yc and yc.HanBoSung < now(), "Yêu cầu bổ sung chưa quá hạn.")
    yc.TrangThai = TT.YC_QUA_HAN
    bc.LyDoKetThuc = "Quá hạn bổ sung thông tin (hạn %s)." % yc.HanBoSung.strftime("%d/%m/%Y %H:%M")
    chuyen_trang_thai(db, bc, TT.BC_DA_DONG, tk.MaTaiKhoan, bc.LyDoKetThuc)
    db.commit()
