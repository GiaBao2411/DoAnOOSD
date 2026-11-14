"""API cho đơn vị xử lý hiện trường: FormNhiemVuHienTruong (UC11), FormCapNhatXuLy (UC12)."""
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import cap_nhat_xu_ly_service as CN
from ..services import hien_truong_service as HT
from ..web import don_vi, pc_chi_tiet, pc_tom_tat, trang_json

router = APIRouter(prefix="/api/don-vi")


@router.get("/nhiem-vu")
def nhiem_vu(tat_ca: int = 0, trang: int = 1, db: Session = Depends(get_db), tk=Depends(don_vi)):
    return dict(ds=trang_json(HT.nhiem_vu_cua_don_vi(db, tk, not tat_ca, trang), pc_tom_tat))


@router.get("/nhiem-vu/{pc}")
def chi_tiet_nhiem_vu(pc: int, db: Session = Depends(get_db), tk=Depends(don_vi)):
    return pc_chi_tiet(HT.lay_nhiem_vu(db, pc, tk))     # nhiệm vụ của đơn vị khác -> lỗi nghiệp vụ (BR09)


@router.post("/nhiem-vu/{pc}/nhan")
def nhan(pc: int, db: Session = Depends(get_db), tk=Depends(don_vi)):
    HT.nhan_nhiem_vu(db, pc, tk)
    return dict(thong_bao="Đã nhận nhiệm vụ PC-%d." % pc)


@router.post("/nhiem-vu/{pc}/tra-lai")
def tra_lai(pc: int, ly_do: str = Form(""), db: Session = Depends(get_db), tk=Depends(don_vi)):
    HT.tra_lai(db, pc, ly_do, tk)
    return dict(thong_bao="Đã trả lại nhiệm vụ PC-%d." % pc)


@router.post("/nhiem-vu/{pc}/ghi-nhan")
def ghi_nhan(pc: int, hanh_dong: str = Form("ghi-nhan"), nhan_xet: str = Form(""), vi_do: str = Form(""),
             kinh_do: str = Form(""), tep: List[UploadFile] = File(default=[]), db: Session = Depends(get_db),
             tk=Depends(don_vi)):
    if hanh_dong == "khong-su-co":
        HT.bao_khong_co_su_co(db, pc, nhan_xet, vi_do, kinh_do, tep, tk)
        return dict(thong_bao="Đã báo không có sự cố. Nhiệm vụ chuyển sang Chờ duyệt kết quả.")
    HT.ghi_nhan_hien_truong(db, pc, nhan_xet, vi_do, kinh_do, tep, tk)
    return dict(thong_bao="Đã lưu ghi nhận hiện trường.")


@router.get("/cap-nhat")
def cap_nhat(db: Session = Depends(get_db), tk=Depends(don_vi)):
    """Các nhiệm vụ đang xử lý (cập nhật tiến độ / gửi kết quả được)."""
    return dict(ds=[pc_tom_tat(p) for p in HT.nhiem_vu_dang_xu_ly(db, tk)])


@router.post("/cap-nhat/{pc}/tien-do")
def tien_do(pc: int, phan_tram: str = Form(""), noi_dung: str = Form(""), db: Session = Depends(get_db),
            tk=Depends(don_vi)):
    CN.luu_tien_do(db, pc, phan_tram, noi_dung, tk)
    return dict(thong_bao="Đã lưu tiến độ.")


@router.post("/cap-nhat/{pc}/ket-qua")
def ket_qua(pc: int, ket_qua: str = Form(""), tep: List[UploadFile] = File(default=[]), db: Session = Depends(get_db),
            tk=Depends(don_vi)):
    CN.gui_ket_qua(db, pc, ket_qua, tep, tk)
    return dict(thong_bao="Đã gửi kết quả. Nhiệm vụ chuyển sang Chờ duyệt kết quả.")
