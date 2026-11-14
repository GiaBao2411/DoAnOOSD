"""Cầu nối USB — chuyển số liệu từ thiết bị đo (Pico 2 cắm cáp USB) lên web (UC13, module M8).

Thiết bị in ra cổng USB các dòng dạng:
    DATA {"ma_thiet_bi": "TRAM01", "khoa": "...", "khong_khi_ppm": 452.3, "tds_ppm": 236.0}
Chương trình này đọc từng dòng DATA và gửi HTTP POST tới /api/tram/so-lieu của web.

Cách chạy (ở thư mục gốc dự án, trong lúc web đang chạy; nhớ ĐÓNG Thonny vì Thonny giữ cổng USB):
    python tools/cau_noi_usb.py                  # tự tìm cổng của mạch Raspberry Pi Pico
    python tools/cau_noi_usb.py --cong COM5      # chỉ định cổng (xem trong Device Manager > Ports)
Rút cáp ra thì chương trình chờ và tự kết nối lại khi cắm vào. Bấm Ctrl+C để dừng.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Thiếu thư viện pyserial. Cài bằng lệnh: pip install pyserial")
    sys.exit(1)

VID_RASPBERRY_PI = 0x2E8A   # mã nhà sản xuất USB của các mạch Raspberry Pi Pico / Pico 2


def tim_cong():
    cong = list(list_ports.comports())
    for c in cong:
        if c.vid == VID_RASPBERRY_PI:
            return c.device
    return None


def gui(url, goi):
    req = urllib.request.Request(url, data=json.dumps(goi).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, OSError) as e:
        return None, {"loi": "Không kết nối được web (%s). Web đã chạy chưa?" % e}


def xu_ly_dong(dong, url, xem_tat_ca=False):
    """Xử lý một dòng đọc từ thiết bị. Trả về mã HTTP nếu là dòng DATA, ngược lại None."""
    dong = dong.strip()
    if not dong:
        return None
    if not dong.startswith("DATA "):
        if xem_tat_ca:
            print("   thiết bị:", dong)
        return None
    try:
        goi = json.loads(dong[5:])
    except ValueError:
        print("!! Dòng DATA không phải JSON hợp lệ:", dong[:120])
        return None
    code, kq = gui(url, goi)
    print("[%s] %s  không khí %7.1f ppm  TDS %6.1f ppm  -> HTTP %s %s" % (
        time.strftime("%H:%M:%S"), goi.get("ma_thiet_bi"), float(goi.get("khong_khi_ppm", 0)),
        float(goi.get("tds_ppm", 0)), code,
        "OK (vượt ngưỡng)" if code == 201 and kq.get("vuot_nguong") else ("OK" if code == 201 else kq.get("loi", "LỖI"))))
    return code


def main():
    ap = argparse.ArgumentParser(description="Cầu nối USB: thiết bị đo -> web")
    ap.add_argument("--cong", help="cổng USB của mạch, ví dụ COM5 (bỏ trống để tự tìm)")
    ap.add_argument("--url", default="http://127.0.0.1:8000/api/tram/so-lieu")
    ap.add_argument("--xem-tat-ca", action="store_true", help="in cả các dòng chú thích (#) của thiết bị")
    a = ap.parse_args()
    print("Cầu nối USB → %s. Ctrl+C để dừng." % a.url)
    bao_cho = False
    while True:
        cong = a.cong or tim_cong()
        if not cong:
            if not bao_cho:
                print("Đang chờ cắm mạch Pico vào cổng USB... (nếu đã cắm mà vẫn chờ: dùng --cong COMx)")
                bao_cho = True
            time.sleep(2)
            continue
        try:
            with serial.Serial(cong, 115200, timeout=1) as sp:
                print("Đã kết nối thiết bị ở cổng %s. Đang chờ số liệu (mỗi chu kỳ đo một dòng)..." % cong)
                bao_cho = False
                while True:
                    raw = sp.readline()
                    if raw:
                        xu_ly_dong(raw.decode("utf-8", "replace"), a.url, a.xem_tat_ca)
        except serial.SerialException as e:
            msg = str(e)
            if "denied" in msg.lower() or "PermissionError" in msg:
                print("!! Cổng %s đang bị chương trình khác giữ (thường là Thonny). Hãy đóng Thonny." % cong)
            else:
                print("!! Mất kết nối với thiết bị (%s). Thử lại sau 2 giây..." % msg[:80])
            time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng cầu nối.")
