"""API đăng nhập (FormDangNhap), đổi mật khẩu, trang chính theo vai trò (FormMain) và đường dẫn
/api/trang-thai-moi cho cơ chế tự cập nhật của trang nội bộ."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import get_db, now
from ..services import (hien_truong_service, kiem_duyet_service, nghiem_thu_service, phan_cong_service,
                        quan_trac_service, tiep_nhan_service, xac_thuc_service)
from ..web import dt, nguoi_dung, noi_bo, pc_tom_tat, so_lieu_json, tai_khoan_json, tram_json

router = APIRouter(prefix="/api")


@router.get("/toi")
def toi(tk=Depends(nguoi_dung)):
    """Tài khoản đang đăng nhập (null nếu chưa đăng nhập)."""
    return dict(tai_khoan=tai_khoan_json(tk))


@router.post("/dang-nhap")
def dang_nhap(request: Request, ten: str = Form(""), mat_khau: str = Form(""), db: Session = Depends(get_db)):
    tk = xac_thuc_service.dang_nhap(db, ten, mat_khau)
    request.session.clear()
    request.session["ma_tk"] = tk.MaTaiKhoan
    return dict(tai_khoan=tai_khoan_json(tk))


@router.post("/dang-xuat")
def dang_xuat(request: Request):
    request.session.clear()
    return dict(ok=True)


@router.post("/doi-mat-khau")
def doi_mat_khau(cu: str = Form(""), moi: str = Form(""), nhap_lai: str = Form(""),
                 db: Session = Depends(get_db), tk=Depends(noi_bo)):
    xac_thuc_service.doi_mat_khau(db, tk, cu, moi, nhap_lai)
    return dict(thong_bao="Đã đổi mật khẩu.", tai_khoan=tai_khoan_json(tk))


@router.get("/trang-chinh")
def trang_chinh(db: Session = Depends(get_db), tk=Depends(noi_bo)):
    if tk.LoaiTaiKhoan == TT.TK_DON_VI:
        ds = hien_truong_service.nhiem_vu_cua_don_vi(db, tk, True, 1)
        dem = {s: sum(1 for p in ds.items if p.TrangThai == s) for s in TT.PC_HIEU_LUC}
        return dict(vai_tro="don_vi", bay_gio=dt(now()), ds=[pc_tom_tat(p) for p in ds.items],
                    dem=dict(cho_tiep_nhan=dem[TT.PC_CHO_TIEP_NHAN], dang_xu_ly=dem[TT.PC_DANG_XU_LY],
                             cho_duyet=dem[TT.PC_CHO_NGHIEM_THU]))
    dem_tn = tiep_nhan_service.dem_hang_doi(db)
    so = dict(moi=dem_tn["moi"], bo_sung=dem_tn["da-bo-sung"], qua_han_bs=dem_tn["qua-han"],
              phan_cong=phan_cong_service.danh_sach_cho(db).tong,
              nghiem_thu=nghiem_thu_service.cho_nghiem_thu(db).tong, cong_khai=kiem_duyet_service.cho_cong_khai(db).tong)
    so["tram_vuot"], so["tram_mat"] = quan_trac_service.dem_canh_bao(db)
    so["dang_xl"] = db.scalar(select(func.count()).select_from(M.BaoCaoSuCo)
                              .where(M.BaoCaoSuCo.TrangThai.in_([TT.BC_DA_PHAN_CONG, TT.BC_DANG_XU_LY])))
    viec = []
    for b in tiep_nhan_service.hang_doi(db, "moi").items[:5]:
        viec.append(dict(ma_tra_cuu=b.MaTraCuu, viec="Tiếp nhận, kiểm tra", noi=b.dia_ban.TenDiaBan, luc=dt(b.NgayGui),
                         url="/can-bo/tiep-nhan?ma=%d" % b.MaBaoCao))
    for b in phan_cong_service.danh_sach_cho(db).items[:5]:
        viec.append(dict(ma_tra_cuu=b.MaTraCuu, viec="Phân công", noi=b.dia_ban.TenDiaBan, luc=dt(b.NgayGui),
                         url="/can-bo/phan-cong?ma=%d" % b.MaBaoCao))
    for p in nghiem_thu_service.cho_nghiem_thu(db).items[:5]:
        gui_kq = p.cap_nhat[-1].ThoiGian if p.cap_nhat else None
        viec.append(dict(ma_tra_cuu=p.bao_cao.MaTraCuu, viec="Duyệt kết quả", noi=p.don_vi.TenDonVi, luc=dt(gui_kq),
                         url="/can-bo/nghiem-thu?pc=%d" % p.MaPhanCong))
    for b in kiem_duyet_service.cho_cong_khai(db).items[:5]:
        viec.append(dict(ma_tra_cuu=b.MaTraCuu, viec="Kiểm duyệt, công khai", noi=b.dia_ban.TenDiaBan, luc=None,
                         url="/can-bo/kiem-duyet?ma=%d" % b.MaBaoCao))
    tram = [dict(tram=tram_json(x["tram"]), moi=so_lieu_json(x["moi"]), mat_ket_noi=x["mat_ket_noi"])
            for x in quan_trac_service.tong_quan(db)]
    return dict(vai_tro="can_bo", bay_gio=dt(now()), so=so, viec=viec, tram=tram)


@router.get("/trang-thai-moi")
def trang_thai_moi(db: Session = Depends(get_db), tk=Depends(noi_bo)):
    """Trang nội bộ hỏi mỗi vài giây: số việc đang chờ (hiện trên menu) và một "dấu" thay đổi.
    Đơn vị gửi kết quả -> dấu đổi -> trang cán bộ tự tải lại dữ liệu / báo có kết quả mới cần duyệt."""
    P = M.PhanCongXuLy
    if tk.LoaiTaiKhoan == TT.TK_DON_VI:
        cho_nhan = db.scalar(select(func.count()).select_from(P)
                             .where(P.MaDonVi == tk.MaDonVi, P.TrangThai == TT.PC_CHO_TIEP_NHAN))
        moi_nhat = db.scalar(select(func.max(M.LichSuTrangThai.MaLichSu)).where(
            M.LichSuTrangThai.MaBaoCao.in_(select(P.MaBaoCao).where(P.MaDonVi == tk.MaDonVi))))
        return JSONResponse({"dem": {"cho_nhan": cho_nhan}, "dau": "%s-%s" % (cho_nhan, moi_nhat or 0)},
                            headers={"Cache-Control": "no-store"})
    dem_tn = tiep_nhan_service.dem_hang_doi(db)
    dem = {"moi": dem_tn["moi"] + dem_tn["da-bo-sung"],
           "phan_cong": phan_cong_service.danh_sach_cho(db).tong,
           "nghiem_thu": nghiem_thu_service.cho_nghiem_thu(db).tong,
           "cong_khai": kiem_duyet_service.cho_cong_khai(db).tong}
    moi_nhat = db.scalar(select(func.max(M.LichSuTrangThai.MaLichSu)))
    return JSONResponse({"dem": dem, "dau": str(moi_nhat or 0)}, headers={"Cache-Control": "no-store"})
