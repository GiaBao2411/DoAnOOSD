"""LuuTruTepService — module M3: kiểm tra tệp, vùng tải lên tạm và vùng bằng chứng lâu dài."""
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from .. import config
from .common import NghiepVuError, tham_so, yeu_cau
from ..db import now

DINH_DANG = {".jpg": "jpg", ".jpeg": "jpg", ".png": "png", ".mp4": "mp4"}


@dataclass
class TepTam:
    duong_dan: Path      # vị trí trong vùng tạm
    ten_goc: str
    loai: str            # jpg | png | mp4
    kich_thuoc: int


def _dung_chu_ky(loai: str, dau: bytes) -> bool:
    if loai == "jpg":
        return dau[:3] == b"\xff\xd8\xff"
    if loai == "png":
        return dau[:8] == b"\x89PNG\r\n\x1a\n"
    if loai == "mp4":
        return dau[4:8] == b"ftyp"
    return False


def tai_len_tam(db: Session, uploads) -> list:
    """Kiểm tra định dạng, dung lượng, số lượng; lưu vào vùng tạm. Lỗi thì xóa các tệp đã lưu."""
    uploads = [u for u in (uploads or []) if u is not None and getattr(u, "filename", "")]
    yeu_cau(len(uploads) <= tham_so(db, "SO_TEP_TOI_DA"),
            "Chỉ được gửi tối đa %d tệp." % tham_so(db, "SO_TEP_TOI_DA"))
    config.UPLOAD_TMP.mkdir(parents=True, exist_ok=True)
    don_vung_tam()
    ket_qua = []
    try:
        for u in uploads:
            ext = os.path.splitext(u.filename)[1].lower()
            loai = DINH_DANG.get(ext)
            yeu_cau(loai, "Tệp “%s” không đúng định dạng (chỉ nhận jpg, png, mp4)." % u.filename)
            gioi_han = tham_so(db, "VIDEO_TOI_DA_MB" if loai == "mp4" else "ANH_TOI_DA_MB") * 1024 * 1024
            dich = config.UPLOAD_TMP / ("%s.%s" % (uuid.uuid4().hex, loai))
            kich_thuoc = 0
            dau = b""
            with open(dich, "wb") as f:
                while True:
                    khoi = u.file.read(1024 * 1024)
                    if not khoi:
                        break
                    if not dau:
                        dau = khoi[:16]
                    kich_thuoc += len(khoi)
                    if kich_thuoc > gioi_han:
                        f.close()
                        dich.unlink(missing_ok=True)
                        raise NghiepVuError("Tệp “%s” vượt quá %d MB." % (u.filename, gioi_han // 1024 // 1024))
                    f.write(khoi)
            ket_qua.append(TepTam(dich, os.path.basename(u.filename)[:255], loai, kich_thuoc))
            if kich_thuoc == 0 or not _dung_chu_ky(loai, dau):
                raise NghiepVuError("Tệp “%s” rỗng hoặc không phải ảnh/video hợp lệ." % u.filename)
    except Exception:
        xoa_tam(ket_qua)
        raise
    return ket_qua


def chuyen_sang_lau_dai(tep: TepTam) -> str:
    """Chuyển tệp từ vùng tạm sang vùng bằng chứng lâu dài; trả về đường dẫn tương đối để lưu CSDL."""
    t = now()
    thu_muc = config.UPLOAD_EVIDENCE / ("%04d" % t.year) / ("%02d" % t.month)
    thu_muc.mkdir(parents=True, exist_ok=True)
    dich = thu_muc / tep.duong_dan.name
    shutil.move(str(tep.duong_dan), str(dich))
    return dich.relative_to(config.UPLOAD_DIR).as_posix()


def don_vung_tam(gio=24):
    """Dọn tệp nằm ở vùng tạm quá 24 giờ (tải lên dở dang, không thành báo cáo) — mục 4.6 của báo cáo."""
    import time
    if not config.UPLOAD_TMP.exists():
        return 0
    han, dem = time.time() - gio * 3600, 0
    for f in config.UPLOAD_TMP.iterdir():
        try:
            if f.is_file() and f.name != ".gitkeep" and f.stat().st_mtime < han:
                f.unlink()
                dem += 1
        except OSError:
            pass
    return dem


def xoa_tam(teps):
    for t in teps or []:
        try:
            Path(t.duong_dan).unlink(missing_ok=True)
        except OSError:
            pass


def xoa_lau_dai(duong_dan_tuong_doi_list):
    for p in duong_dan_tuong_doi_list or []:
        try:
            (config.UPLOAD_DIR / p).unlink(missing_ok=True)
        except OSError:
            pass


def duong_dan_that(duong_dan_tuong_doi: str) -> Path:
    p = (config.UPLOAD_DIR / duong_dan_tuong_doi).resolve()
    yeu_cau(str(p).startswith(str(config.UPLOAD_DIR.resolve())), "Đường dẫn tệp không hợp lệ.")
    return p
