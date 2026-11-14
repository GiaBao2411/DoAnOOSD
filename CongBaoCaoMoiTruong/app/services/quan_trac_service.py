"""QuanTracService — UC13 Gửi số liệu quan trắc, UC14 Theo dõi số liệu quan trắc, quản lý thiết bị trong UC09 (module M8).

Thiết bị đo (Raspberry Pi Pico 2 + MQ135 + TDS) gửi qua cầu nối USB (hoặc Pico W gửi qua WiFi) một HTTP POST dạng JSON:
    {"ma_thiet_bi": "TRAM01", "khoa": "...", "khong_khi_ppm": 452.3, "tds_ppm": 236.0}
"""
import re
import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..db import now
from .common import bam, kiem_tra_bam, tham_so, text_req, yeu_cau

MA_RE = re.compile(r"^[A-Za-z0-9_-]{2,20}$")


class LoiApi(Exception):
    """Lỗi trả về cho thiết bị kèm mã HTTP (401: sai mã/khóa, 422: số liệu sai)."""
    def __init__(self, ma_http, thong_bao):
        super().__init__(thong_bao)
        self.ma_http = ma_http


# ---------------- UC13: thiết bị gửi số liệu ----------------
def _so(goi, khoa, toi_da):
    try:
        v = float(goi.get(khoa))
    except (TypeError, ValueError):
        raise LoiApi(422, "Thiếu hoặc sai kiểu giá trị %s." % khoa)
    if not (0 <= v <= toi_da):  # BR17: ngoài dải đo của cảm biến
        raise LoiApi(422, "%s = %s nằm ngoài dải đo 0..%d." % (khoa, v, toi_da))
    return round(v, 1)


def nhan_so_lieu(db: Session, goi: dict):
    if not isinstance(goi, dict):
        raise LoiApi(422, "Gói tin phải là JSON object.")
    ma = str(goi.get("ma_thiet_bi") or goi.get("ma_tram") or "").strip()
    khoa = str(goi.get("khoa") or "")
    tram = db.scalar(select(M.TramQuanTrac).where(M.TramQuanTrac.MaThietBi == ma)) if ma else None
    # BR17: sai mã, sai khóa hoặc thiết bị ngừng sử dụng -> 401, không lưu
    if not tram or not tram.DangSuDung or not kiem_tra_bam(khoa, tram.KhoaBam):
        raise LoiApi(401, "Mã thiết bị hoặc khóa không đúng, hoặc thiết bị đã ngừng sử dụng.")
    kk = _so(goi, "khong_khi_ppm", TT.KHI_TOI_DA_PPM)
    tds = _so(goi, "tds_ppm", TT.TDS_TOI_DA_PPM)
    vuot = kk > tram.NguongKhongKhi or tds > tram.NguongTDS  # BR18
    t = now()
    sl = M.SoLieuQuanTrac(MaTram=tram.MaTram, ThoiGianDo=t, KhongKhiPPM=kk, TdsPPM=tds, VuotNguong=vuot)
    db.add(sl)
    tram.LanGuiCuoi = t
    db.commit()
    return sl


# ---------------- UC14: cán bộ theo dõi ----------------
def mat_ket_noi(db, tram, luc=None):
    """BR19: quá TRAM_MAT_KET_NOI_PHUT phút không gửi thì mất kết nối."""
    if not tram.LanGuiCuoi:
        return True
    return (luc or now()) - tram.LanGuiCuoi > timedelta(minutes=tham_so(db, "TRAM_MAT_KET_NOI_PHUT"))


def ds_tram(db: Session, chi_dang_dung=False):
    s = select(M.TramQuanTrac).order_by(M.TramQuanTrac.MaThietBi)
    if chi_dang_dung:
        s = s.where(M.TramQuanTrac.DangSuDung == True)  # noqa: E712
    return db.scalars(s).all()


def moi_nhat(db: Session, ma_tram):
    return db.scalar(select(M.SoLieuQuanTrac).where(M.SoLieuQuanTrac.MaTram == ma_tram)
                     .order_by(M.SoLieuQuanTrac.ThoiGianDo.desc(), M.SoLieuQuanTrac.MaSoLieu.desc()).limit(1))


def tong_quan(db: Session):
    """Danh sách thiết bị đang dùng kèm số liệu mới nhất và trạng thái kết nối."""
    t = now()
    out = []
    for tr in ds_tram(db, True):
        out.append(dict(tram=tr, moi=moi_nhat(db, tr.MaTram), mat_ket_noi=mat_ket_noi(db, tr, t)))
    return out


def so_lieu(db: Session, ma_tram: int, tu, den, chi_vuot=False, toi_da=2000):
    yeu_cau(tu <= den, "Từ thời điểm phải trước đến thời điểm.")
    s = (select(M.SoLieuQuanTrac).where(M.SoLieuQuanTrac.MaTram == ma_tram, M.SoLieuQuanTrac.ThoiGianDo >= tu,
                                        M.SoLieuQuanTrac.ThoiGianDo <= den)
         .order_by(M.SoLieuQuanTrac.ThoiGianDo.desc(), M.SoLieuQuanTrac.MaSoLieu.desc()).limit(toi_da))
    if chi_vuot:
        s = s.where(M.SoLieuQuanTrac.VuotNguong == True)  # noqa: E712
    return db.scalars(s).all()


def dem_canh_bao(db: Session):
    """Cho trang chính: số thiết bị đang vượt ngưỡng và số thiết bị mất kết nối."""
    tq = tong_quan(db)
    return (sum(1 for x in tq if x["moi"] and x["moi"].VuotNguong and not x["mat_ket_noi"]),
            sum(1 for x in tq if x["mat_ket_noi"]))


def bieu_do_svg(rows, nguong_kk, nguong_tds, w=900, h=240):
    """Vẽ biểu đồ đường bằng SVG (không cần Internet, không cần thư viện JS)."""
    if not rows:
        return ""
    rows = sorted(rows, key=lambda r: r.ThoiGianDo)
    t0, t1 = rows[0].ThoiGianDo, rows[-1].ThoiGianDo
    span = max((t1 - t0).total_seconds(), 1)
    vmax = max([r.KhongKhiPPM for r in rows] + [r.TdsPPM for r in rows] + [nguong_kk, nguong_tds]) * 1.1
    L, R, T, B = 50, 10, 10, 28
    W, H = w - L - R, h - T - B

    def X(t):
        return L + W * (t - t0).total_seconds() / span

    def Y(v):
        return T + H - H * v / vmax

    def line(vals, color, dash=""):
        pts = " ".join("%.1f,%.1f" % (X(r.ThoiGianDo), Y(v)) for r, v in vals)
        return '<polyline fill="none" stroke="%s" stroke-width="2" %s points="%s"/>' % (color, dash, pts)

    g = ['<svg viewBox="0 0 %d %d" class="chart" xmlns="http://www.w3.org/2000/svg">' % (w, h),
         '<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#9fb4b0"/>' % (L, T, W, H)]
    for k in range(5):
        v = vmax * k / 4
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#dbe4e2"/>' % (L, L + W, Y(v), Y(v)))
        g.append('<text x="%d" y="%.1f" font-size="10" text-anchor="end" fill="#1d2a2a">%d</text>' % (L - 4, Y(v) + 4, v))
    for k in range(5):
        t = t0 + (t1 - t0) * k / 4
        anchor = "start" if k == 0 else ("end" if k == 4 else "middle")
        g.append('<text x="%.1f" y="%d" font-size="10" text-anchor="%s" fill="#1d2a2a">%s</text>' % (X(t), h - 8, anchor, t.strftime("%H:%M")))
    g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#c0392b" stroke-dasharray="6 4"/>' % (L, L + W, Y(nguong_kk), Y(nguong_kk)))
    if nguong_tds != nguong_kk:
        g.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="#e67e22" stroke-dasharray="6 4"/>' % (L, L + W, Y(nguong_tds), Y(nguong_tds)))
    g.append(line([(r, r.KhongKhiPPM) for r in rows], "#2e6da4"))
    g.append(line([(r, r.TdsPPM) for r in rows], "#1f6f43"))
    for r in rows:
        if r.VuotNguong:
            v = r.KhongKhiPPM if r.KhongKhiPPM > nguong_kk else r.TdsPPM
            g.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#c0392b"/>' % (X(r.ThoiGianDo), Y(v)))
    g.append("</svg>")
    return "".join(g)


# ---------------- UC09: quản lý thiết bị (cán bộ) ----------------
def sinh_khoa():
    return secrets.token_urlsafe(9)


def luu_tram(db: Session, ma, ma_thiet_bi, ten, ma_dia_ban, vi_do, kinh_do, nguong_kk, nguong_tds, dang_dung):
    """Trả về (thiết bị, khóa mới hoặc None). Thiết bị mới được cấp khóa; khóa chỉ hiển thị một lần."""
    ma_thiet_bi = text_req(ma_thiet_bi, "mã thiết bị", 20).upper()
    yeu_cau(MA_RE.match(ma_thiet_bi), "Mã thiết bị chỉ gồm chữ, số, gạch ngang, gạch dưới (2–20 ký tự).")
    ten = text_req(ten, "tên thiết bị", 100)
    yeu_cau(ma_dia_ban, "Vui lòng chọn phường/xã đặt thiết bị.")
    trung = select(func.count()).select_from(M.TramQuanTrac).where(M.TramQuanTrac.MaThietBi == ma_thiet_bi)
    if ma:
        trung = trung.where(M.TramQuanTrac.MaTram != int(ma))
    yeu_cau(db.scalar(trung) == 0, "Mã thiết bị đã tồn tại.")

    def so(v, ten_, lo, hi, bat_buoc):
        if v in (None, ""):
            yeu_cau(not bat_buoc, "Vui lòng nhập %s." % ten_)
            return None
        try:
            x = float(str(v).replace(",", "."))
        except ValueError:
            x = None
        yeu_cau(x is not None and lo < x <= hi, "%s không hợp lệ." % ten_.capitalize())
        return x

    vd, kd = so(vi_do, "vĩ độ", -90, 90, False), so(kinh_do, "kinh độ", -180, 180, False)
    ng1 = so(nguong_kk, "ngưỡng không khí", 0, TT.KHI_TOI_DA_PPM, True)
    ng2 = so(nguong_tds, "ngưỡng TDS", 0, TT.TDS_TOI_DA_PPM, True)
    khoa = None
    if ma:
        o = db.get(M.TramQuanTrac, int(ma))
        yeu_cau(o, "Không tìm thấy thiết bị.")
    else:
        khoa = sinh_khoa()
        o = M.TramQuanTrac(KhoaBam=bam(khoa))
    o.MaThietBi, o.TenTram, o.MaDiaBan = ma_thiet_bi, ten, int(ma_dia_ban)
    o.ViDo, o.KinhDo, o.NguongKhongKhi, o.NguongTDS, o.DangSuDung = vd, kd, ng1, ng2, bool(dang_dung)
    db.add(o)
    db.commit()
    return o, khoa


def cap_khoa_moi(db: Session, ma: int):
    o = db.get(M.TramQuanTrac, ma)
    yeu_cau(o, "Không tìm thấy thiết bị.")
    khoa = sinh_khoa()
    o.KhoaBam = bam(khoa)
    db.commit()
    return o, khoa
