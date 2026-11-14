from datetime import datetime
from decimal import Decimal

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models as M
from . import trang_thai as TT
from .db import get_db
from .services.common import rv
from .services.hien_truong_service import khoang_cach_m


def nguoi_dung(request: Request, db: Session = Depends(get_db)):
    ma = request.session.get("ma_tk")
    if not ma:
        return None
    tk = db.get(M.TaiKhoan, ma)
    if not tk or tk.TrangThai != TT.TK_HOAT_DONG:
        request.session.clear()
        return None
    return tk


def _yeu_cau_dang_nhap(request: Request, tk):
    if tk is None:
        raise HTTPException(401, "Vui lòng đăng nhập.")
    if tk.PhaiDoiMatKhau and request.url.path != "/api/doi-mat-khau":
        raise HTTPException(403, "Vui lòng đổi mật khẩu trước khi dùng hệ thống.")
    return tk


def noi_bo(request: Request, tk=Depends(nguoi_dung)):
    return _yeu_cau_dang_nhap(request, tk)


def can_bo(request: Request, tk=Depends(nguoi_dung)):
    tk = _yeu_cau_dang_nhap(request, tk)
    if tk.LoaiTaiKhoan != TT.TK_CAN_BO:
        raise HTTPException(403, "Tài khoản của bạn không được phép dùng chức năng này.")
    return tk


def don_vi(request: Request, tk=Depends(nguoi_dung)):
    tk = _yeu_cau_dang_nhap(request, tk)
    if tk.LoaiTaiKhoan != TT.TK_DON_VI:
        raise HTTPException(403, "Tài khoản của bạn không được phép dùng chức năng này.")
    return tk


def ten_hien_thi(tk) -> str:
    if tk is None:
        return ""
    return tk.can_bo.HoTen if tk.MaCanBo else tk.don_vi.TenDonVi


def tai_khoan_json(tk):
    if tk is None:
        return None
    return dict(ma=tk.MaTaiKhoan, ten_dang_nhap=tk.TenDangNhap, loai=tk.LoaiTaiKhoan, ten_hien_thi=ten_hien_thi(tk),
                phai_doi_mat_khau=bool(tk.PhaiDoiMatKhau))


def dt(v):
    return v.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(v, datetime) else None


def so(v):
    if v is None:
        return None
    return float(v) if isinstance(v, Decimal) else v


def trang_json(ds, ham):
    return dict(items=[ham(x) for x in ds.items], trang=ds.trang, so_trang=ds.so_trang, tong=ds.tong)


def media_bc(m, nhan=None):
    return dict(bang="bc", ma=m.MaMinhChung, ten=m.TenTep, loai=m.LoaiTep, cong_khai=bool(m.DuocCongKhai),
                bo_sung=bool(m.MaYeuCau), nhan=nhan)


def media_xl(m, nhan=None):
    return dict(bang="xl", ma=m.MaMinhChung, ten=m.TenTep, loai=m.LoaiTep, cong_khai=bool(m.DuocCongKhai),
                giai_doan=m.GiaiDoan, nhan=nhan)


def bc_tom_tat(b):
    return dict(ma=b.MaBaoCao, ma_tra_cuu=b.MaTraCuu, dia_ban=b.dia_ban.TenDiaBan if b.dia_ban else "",
                loai=b.loai.TenLoai if b.loai else None, ngay_gui=dt(b.NgayGui), trang_thai=b.TrangThai,
                uu_tien=b.MucDoUuTien, mo_ta=b.MoTa)


def lich_su_json(bc):
    out = []
    for h in bc.lich_su:
        if h.tai_khoan:
            ai = h.tai_khoan.can_bo.HoTen if h.tai_khoan.can_bo else h.tai_khoan.don_vi.TenDonVi
        else:
            ai = "Người dân"
        out.append(dict(thoi_gian=dt(h.ThoiGian), nguoi=ai, cu=h.TrangThaiCu, moi=h.TrangThaiMoi, ghi_chu=h.GhiChu))
    return out


def nghiem_thu_json(pc):
    return [dict(thoi_gian=dt(n.ThoiGian), ket_qua=n.KetQua, nhan_xet=n.NhanXet) for n in pc.nghiem_thu]


def bc_chi_tiet(bc, lien_he=False):
    d = bc_tom_tat(bc)
    d.update(thoi_gian_phat_hien=dt(bc.ThoiGianPhatHien), dia_chi=bc.DiaChi, vi_do=so(bc.ViDo), kinh_do=so(bc.KinhDo),
             ma_dia_ban=bc.MaDiaBan, ly_do_ket_thuc=bc.LyDoKetThuc, rv=rv(bc),
             minh_chung=[media_bc(m) for m in bc.minh_chung])
    if lien_he:
        n = bc.nguoi_bao_cao
        d["nguoi_bao_cao"] = dict(ho_ten=n.HoTen, so_dien_thoai=n.SoDienThoai, email=n.Email) if n else None
        d["yeu_cau_bo_sung"] = [dict(ma=y.MaYeuCau, noi_dung=y.NoiDungYeuCau, ngay=dt(y.NgayYeuCau), han=dt(y.HanBoSung),
                                     trang_thai=y.TrangThai, phan_hoi=y.NoiDungPhanHoi, ngay_phan_hoi=dt(y.NgayPhanHoi))
                                for y in bc.yeu_cau_bo_sung]
        d["lich_su"] = lich_su_json(bc)
        d["phan_cong"] = [dict(ma=p.MaPhanCong, ma_don_vi=p.MaDonVi, don_vi=p.don_vi.TenDonVi, ngay=dt(p.NgayPhanCong),
                               trang_thai=p.TrangThai, ly_do_tra_lai=p.LyDoTraLai, nghiem_thu=nghiem_thu_json(p))
                          for p in bc.phan_cong]
    return d


def cap_nhat_json(pc):
    out = []
    bc = pc.bao_cao
    for c in pc.cap_nhat:
        out.append(dict(ma=c.MaCapNhat, thoi_gian=dt(c.ThoiGian), loai=c.LoaiCapNhat, phan_tram=c.PhanTramTienDo,
                        noi_dung=c.NoiDung, vi_do=so(c.ViDo), kinh_do=so(c.KinhDo),
                        khoang_cach=khoang_cach_m(so(bc.ViDo), so(bc.KinhDo), so(c.ViDo), so(c.KinhDo)),
                        minh_chung=[media_xl(m, "Ảnh %s · %s" % (m.GiaiDoan.lower(), m.TenTep)) for m in c.minh_chung]))
    return out


def pc_tom_tat(p):
    kq = [c for c in p.cap_nhat if c.LoaiCapNhat in (TT.CN_KET_QUA, TT.CN_KHONG_SU_CO)]
    kq = kq[-1] if kq else None
    return dict(ma=p.MaPhanCong, trang_thai=p.TrangThai, ngay=dt(p.NgayPhanCong), don_vi=p.don_vi.TenDonVi,
                ma_tra_cuu=p.bao_cao.MaTraCuu, ma_bao_cao=p.MaBaoCao, dia_ban=p.bao_cao.dia_ban.TenDiaBan,
                uu_tien=p.bao_cao.MucDoUuTien, loai_bc=p.bao_cao.loai.TenLoai if p.bao_cao.loai else None,
                ket_qua_loai=kq.LoaiCapNhat if kq else None, ket_qua_luc=dt(kq.ThoiGian) if kq else None)


def pc_chi_tiet(p):
    d = pc_tom_tat(p)
    d.update(noi_dung=p.NoiDungNhiemVu, bao_cao=bc_chi_tiet(p.bao_cao), cap_nhat=cap_nhat_json(p),
             nghiem_thu=nghiem_thu_json(p))
    return d


def tram_json(t):
    return dict(ma=t.MaTram, ma_thiet_bi=t.MaThietBi, ten=t.TenTram, dia_ban=t.dia_ban.TenDiaBan if t.dia_ban else "",
                ma_dia_ban=t.MaDiaBan, vi_do=so(t.ViDo), kinh_do=so(t.KinhDo), nguong_kk=so(t.NguongKhongKhi),
                nguong_tds=so(t.NguongTDS), lan_gui_cuoi=dt(t.LanGuiCuoi), dang_dung=bool(t.DangSuDung))


def so_lieu_json(s):
    if s is None:
        return None
    return dict(thoi_gian=dt(s.ThoiGianDo), kk=so(s.KhongKhiPPM), tds=so(s.TdsPPM), vuot=bool(s.VuotNguong))
