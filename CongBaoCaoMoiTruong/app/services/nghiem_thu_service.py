"""NghiemThuService — UC07 Nghiệm thu kết quả (module M4). BR12."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import chuyen_trang_thai, phan_trang, text_req, yeu_cau


def cho_nghiem_thu(db: Session, trang=1):
    P = M.PhanCongXuLy
    return phan_trang(db, select(P).where(P.TrangThai == TT.PC_CHO_NGHIEM_THU).order_by(P.MaPhanCong), trang)


def cap_nhat_cuoi(pc: M.PhanCongXuLy):
    ds = [c for c in pc.cap_nhat if c.LoaiCapNhat in (TT.CN_KET_QUA, TT.CN_KHONG_SU_CO)]
    return ds[-1] if ds else None


def nghiem_thu(db: Session, ma_pc, ket_qua, nhan_xet, tk):
    pc = db.get(M.PhanCongXuLy, int(ma_pc))
    yeu_cau(pc and pc.TrangThai == TT.PC_CHO_NGHIEM_THU, "Nhiệm vụ không ở trạng thái Chờ duyệt kết quả.")
    yeu_cau(ket_qua in TT.NT_ALL, "Vui lòng chọn quyết định duyệt.")
    cuoi = cap_nhat_cuoi(pc)
    nhan_xet = (nhan_xet or "").strip()[:1000] or None
    bc = pc.bao_cao
    if ket_qua == TT.NT_CHUA_DAT:
        nhan_xet = text_req(nhan_xet, "yêu cầu xử lý thêm", 1000)
        pc.TrangThai = TT.PC_DANG_XU_LY
        chuyen_trang_thai(db, bc, TT.BC_DANG_XU_LY, tk.MaTaiKhoan, "Duyệt kết quả chưa đạt: " + nhan_xet)
    elif ket_qua == TT.NT_DAT:
        yeu_cau(cuoi and cuoi.LoaiCapNhat == TT.CN_KET_QUA, "Đơn vị báo không có sự cố — hãy chọn “Xác nhận không có sự cố” hoặc “Chưa đạt”.")
        pc.TrangThai = TT.PC_HOAN_THANH
        chuyen_trang_thai(db, bc, TT.BC_CHO_CONG_KHAI, tk.MaTaiKhoan, "Duyệt kết quả: đạt")
    else:
        yeu_cau(cuoi and cuoi.LoaiCapNhat == TT.CN_KHONG_SU_CO, "Đơn vị không báo “không có sự cố” cho nhiệm vụ này.")
        pc.TrangThai = TT.PC_HOAN_THANH
        bc.LyDoKetThuc = "Không xác minh được sự cố tại hiện trường."
        chuyen_trang_thai(db, bc, TT.BC_DA_DONG, tk.MaTaiKhoan, bc.LyDoKetThuc)
    db.add(M.NghiemThu(MaPhanCong=pc.MaPhanCong, MaCanBo=tk.MaCanBo, ThoiGian=now(), KetQua=ket_qua, NhanXet=nhan_xet))
    db.commit()
    return pc
