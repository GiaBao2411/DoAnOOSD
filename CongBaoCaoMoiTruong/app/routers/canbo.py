"""API cho các màn hình của cán bộ xử lý: FormTiepNhan, FormPhanCong, FormDuyetKetQua, FormKiemDuyet,
FormThietBiDo, FormTraCuu (nội bộ)."""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import get_db, now
from ..services import (danh_muc_service, kiem_duyet_service, nghiem_thu_service, phan_cong_service,
                        quan_trac_service, tiep_nhan_service, tra_cuu_service)
from ..services.common import NghiepVuError, parse_dt, tham_so
from ..web import (bc_chi_tiet, bc_tom_tat, can_bo, dt, media_bc, media_xl, pc_chi_tiet, pc_tom_tat, so_lieu_json,
                   trang_json, tram_json)

router = APIRouter(prefix="/api/can-bo")


def _bc(db, ma):
    bc = db.get(M.BaoCaoSuCo, ma)
    if not bc:
        raise HTTPException(404, "Không tìm thấy báo cáo.")
    return bc


@router.get("/bao-cao/{ma}")
def chi_tiet_bao_cao(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    """Chi tiết đầy đủ một báo cáo cho cán bộ (dùng ở Tiếp nhận, Phân công, Tra cứu nội bộ)."""
    bc = _bc(db, ma)
    d = bc_chi_tiet(bc, lien_he=True)
    yc = [y for y in bc.yeu_cau_bo_sung if y.TrangThai == TT.YC_CHO]
    d["yc_qua_han"] = bool(bc.TrangThai == TT.BC_CHO_BO_SUNG and yc and yc[-1].HanBoSung < now())
    d["han_mac_dinh"] = dt(now() + timedelta(days=tham_so(db, "HAN_BO_SUNG_NGAY")))
    kd = tra_cuu_service.ban_cong_khai(db, bc.MaBaoCao)
    d["ban_cong_khai"] = kd.TieuDeCongKhai if kd else None
    return d


# ---------------- UC05 Tiếp nhận và kiểm tra ----------------
@router.get("/tiep-nhan")
def tiep_nhan(tab: str = "moi", trang: int = 1, db: Session = Depends(get_db), tk=Depends(can_bo)):
    ds = tiep_nhan_service.hang_doi(db, tab, trang)
    return dict(ds=trang_json(ds, bc_tom_tat), dem=tiep_nhan_service.dem_hang_doi(db),
                ds_loai=[dict(ma=l.MaLoai, ten=l.TenLoai) for l in danh_muc_service.ds_loai(db, True)])


@router.post("/tiep-nhan/{ma}/nhan")
def tn_nhan(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    tiep_nhan_service.tiep_nhan(db, ma, tk)
    return dict(thong_bao="Đã tiếp nhận, báo cáo chuyển sang Đang xem xét.")


@router.post("/tiep-nhan/{ma}/hop-le")
def tn_hop_le(ma: int, ma_loai: str = Form(""), uu_tien: str = Form(""), rv: str = Form(""),
              db: Session = Depends(get_db), tk=Depends(can_bo)):
    bc = tiep_nhan_service.xac_nhan_hop_le(db, ma, ma_loai, uu_tien, tk, rv)
    return dict(thong_bao="%s hợp lệ, đã chuyển sang Chờ phân công." % bc.MaTraCuu)


@router.post("/tiep-nhan/{ma}/bo-sung")
def tn_bo_sung(ma: int, noi_dung: str = Form(""), han: str = Form(""), rv: str = Form(""),
               db: Session = Depends(get_db), tk=Depends(can_bo)):
    tiep_nhan_service.yeu_cau_bo_sung(db, ma, noi_dung, han, tk, rv)
    return dict(thong_bao="Đã gửi yêu cầu bổ sung, báo cáo chuyển sang Chờ bổ sung.")


@router.post("/tiep-nhan/{ma}/tu-choi")
def tn_tu_choi(ma: int, noi_dung: str = Form(""), rv: str = Form(""), db: Session = Depends(get_db), tk=Depends(can_bo)):
    tiep_nhan_service.tu_choi(db, ma, noi_dung, tk, rv)
    return dict(thong_bao="Đã từ chối báo cáo.")


@router.post("/tiep-nhan/{ma}/dong")
def tn_dong(ma: int, db: Session = Depends(get_db), tk=Depends(can_bo)):
    tiep_nhan_service.dong_ho_so_qua_han(db, ma, tk)
    return dict(thong_bao="Đã đóng hồ sơ do quá hạn bổ sung.")


# ---------------- UC06 Phân công ----------------
@router.get("/phan-cong")
def phan_cong(ma: int = 0, trang: int = 1, db: Session = Depends(get_db), tk=Depends(can_bo)):
    out = dict(ds=trang_json(phan_cong_service.danh_sach_cho(db, trang), bc_tom_tat), chon=None)
    if ma:
        bc = _bc(db, ma)
        hl = phan_cong_service.phan_cong_hieu_luc(db, bc.MaBaoCao)
        out["chon"] = dict(
            bao_cao=bc_chi_tiet(bc, lien_he=True),
            don_vi=[dict(ma=d.MaDonVi, ten=d.TenDonVi, goi_y=d.MaDiaBan == bc.MaDiaBan)
                    for d in phan_cong_service.goi_y_don_vi(db, bc)],
            pc_hieu_luc=dict(ma=hl.MaPhanCong, ma_don_vi=hl.MaDonVi, don_vi=hl.don_vi.TenDonVi,
                             trang_thai=hl.TrangThai) if hl else None,
            giao_duoc=bc.TrangThai in (TT.BC_CHO_PHAN_CONG, TT.BC_DA_PHAN_CONG, TT.BC_DANG_XU_LY))
    return out


@router.post("/phan-cong/{ma}/giao")
def pc_giao(ma: int, ma_don_vi: str = Form(""), noi_dung: str = Form(""), rv: str = Form(""),
            db: Session = Depends(get_db), tk=Depends(can_bo)):
    pc = phan_cong_service.giao_nhiem_vu(db, ma, ma_don_vi, noi_dung, tk, rv)
    return dict(thong_bao="Đã giao PC-%d cho %s." % (pc.MaPhanCong, pc.don_vi.TenDonVi))


# ---------------- UC07 Duyệt kết quả ----------------
@router.get("/nghiem-thu")
def nghiem_thu(pc: int = 0, trang: int = 1, db: Session = Depends(get_db), tk=Depends(can_bo)):
    ds = nghiem_thu_service.cho_nghiem_thu(db, trang)
    chon = db.get(M.PhanCongXuLy, pc) if pc else (ds.items[0] if ds.items else None)
    ct = None
    if chon:
        ct = pc_chi_tiet(chon)
        cuoi = nghiem_thu_service.cap_nhat_cuoi(chon)
        ct["khong_su_co"] = bool(cuoi and cuoi.LoaiCapNhat == TT.CN_KHONG_SU_CO)
    return dict(ds=trang_json(ds, pc_tom_tat), chon=ct, bay_gio=dt(now()))


@router.post("/nghiem-thu/{pc}")
def nt_luu(pc: int, ket_qua: str = Form(""), nhan_xet: str = Form(""), db: Session = Depends(get_db),
           tk=Depends(can_bo)):
    p = nghiem_thu_service.nghiem_thu(db, pc, ket_qua, nhan_xet, tk)
    if ket_qua == TT.NT_DAT:
        # Đạt -> báo cáo sang "Chờ công khai": giao diện mở luôn trang kiểm duyệt của báo cáo đó
        return dict(thong_bao="Đã duyệt PC-%d: Đạt. Báo cáo chuyển sang Chờ công khai — kiểm duyệt nội dung rồi công khai bên dưới." % pc,
                    chuyen_den="/can-bo/kiem-duyet?ma=%d" % p.MaBaoCao)
    return dict(thong_bao="Đã lưu kết quả duyệt PC-%d: %s." % (pc, ket_qua), chuyen_den="/can-bo/nghiem-thu")


# ---------------- UC08 Kiểm duyệt và công khai ----------------
@router.get("/kiem-duyet")
def kiem_duyet(ma: int = 0, trang: int = 1, db: Session = Depends(get_db), tk=Depends(can_bo)):
    ds = kiem_duyet_service.cho_cong_khai(db, trang)

    def dong(b):
        d = bc_tom_tat(b)
        xong = [p for p in b.phan_cong if p.TrangThai == TT.PC_HOAN_THANH]
        d["don_vi_xu_ly"] = xong[-1].don_vi.TenDonVi if xong else ""
        return d

    bc = db.get(M.BaoCaoSuCo, ma) if ma else (ds.items[0] if ds.items else None)
    ct = None
    if bc:
        kd = kiem_duyet_service.ban_dang_cho(db, bc.MaBaoCao)
        tieu_de, noi_dung = (kd.TieuDeCongKhai, kd.NoiDungCongKhai) if kd else kiem_duyet_service.ban_nhap_mac_dinh(bc)
        anh = [(media_bc(m, nhan) if bang == "bc" else media_xl(m, nhan)) for bang, m, nhan in kiem_duyet_service.tat_ca_anh(bc)]
        ct = dict(bao_cao=bc_chi_tiet(bc, lien_he=True), anh=anh, tieu_de=tieu_de, noi_dung=noi_dung,
                  ban_nhap=dict(thoi_gian=dt(kd.ThoiGian), da_kiem_tra=bool(kd.DaKiemTraAnDanh)) if kd else None,
                  lich_su_kd=[dict(ma=k.MaKiemDuyet, can_bo=k.can_bo.HoTen, thoi_gian=dt(k.ThoiGian), trang_thai=k.TrangThai,
                                   dang_hien_thi=bool(k.DangHienThi), ly_do=k.LyDo) for k in bc.kiem_duyet])
    return dict(ds=trang_json(ds, dong), chon=ct)


@router.post("/kiem-duyet/{ma}")
def kd_luu(ma: int, hanh_dong: str = Form(""), tieu_de: str = Form(""), noi_dung: str = Form(""),
           da_kiem_tra: str = Form(""), anh: List[str] = Form(default=[]), ly_do: str = Form(""),
           db: Session = Depends(get_db), tk=Depends(can_bo)):
    if hanh_dong == "luu":
        kiem_duyet_service.luu_ban_nhap(db, ma, tieu_de, noi_dung, da_kiem_tra, anh, tk)
        db.commit()
        return dict(thong_bao="Đã lưu bản nháp công khai.", chuyen_den="/can-bo/kiem-duyet?ma=%d" % ma)
    duyet = hanh_dong == "duyet"
    kiem_duyet_service.quyet_dinh(db, ma, tieu_de, noi_dung, da_kiem_tra, anh, duyet, ly_do, tk)
    if duyet:
        return dict(thong_bao="Đã duyệt và công khai kết quả.", chuyen_den="/can-bo/kiem-duyet")
    return dict(thong_bao="Đã ghi quyết định không duyệt.", chuyen_den="/can-bo/kiem-duyet?ma=%d" % ma)


# ---------------- UC14 Theo dõi số liệu của thiết bị đo (module M8) ----------------
@router.get("/tram-quan-trac")
def tram_quan_trac(tram: int = 0, tu: str = "", den: str = "", vuot: str = "", db: Session = Depends(get_db),
                   tk=Depends(can_bo)):
    tq = quan_trac_service.tong_quan(db)
    chon = db.get(M.TramQuanTrac, tram) if tram else (tq[0]["tram"] if tq else None)
    rows, loi = [], None
    t_den = now()
    t_tu = t_den - timedelta(hours=3)
    try:
        if tu:
            t_tu = parse_dt(tu, "từ thời điểm")
        if den:
            t_den = parse_dt(den, "đến thời điểm")
        if chon:
            rows = quan_trac_service.so_lieu(db, chon.MaTram, t_tu, t_den, bool(vuot))
    except NghiepVuError as e:
        loi = str(e)
    return dict(tq=[dict(tram=tram_json(x["tram"]), moi=so_lieu_json(x["moi"]), mat_ket_noi=x["mat_ket_noi"]) for x in tq],
                chon=tram_json(chon) if chon else None, rows=[so_lieu_json(r) for r in rows], loi=loi,
                tu=dt(t_tu), den=dt(t_den), phut=tham_so(db, "TRAM_MAT_KET_NOI_PHUT"))


# ---------------- UC02 Tra cứu nội bộ ----------------
@router.get("/tra-cuu")
def tra_cuu(q: str = "", trang_thai: str = "", loai: str = "", dia_ban: str = "", tu_ngay: str = "",
            den_ngay: str = "", trang: int = 1, db: Session = Depends(get_db), tk=Depends(can_bo)):
    loi = None
    tu = den = None
    try:
        tu = parse_dt(tu_ngay, "từ ngày", False)
        den = parse_dt(den_ngay, "đến ngày", False)
        den = den + timedelta(days=1) if den else None
    except NghiepVuError as e:
        loi = str(e)
    ds = tra_cuu_service.tim_noi_bo(db, q, trang_thai or None, loai or None, dia_ban or None, tu, den, trang)
    return dict(ds=trang_json(ds, bc_tom_tat), loi=loi,
                ds_loai=[dict(ma=l.MaLoai, ten=l.TenLoai) for l in danh_muc_service.ds_loai(db)],
                ds_dia_ban=[dict(ma=d.MaDiaBan, ten=d.TenDiaBan) for d in danh_muc_service.ds_dia_ban(db)])
