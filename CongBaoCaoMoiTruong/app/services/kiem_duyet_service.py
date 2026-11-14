from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import chuyen_trang_thai, phan_trang, text_req, yeu_cau
from .nghiem_thu_service import cap_nhat_cuoi


def cho_cong_khai(db: Session, trang=1):
    B = M.BaoCaoSuCo
    return phan_trang(db, select(B).where(B.TrangThai == TT.BC_CHO_CONG_KHAI).order_by(B.MaBaoCao), trang)


def phan_cong_hoan_thanh(bc):
    ds = [p for p in bc.phan_cong if p.TrangThai == TT.PC_HOAN_THANH]
    return ds[-1] if ds else None


def tat_ca_anh(bc):
    out = [("bc", m, "Người dân gửi") for m in bc.minh_chung]
    for pc in bc.phan_cong:
        for cn in pc.cap_nhat:
            out += [("xl", m, "Đơn vị — %s xử lý" % m.GiaiDoan.lower()) for m in cn.minh_chung]
    return out


def ban_nhap_mac_dinh(bc):
    loai = bc.loai.TenLoai if bc.loai else "sự cố môi trường"
    tieu_de = "Đã xử lý %s tại %s" % (loai.lower(), bc.dia_ban.TenDiaBan)
    pc = phan_cong_hoan_thanh(bc)
    kq = cap_nhat_cuoi(pc).NoiDung if pc and cap_nhat_cuoi(pc) else ""
    noi_dung = "Sự cố được phản ánh ngày %s%s.\nKết quả xử lý: %s" % (
        bc.NgayGui.strftime("%d/%m/%Y"), (" tại " + bc.DiaChi) if bc.DiaChi else "", kq)
    return tieu_de, noi_dung


def ban_dang_cho(db: Session, ma_bc):
    return db.scalar(select(M.KiemDuyet).where(M.KiemDuyet.MaBaoCao == ma_bc, M.KiemDuyet.TrangThai == TT.KD_CHO_DUYET)
                     .order_by(M.KiemDuyet.MaKiemDuyet.desc()))


def luu_ban_nhap(db: Session, ma_bc, tieu_de, noi_dung, da_kiem_tra, anh_chon, tk) -> M.KiemDuyet:
    bc = db.get(M.BaoCaoSuCo, int(ma_bc))
    yeu_cau(bc and bc.TrangThai == TT.BC_CHO_CONG_KHAI, "Báo cáo không ở trạng thái Chờ công khai.")
    tieu_de = text_req(tieu_de, "tiêu đề công khai", 200)
    noi_dung = text_req(noi_dung, "nội dung công khai")
    kd = ban_dang_cho(db, bc.MaBaoCao)
    if not kd:
        kd = M.KiemDuyet(MaBaoCao=bc.MaBaoCao, TrangThai=TT.KD_CHO_DUYET)
        db.add(kd)
    kd.MaCanBo, kd.TieuDeCongKhai, kd.NoiDungCongKhai = tk.MaCanBo, tieu_de, noi_dung
    kd.DaKiemTraAnDanh, kd.ThoiGian = bool(da_kiem_tra), now()
    chon = set(anh_chon or [])
    for bang, m, _ in tat_ca_anh(bc):
        m.DuocCongKhai = ("%s-%d" % (bang, m.MaMinhChung)) in chon
    db.flush()
    return kd


def quyet_dinh(db: Session, ma_bc, tieu_de, noi_dung, da_kiem_tra, anh_chon, duyet: bool, ly_do, tk):
    kd = luu_ban_nhap(db, ma_bc, tieu_de, noi_dung, da_kiem_tra, anh_chon, tk)
    bc = kd.bao_cao or db.get(M.BaoCaoSuCo, int(ma_bc))
    if duyet:
        yeu_cau(kd.DaKiemTraAnDanh, "Phải xác nhận đã kiểm tra ẩn thông tin cá nhân trước khi duyệt (BR12).")
        db.execute(update(M.KiemDuyet).where(M.KiemDuyet.MaBaoCao == bc.MaBaoCao, M.KiemDuyet.DangHienThi == True)
                   .values(DangHienThi=False))
        db.flush()
        kd.TrangThai, kd.DangHienThi, kd.LyDo = TT.KD_DA_DUYET, True, None
        chuyen_trang_thai(db, bc, TT.BC_HOAN_TAT, tk.MaTaiKhoan, "Duyệt và công khai kết quả")
    else:
        kd.TrangThai, kd.DangHienThi = TT.KD_KHONG_DUYET, False
        kd.LyDo = text_req(ly_do, "lý do không duyệt", 500)
    db.commit()
    return kd
