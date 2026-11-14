"""ApiSoLieuQuanTrac — điểm nhận số liệu của thiết bị đo IoT (UC13, module M8). Không có giao diện."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import quan_trac_service as QT
from ..telemetry import danh_dau

router = APIRouter(prefix="/api/tram")


@router.post("/so-lieu")
async def post_so_lieu(request: Request, db: Session = Depends(get_db)):
    try:
        goi = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "loi": "Nội dung không phải JSON hợp lệ."}, status_code=400)
    try:
        sl = await run_in_threadpool(QT.nhan_so_lieu, db, goi)  # băm khóa tốn CPU: chạy ngoài vòng lặp sự kiện
    except QT.LoiApi as e:
        db.rollback()
        danh_dau("thiet_bi.tu_choi", ma_thiet_bi=str(goi.get("ma_thiet_bi", "")) if isinstance(goi, dict) else "", ma_http=e.ma_http)
        return JSONResponse({"ok": False, "loi": str(e)}, status_code=e.ma_http)
    danh_dau("thiet_bi.so_lieu", ma_thiet_bi=sl.tram.MaThietBi, khong_khi_ppm=float(sl.KhongKhiPPM),
             tds_ppm=float(sl.TdsPPM), vuot_nguong=bool(sl.VuotNguong))
    return JSONResponse({"ok": True, "ma_so_lieu": sl.MaSoLieu, "vuot_nguong": sl.VuotNguong,
                         "thoi_gian": sl.ThoiGianDo.strftime("%Y-%m-%d %H:%M:%S")}, status_code=201)
