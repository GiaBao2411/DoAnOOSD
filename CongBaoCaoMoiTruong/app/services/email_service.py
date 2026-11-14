import html
import logging
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from .. import config

log = logging.getLogger("email")
MAU_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")


def da_cau_hinh() -> bool:
    return bool(config.SMTP_USER and config.SMTP_PASSWORD)


def hop_le(email: str) -> bool:
    return bool(email) and len(email) <= 254 and MAU_EMAIL.fullmatch(email) is not None


def _gui_smtp(den: str, tieu_de: str, van_ban: str, trang_html: str):
    msg = EmailMessage()
    msg["Subject"] = tieu_de
    msg["From"] = formataddr((config.SMTP_TEN_GUI, config.SMTP_USER))
    msg["To"] = den
    msg.set_content(van_ban)
    msg.add_alternative(trang_html, subtype="html")
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
        if config.SMTP_TLS:
            s.starttls(context=ssl.create_default_context())
        s.login(config.SMTP_USER, config.SMTP_PASSWORD)
        s.send_message(msg)


def _gui_an_toan(den: str, tieu_de: str, van_ban: str, trang_html: str):
    if not da_cau_hinh():
        log.warning("Chưa cấu hình SMTP_USER / SMTP_PASSWORD trong .env — bỏ qua gửi thư tới %s", den)
        return
    try:
        _gui_smtp(den, tieu_de, van_ban, trang_html)
        log.info("Đã gửi thư '%s' tới %s", tieu_de, den)
    except Exception as e:
        log.error("Gửi thư tới %s thất bại: %s", den, e)
        print("[EMAIL] Gửi thư tới %s thất bại: %s" % (den, e))


def _khung(noi_dung_html: str) -> str:
    return ('<div style="font-family:Arial,sans-serif;font-size:15px;color:#1d2a2a;max-width:560px">'
            '<p style="font-size:17px;font-weight:bold;color:#1f5753;margin:0 0 14px">Cổng báo cáo sự cố môi trường</p>'
            + noi_dung_html +
            '<p style="font-size:13px;margin-top:22px">Thư này được gửi tự động, vui lòng không trả lời.</p></div>')


def gui_ma_bao_cao(den: str, ma: str, ngay_gui: str, phuong: str, mo_ta: str):
    link = "%s/tra-cuu?ma=%s" % (config.DIA_CHI_WEB.rstrip("/"), ma)
    tieu_de = "Mã báo cáo sự cố của bạn: %s" % ma
    van_ban = ("Cảm ơn bạn đã gửi phản ánh.\n\nMã báo cáo: %s\nNgày gửi: %s\nPhường/xã: %s\nNội dung: %s\n\n"
               "Dùng mã này để tra cứu tiến độ và bổ sung thông tin khi được yêu cầu:\n%s\n"
               % (ma, ngay_gui, phuong, mo_ta, link))
    h = html.escape
    trang = _khung(
        '<p>Cảm ơn bạn đã gửi phản ánh. Đây là mã báo cáo của bạn:</p>'
        '<p style="font-size:26px;font-weight:bold;letter-spacing:1px;margin:10px 0 16px">%s</p>'
        '<table style="border-collapse:collapse;font-size:14px">'
        '<tr><td style="padding:3px 14px 3px 0"><b>Ngày gửi</b></td><td>%s</td></tr>'
        '<tr><td style="padding:3px 14px 3px 0"><b>Phường/xã</b></td><td>%s</td></tr>'
        '<tr><td style="padding:3px 14px 3px 0;vertical-align:top"><b>Nội dung</b></td><td>%s</td></tr></table>'
        '<p style="margin-top:18px">Dùng mã này để tra cứu tiến độ và bổ sung thông tin khi được yêu cầu:</p>'
        '<p><a href="%s" style="background:#2b706b;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;'
        'display:inline-block">Tra cứu báo cáo %s</a></p>'
        % (h(ma), h(ngay_gui), h(phuong), h(mo_ta), h(link), h(ma)))
    _gui_an_toan(den, tieu_de, van_ban, trang)


def gui_lai_ma(den: str, ds: list):
    tieu_de = "Các mã báo cáo sự cố bạn đã gửi"
    goc = config.DIA_CHI_WEB.rstrip("/")
    van_ban = "Các báo cáo đã gửi bằng email này:\n\n" + "\n".join(
        "- %s (gửi %s, %s) — %s: %s/tra-cuu?ma=%s" % (m, n, p, t, goc, m) for m, n, p, t in ds)
    h = html.escape
    dong = "".join(
        '<tr><td style="padding:6px 14px 6px 0"><a href="%s/tra-cuu?ma=%s" style="color:#1f5753;font-weight:bold">%s</a></td>'
        '<td style="padding:6px 14px 6px 0">%s</td><td style="padding:6px 14px 6px 0">%s</td><td>%s</td></tr>'
        % (h(goc), h(m), h(m), h(n), h(p), h(t)) for m, n, p, t in ds)
    trang = _khung('<p>Đây là các báo cáo bạn đã gửi bằng địa chỉ email này. Bấm vào mã để tra cứu.</p>'
                   '<table style="border-collapse:collapse;font-size:14px"><tr>'
                   '<th align="left">Mã báo cáo</th><th align="left">Ngày gửi</th><th align="left">Phường/xã</th>'
                   '<th align="left">Trạng thái</th></tr>%s</table>' % dong)
    _gui_an_toan(den, tieu_de, van_ban, trang)
