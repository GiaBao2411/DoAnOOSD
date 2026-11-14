"""API cho trang công khai của người dân (FormTrangChu, FormGuiBaoCao, FormTraCuu, FormLayLaiMa,
FormBoSungThongTin) và phục vụ tệp bằng chứng theo quyền."""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from .. import models as M
from .. import trang_thai as TT
from ..db import get_db, now
from ..services import bao_cao_service, bo_sung_service, danh_muc_service, email_service, tra_cuu_service
from ..services import luu_tru_tep_service as LT
from ..services.common import NghiepVuError, bi_khoa_tam, ghi_sai
from ..telemetry import danh_dau
from ..web import dt, nguoi_dung, so

router = APIRouter()


def _loai_json(ds):
    return [dict(ma=l.MaLoai, ten=l.TenLoai) for l in ds]


def _dia_ban_json(ds):
    return [dict(ma=d.MaDiaBan, ten=d.TenDiaBan) for d in ds]


@router.get("/api/cau-hinh")
def cau_hinh(db: Session = Depends(get_db)):
    """Dữ liệu chung cho giao diện: tâm bản đồ, danh mục đang dùng, các bước tiến trình."""
    return dict(map_lat=config.MAP_CENTER_LAT, map_lng=config.MAP_CENTER_LNG, bay_gio=dt(now()),
                ds_loai=_loai_json(danh_muc_service.ds_loai(db, True)),
                ds_dia_ban=_dia_ban_json(danh_muc_service.ds_dia_ban(db, True)),
                trang_thai_bc=TT.BC_ALL, uu_tien=TT.UU_TIEN, loc_o_don_vi=TT.LOC_O_DON_VI,
                nguong_mac_dinh=TT.NGUONG_MAC_DINH)


@router.get("/api/trang-chu")
def trang_chu(loai: str = "", dia_ban: str = "", db: Session = Depends(get_db)):
    ds = tra_cuu_service.ban_do_cong_khai(db, loai or None, dia_ban or None)
    return dict(ds=[dict(ma_tra_cuu=b.MaTraCuu, tieu_de=k.TieuDeCongKhai, loai=b.loai.TenLoai if b.loai else "",
                         dia_ban=b.dia_ban.TenDiaBan, ngay=dt(k.ThoiGian), lat=so(b.ViDo), lng=so(b.KinhDo))
                    for b, k in ds],
                ds_loai=_loai_json(danh_muc_service.ds_loai(db)),
                ds_dia_ban=_dia_ban_json(danh_muc_service.ds_dia_ban(db, True)))


@router.post("/api/bao-cao", status_code=201)
def gui_bao_cao(bg: BackgroundTasks, mo_ta: str = Form(""), thoi_gian_phat_hien: str = Form(""), ma_dia_ban: str = Form(""),
                dia_chi: str = Form(""), vi_do: str = Form(""), kinh_do: str = Form(""), ho_ten: str = Form(""),
                so_dien_thoai: str = Form(""), email: str = Form(""), tep: List[UploadFile] = File(default=[]),
                db: Session = Depends(get_db)):
    bc = bao_cao_service.gui_bao_cao(db, mo_ta, thoi_gian_phat_hien, ma_dia_ban, dia_chi, vi_do, kinh_do,
                                     ho_ten, so_dien_thoai, tep, email)
    danh_dau("bao_cao.gui", ma_tra_cuu=bc.MaTraCuu, dia_ban=bc.dia_ban.TenDiaBan, so_tep=len(bc.minh_chung))
    da_gui_mail = None
    if bc.nguoi_bao_cao and bc.nguoi_bao_cao.Email:
        da_gui_mail = bc.nguoi_bao_cao.Email
        bg.add_task(email_service.gui_ma_bao_cao, da_gui_mail, bc.MaTraCuu, bc.NgayGui.strftime("%d/%m/%Y %H:%M"),
                    bc.dia_ban.TenDiaBan, bc.MoTa[:300])
    return dict(ma_tra_cuu=bc.MaTraCuu, email=da_gui_mail, mail_bat=email_service.da_cau_hinh())


# ---------- Quên mã báo cáo: gửi lại danh sách mã vào email đã dùng khi gửi ----------
@router.post("/api/quen-ma")
def quen_ma(request: Request, bg: BackgroundTasks, email: str = Form(""), db: Session = Depends(get_db)):
    email = (email or "").strip().lower()
    khoa = "qm:%s" % (request.client.host if request.client else "")
    if bi_khoa_tam(khoa):
        raise NghiepVuError("Bạn đã yêu cầu quá nhiều lần. Vui lòng thử lại sau 15 phút.")
    if not email_service.hop_le(email):
        raise NghiepVuError("Địa chỉ email không hợp lệ.")
    ghi_sai(khoa)                      # mỗi IP tối đa 5 lần / 15 phút, chống dùng trang này để gửi thư rác
    ds = db.execute(select(M.BaoCaoSuCo.MaTraCuu, M.BaoCaoSuCo.NgayGui, M.DiaBan.TenDiaBan, M.BaoCaoSuCo.TrangThai)
                    .join(M.NguoiBaoCao, M.NguoiBaoCao.MaNguoiBaoCao == M.BaoCaoSuCo.MaNguoiBaoCao)
                    .join(M.DiaBan, M.DiaBan.MaDiaBan == M.BaoCaoSuCo.MaDiaBan)
                    .where(M.NguoiBaoCao.Email == email).order_by(M.BaoCaoSuCo.NgayGui.desc())).all()
    if ds:
        bg.add_task(email_service.gui_lai_ma, email, [(m, n.strftime("%d/%m/%Y"), p, t) for m, n, p, t in ds])
    # Luôn trả cùng một câu, không cho biết email có trong hệ thống hay không
    return dict(da_gui=True, email=email)


@router.get("/api/tra-cuu")
def tra_cuu(ma: str = "", db: Session = Depends(get_db)):
    bc = tra_cuu_service.tim_theo_ma(db, ma)
    if not bc:
        raise HTTPException(404, "Không tìm thấy báo cáo có mã “%s”. Vui lòng kiểm tra lại." % ma)
    kq = tra_cuu_service.du_lieu_cong_khai(db, bc)
    kd = kq["kd"]
    return dict(ma_tra_cuu=bc.MaTraCuu, trang_thai=bc.TrangThai, trang_thai_hien_thi=kq["trang_thai"],
                ngay_gui=dt(bc.NgayGui), dia_ban=bc.dia_ban.TenDiaBan, loai=bc.loai.TenLoai if bc.loai else "",
                buoc=kq["buoc"], buoc_hien_tai=kq["buoc_hien_tai"], cap_nhat_cuoi=dt(kq["cap_nhat_cuoi"]),
                ket_thuc=kq["ket_thuc"], ly_do_ket_thuc=bc.LyDoKetThuc,
                cong_khai=dict(tieu_de=kd.TieuDeCongKhai, noi_dung=kd.NoiDungCongKhai, ngay=dt(kd.ThoiGian)) if kd else None,
                anh=[dict(nhan=n, bang=b, ma=m, loai=l) for n, b, m, l in kq["anh"]],
                cho_bo_sung=bc.TrangThai == TT.BC_CHO_BO_SUNG)


# ---------- UC03 Bổ sung thông tin ----------
def _bc_da_xac_minh(request, db):
    s = request.session.get("bo_sung")
    if not s:
        return None
    ma_bc, het_han = s
    if now().timestamp() > het_han:
        request.session.pop("bo_sung", None)
        return None
    return db.get(M.BaoCaoSuCo, ma_bc)


@router.get("/api/bo-sung")
def bo_sung(request: Request, db: Session = Depends(get_db)):
    bc = _bc_da_xac_minh(request, db)
    if not bc:
        return dict(bc=None)
    yc = bo_sung_service.yeu_cau_dang_cho(db, bc.MaBaoCao)
    return dict(bc=dict(ma_tra_cuu=bc.MaTraCuu, trang_thai=bc.TrangThai),
                yc=dict(noi_dung=yc.NoiDungYeuCau, ngay=dt(yc.NgayYeuCau), han=dt(yc.HanBoSung),
                        con_han=yc.HanBoSung >= now()) if yc else None)


@router.post("/api/bo-sung/xac-minh")
def bo_sung_xac_minh(request: Request, ma: str = Form(""), db: Session = Depends(get_db)):
    bc = bo_sung_service.xac_minh(db, ma, request.client.host if request.client else "")
    request.session["bo_sung"] = [bc.MaBaoCao, (now() + timedelta(minutes=30)).timestamp()]
    return dict(thong_bao="Đã tìm thấy báo cáo.")


@router.post("/api/bo-sung/gui")
def bo_sung_gui(request: Request, noi_dung: str = Form(""), tep: List[UploadFile] = File(default=[]),
                db: Session = Depends(get_db)):
    bc = _bc_da_xac_minh(request, db)
    if not bc:
        raise NghiepVuError("Phiên xác minh đã hết, vui lòng xác minh lại.")
    bo_sung_service.gui_bo_sung(db, bc, noi_dung, tep)
    return dict(thong_bao="Đã gửi bổ sung. Báo cáo chuyển về trạng thái Đang xem xét.")


@router.post("/api/bo-sung/thoat")
def bo_sung_thoat(request: Request):
    request.session.pop("bo_sung", None)
    return dict(ok=True)


# ---------- Phục vụ tệp bằng chứng theo quyền (M3, M6) ----------
@router.get("/tep/{bang}/{ma}")
def tep(request: Request, bang: str, ma: int, db: Session = Depends(get_db), tk=Depends(nguoi_dung)):
    if bang == "bc":
        m = db.get(M.MinhChungBaoCao, ma)
        bc = m.bao_cao if m else None
    elif bang == "xl":
        m = db.get(M.MinhChungXuLy, ma)
        bc = m.cap_nhat.phan_cong.bao_cao if m else None
    else:
        m = bc = None
    if not m:
        raise HTTPException(404)
    duoc_xem = False
    if tk and tk.LoaiTaiKhoan == TT.TK_CAN_BO and not tk.PhaiDoiMatKhau:
        duoc_xem = True
    elif tk and tk.LoaiTaiKhoan == TT.TK_DON_VI and not tk.PhaiDoiMatKhau:
        duoc_xem = any(p.MaDonVi == tk.MaDonVi for p in bc.phan_cong)
    if not duoc_xem and m.DuocCongKhai and bc.TrangThai == TT.BC_HOAN_TAT and tra_cuu_service.ban_cong_khai(db, bc.MaBaoCao):
        duoc_xem = True
    if not duoc_xem:
        s = request.session.get("bo_sung")
        duoc_xem = bang == "bc" and bool(s) and s[0] == bc.MaBaoCao
    if not duoc_xem:
        raise HTTPException(404)
    p = LT.duong_dan_that(m.DuongDan)
    if not p.exists():
        raise HTTPException(404)
    mt = {"jpg": "image/jpeg", "png": "image/png", "mp4": "video/mp4"}[m.LoaiTep]
    return FileResponse(str(p), media_type=mt, headers={"Cache-Control": "private, max-age=3600"})
