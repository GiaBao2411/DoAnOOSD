"""Phần dùng chung của tầng nghiệp vụ: lỗi nghiệp vụ, chuyển trạng thái + ghi lịch sử, tham số, phân trang."""
import hashlib
import hmac
import math
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import models as M
from .. import trang_thai as TT
from ..config import PAGE_SIZE
from ..db import now
from ..telemetry import danh_dau


class NghiepVuError(Exception):
    """Vi phạm quy tắc nghiệp vụ — hiển thị cho người dùng."""


def yeu_cau(dieu_kien, thong_bao):
    if not dieu_kien:
        raise NghiepVuError(thong_bao)


# ---------- băm mật khẩu / mã bí mật (PBKDF2-SHA256) ----------
def bam(gia_tri: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", gia_tri.encode("utf-8"), bytes.fromhex(salt), 200_000)
    return "pbkdf2$200000$%s$%s" % (salt, h.hex())


def kiem_tra_bam(gia_tri: str, chuoi_bam: str) -> bool:
    try:
        _, it, salt, h = chuoi_bam.split("$")
        h2 = hashlib.pbkdf2_hmac("sha256", gia_tri.encode("utf-8"), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(h2.hex(), h)
    except Exception:
        return False


# ---------- chống dò mật khẩu / mã bí mật: sai 5 lần thì khóa 15 phút (bộ nhớ máy chủ, dữ liệu tạm) ----------
_sai = {}


def bi_khoa_tam(khoa: str) -> bool:
    lan, den = _sai.get(khoa, (0, None))
    return den is not None and den > now()


def ghi_sai(khoa: str):
    lan = _sai.get(khoa, (0, None))[0] + 1
    _sai[khoa] = (0, now() + timedelta(minutes=15)) if lan >= 5 else (lan, None)


def xoa_sai(khoa: str):
    _sai.pop(khoa, None)


def so_lan_con(khoa: str) -> int:
    return 5 - _sai.get(khoa, (0, None))[0]


# ---------- tham số hệ thống ----------
def tham_so(db: Session, ma: str) -> int:
    ts = db.get(M.ThamSoHeThong, ma)
    if ts is None:
        return int(dict((a, b) for a, b, _ in TT.THAM_SO_MAC_DINH)[ma])
    return int(ts.GiaTri)


# ---------- chuyển trạng thái báo cáo + lịch sử (BR15) ----------
def chuyen_trang_thai(db: Session, bc: M.BaoCaoSuCo, moi: str, ma_tk, ghi_chu: str = None):
    cu = bc.TrangThai
    yeu_cau(moi in TT.BC_CHUYEN.get(cu, []),
            "Không thể chuyển báo cáo %s từ trạng thái “%s” sang “%s”." % (bc.MaTraCuu, cu, moi))
    bc.TrangThai = moi
    db.add(M.LichSuTrangThai(MaBaoCao=bc.MaBaoCao, TrangThaiCu=cu, TrangThaiMoi=moi, ThoiGian=now(),
                             MaTaiKhoan=ma_tk, GhiChu=(ghi_chu or "")[:500] or None))
    danh_dau("bao_cao.chuyen_trang_thai", ma_tra_cuu=bc.MaTraCuu, tu=cu or "", den=moi)


def kiem_tra_phien_ban(ban_ghi, rv_gui: str):
    """Chống cập nhật đè: so RowVersion lúc mở trang với hiện tại (chỉ có hiệu lực trên SQL Server)."""
    hien_tai = getattr(ban_ghi, "RowVersion", None)
    if hien_tai and rv_gui:
        yeu_cau(hien_tai.hex() == rv_gui, "Dữ liệu đã được người khác cập nhật. Vui lòng tải lại trang và thao tác lại.")


def rv(ban_ghi) -> str:
    v = getattr(ban_ghi, "RowVersion", None)
    return v.hex() if v else ""


# ---------- phân trang (SQL Server yêu cầu ORDER BY khi dùng OFFSET) ----------
class Trang:
    def __init__(self, items, trang, tong):
        self.items, self.trang, self.tong = items, trang, tong
        self.so_trang = max(1, math.ceil(tong / PAGE_SIZE))


def phan_trang(db: Session, stmt, trang: int) -> Trang:
    trang = max(1, int(trang or 1))
    tong = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = db.scalars(stmt.offset((trang - 1) * PAGE_SIZE).limit(PAGE_SIZE)).all()
    return Trang(items, trang, tong)


def parse_dt(s: str, ten: str, bat_buoc=True):
    if not s:
        yeu_cau(not bat_buoc, "Vui lòng nhập %s." % ten)
        return None
    for f in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    raise NghiepVuError("%s không đúng định dạng ngày giờ." % ten.capitalize())


def text_req(s: str, ten: str, max_len: int = None) -> str:
    s = (s or "").strip()
    yeu_cau(s, "Vui lòng nhập %s." % ten)
    if max_len:
        yeu_cau(len(s) <= max_len, "%s tối đa %d ký tự." % (ten.capitalize(), max_len))
    return s
