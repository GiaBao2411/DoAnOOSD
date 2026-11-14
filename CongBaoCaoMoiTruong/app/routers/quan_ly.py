from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from .. import trang_thai as TT
from ..db import get_db
from ..services import danh_muc_service as DM
from ..services import quan_trac_service as QT
from ..services import tai_khoan_service as TKS
from ..web import can_bo, dt, tram_json

router = APIRouter(prefix="/api/can-bo")


def _loai(o):
    return dict(ma=o.MaLoai, ten=o.TenLoai, mo_ta=o.MoTa, dang_dung=bool(o.DangSuDung))


def _dia_ban(o):
    return dict(ma=o.MaDiaBan, ten=o.TenDiaBan, tinh=o.TinhThanh, dang_dung=bool(o.DangSuDung))


def _don_vi(o):
    return dict(ma=o.MaDonVi, ten=o.TenDonVi, ma_dia_ban=o.MaDiaBan, dia_ban=o.dia_ban.TenDiaBan if o.dia_ban else "",
                dia_chi=o.DiaChi, sdt=o.SoDienThoai, dang_dung=bool(o.DangSuDung))


def _tham_so(o):
    return dict(ma=o.MaThamSo, gia_tri=o.GiaTri, mo_ta=o.MoTa, ngay=dt(o.NgayCapNhat),
                can_bo=o.can_bo.HoTen if o.can_bo else None)


@router.get("/danh-muc")
def danh_muc(tab: str = "loai", db: Session = Depends(get_db), tk=Depends(can_bo)):
    if tab == "loai":
        ds = [_loai(o) for o in DM.ds_loai(db)]
    elif tab == "dia-ban":
        ds = [_dia_ban(o) for o in DM.ds_dia_ban(db)]
    elif tab == "don-vi":
        ds = [_don_vi(o) for o in DM.ds_don_vi(db)]
    elif tab == "tram":
        ds = [tram_json(o) for o in QT.ds_tram(db)]
    else:
        ds = [_tham_so(o) for o in DM.ds_tham_so(db)]
    return dict(tab=tab, ds=ds, ds_dia_ban=[dict(ma=d.MaDiaBan, ten=d.TenDiaBan) for d in DM.ds_dia_ban(db, True)],
                nguong_mac_dinh=TT.NGUONG_MAC_DINH)


@router.post("/danh-muc/loai")
def luu_loai(ma: str = Form(""), ten: str = Form(""), mo_ta: str = Form(""), dang_dung: str = Form(""),
             db: Session = Depends(get_db), tk=Depends(can_bo)):
    DM.luu_loai(db, ma, ten, mo_ta, dang_dung)
    return dict(thong_bao="Đã lưu loại sự cố.")


@router.post("/danh-muc/dia-ban")
def luu_dia_ban(ma: str = Form(""), ten: str = Form(""), tinh: str = Form(""), dang_dung: str = Form(""),
                db: Session = Depends(get_db), tk=Depends(can_bo)):
    DM.luu_dia_ban(db, ma, ten, tinh, dang_dung)
    return dict(thong_bao="Đã lưu địa bàn.")


@router.post("/danh-muc/don-vi")
def luu_don_vi(ma: str = Form(""), ten: str = Form(""), ma_dia_ban: str = Form(""), dia_chi: str = Form(""),
               sdt: str = Form(""), dang_dung: str = Form(""), db: Session = Depends(get_db), tk=Depends(can_bo)):
    DM.luu_don_vi(db, ma, ten, ma_dia_ban, dia_chi, sdt, dang_dung)
    return dict(thong_bao="Đã lưu đơn vị xử lý.")


def _khoa(kq):
    tram, khoa = kq
    if khoa:
        return dict(thong_bao="Đã lưu thiết bị %s và cấp khóa mới." % tram.MaThietBi, khoa=[tram.MaThietBi, khoa],
                    ma=tram.MaTram)
    return dict(thong_bao="Đã lưu thiết bị %s." % tram.MaThietBi, ma=tram.MaTram)


@router.post("/danh-muc/tram")
def luu_tram(ma: str = Form(""), ma_thiet_bi: str = Form(""), ten: str = Form(""), ma_dia_ban: str = Form(""),
             vi_do: str = Form(""), kinh_do: str = Form(""), nguong_kk: str = Form(""), nguong_tds: str = Form(""),
             dang_dung: str = Form(""), db: Session = Depends(get_db), tk=Depends(can_bo)):
    return _khoa(QT.luu_tram(db, ma, ma_thiet_bi, ten, ma_dia_ban, vi_do, kinh_do, nguong_kk, nguong_tds, dang_dung))


@router.post("/danh-muc/tram/{ma}/cap-khoa")
def cap_khoa(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    return _khoa(QT.cap_khoa_moi(db, ma))


@router.post("/danh-muc/tham-so")
def luu_tham_so(ma: str = Form(""), gia_tri: str = Form(""), db: Session = Depends(get_db), tk=Depends(can_bo)):
    DM.luu_tham_so(db, ma, gia_tri, tk)
    return dict(thong_bao="Đã cập nhật tham số %s." % ma)


def _tai_khoan(t):
    return dict(ma=t.MaTaiKhoan, ten_dang_nhap=t.TenDangNhap, don_vi=t.don_vi.TenDonVi if t.don_vi else "",
                trang_thai=t.TrangThai, lan_dang_nhap_cuoi=dt(t.LanDangNhapCuoi))


@router.get("/tai-khoan")
def tai_khoan(q: str = "", db: Session = Depends(get_db), tk=Depends(can_bo)):
    return dict(ds=[_tai_khoan(t) for t in TKS.ds_tai_khoan(db, q)],
                ds_don_vi=[dict(ma=d.MaDonVi, ten=d.TenDonVi) for d in DM.ds_don_vi(db, True)])


@router.post("/tai-khoan/them")
def tk_them(ten: str = Form(""), ma_don_vi: str = Form(""), db: Session = Depends(get_db), tk=Depends(can_bo)):
    t, mk = TKS.them(db, ten, ma_don_vi)
    return dict(thong_bao="Đã lưu tài khoản %s." % t.TenDangNhap, mat_khau_tam=[t.TenDangNhap, mk], ma=t.MaTaiKhoan)


@router.post("/tai-khoan/{ma}/khoa")
def tk_khoa(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    t = TKS.doi_trang_thai(db, ma, tk)
    return dict(thong_bao="Tài khoản %s: %s." % (t.TenDangNhap, t.TrangThai.lower()))


@router.post("/tai-khoan/{ma}/dat-lai")
def tk_dat_lai(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    t, mk = TKS.dat_lai_mat_khau(db, ma)
    return dict(thong_bao="Đã lưu tài khoản %s." % t.TenDangNhap, mat_khau_tam=[t.TenDangNhap, mk])
