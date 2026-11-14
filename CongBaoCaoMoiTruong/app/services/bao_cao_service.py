import re
import uuid

from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from . import email_service
from . import luu_tru_tep_service as LT
from .common import NghiepVuError, chuyen_trang_thai, parse_dt, text_req, yeu_cau


def _so_thuc(s, ten, lo, hi):
    if s in (None, ""):
        return None
    try:
        v = round(float(s), 6)
    except ValueError:
        raise NghiepVuError("%s không hợp lệ." % ten)
    yeu_cau(lo <= v <= hi, "%s phải trong khoảng %s..%s." % (ten, lo, hi))
    return v


def gui_bao_cao(db: Session, mo_ta, thoi_gian_phat_hien, ma_dia_ban, dia_chi, vi_do, kinh_do,
                ho_ten, so_dien_thoai, tep_tai_len, email=None):
    mo_ta = text_req(mo_ta, "mô tả sự cố")
    tg = parse_dt(thoi_gian_phat_hien, "thời gian phát hiện")
    yeu_cau(tg <= now(), "Thời gian phát hiện không được sau thời điểm gửi.")
    yeu_cau(ma_dia_ban, "Vui lòng chọn phường/xã.")
    db_ = db.get(M.DiaBan, int(ma_dia_ban))
    yeu_cau(db_ and db_.DangSuDung, "Phường/xã không hợp lệ.")
    vi_do = _so_thuc(vi_do, "Vĩ độ", -90, 90)
    kinh_do = _so_thuc(kinh_do, "Kinh độ", -180, 180)
    dia_chi = (dia_chi or "").strip()[:250] or None
    yeu_cau((vi_do is not None and kinh_do is not None) or dia_chi,
            "Vui lòng chọn vị trí trên bản đồ hoặc nhập địa chỉ.")
    sdt = (so_dien_thoai or "").strip() or None
    yeu_cau(sdt is None or re.fullmatch(r"[0-9 +.-]{8,15}", sdt), "Số điện thoại không hợp lệ.")
    email = (email or "").strip().lower() or None
    yeu_cau(email is None or email_service.hop_le(email), "Địa chỉ email không hợp lệ.")

    teps = LT.tai_len_tam(db, tep_tai_len)
    yeu_cau(teps, "Báo cáo phải có ít nhất một ảnh hoặc video làm bằng chứng.")
    da_chuyen = []
    try:
        nbc = None
        ho_ten = (ho_ten or "").strip()[:100] or None
        if ho_ten or sdt or email:
            nbc = M.NguoiBaoCao(HoTen=ho_ten, SoDienThoai=sdt, Email=email)
            db.add(nbc)
            db.flush()
        t = now()
        bc = M.BaoCaoSuCo(MaTraCuu="T" + uuid.uuid4().hex[:18],
                          MaNguoiBaoCao=nbc.MaNguoiBaoCao if nbc else None, MaDiaBan=int(ma_dia_ban),
                          MoTa=mo_ta, DiaChi=dia_chi, ViDo=vi_do, KinhDo=kinh_do, ThoiGianPhatHien=tg,
                          NgayGui=t, TrangThai=None)
        bc.TrangThai = TT.BC_MOI_GUI
        db.add(bc)
        db.flush()
        bc.MaTraCuu = "BC%d-%06d" % (t.year, bc.MaBaoCao)
        db.add(M.LichSuTrangThai(MaBaoCao=bc.MaBaoCao, TrangThaiCu=None, TrangThaiMoi=TT.BC_MOI_GUI,
                                 ThoiGian=t, MaTaiKhoan=None, GhiChu="Người dân gửi báo cáo"))
        for tep in teps:
            p = LT.chuyen_sang_lau_dai(tep)
            da_chuyen.append(p)
            db.add(M.MinhChungBaoCao(MaBaoCao=bc.MaBaoCao, TenTep=tep.ten_goc, LoaiTep=tep.loai,
                                     KichThuoc=tep.kich_thuoc, DuongDan=p, NgayTaiLen=t))
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        LT.xoa_tam(teps)
        LT.xoa_lau_dai(da_chuyen)
        raise
    return bc
