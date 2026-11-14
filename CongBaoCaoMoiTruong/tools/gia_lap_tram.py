"""Giả lập thiết bị đo IoT (thay cho mạch Pico thật) — gửi số liệu về web mỗi vài giây.

Cách chạy (ở thư mục gốc dự án, trong lúc web đang chạy):
    python tools/gia_lap_tram.py                       # TRAM01 và TRAM02, 10 giây/lần
    python tools/gia_lap_tram.py --tram TRAM03:KhoaTram03 --chu-ky 5
    python tools/gia_lap_tram.py --url http://192.168.1.10:8000/api/tram/so-lieu

Gói tin gửi đi giống hệt gói của mạch Pico (tram_quan_trac/main.py): ma_thiet_bi, khoa, khong_khi_ppm, tds_ppm.
Bấm Ctrl+C để dừng. Chỉ dùng thư viện có sẵn của Python.
"""
import argparse
import json
import math
import random
import time
import urllib.error
import urllib.request


def gui(url, goi):
    req = urllib.request.Request(url, data=json.dumps(goi).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, OSError) as e:
        return None, {"loi": "Không kết nối được máy chủ (%s). Web đã chạy chưa?" % e}


def main():
    ap = argparse.ArgumentParser(description="Giả lập thiết bị đo IoT")
    ap.add_argument("--url", default="http://127.0.0.1:8000/api/tram/so-lieu")
    ap.add_argument("--tram", action="append", help="MA_THIET_BI:KHOA (lặp lại để giả lập nhiều thiết bị)")
    ap.add_argument("--chu-ky", type=float, default=10, help="số giây giữa hai lần gửi")
    a = ap.parse_args()
    trams = [t.split(":", 1) for t in (a.tram or ["TRAM01:KhoaTram01", "TRAM02:KhoaTram02"])]
    print("Giả lập %d thiết bị, gửi tới %s mỗi %g giây. Ctrl+C để dừng." % (len(trams), a.url, a.chu_ky))
    rnd = random.Random()
    k = 0
    while True:
        k += 1
        for i, (ma, khoa) in enumerate(trams):
            kk = 430 + 60 * math.sin(k / 6 + i) + rnd.uniform(-20, 20)
            tds = 250 + 80 * i + rnd.uniform(-15, 15)
            if (k + 7 * i) % 30 in range(20, 25):   # thỉnh thoảng có khói / nước thải để thấy vượt ngưỡng
                kk += rnd.uniform(700, 1200)
                tds += rnd.uniform(500, 900)
            goi = {"ma_thiet_bi": ma, "khoa": khoa, "khong_khi_ppm": round(kk, 1), "tds_ppm": round(tds, 1)}
            code, kq = gui(a.url, goi)
            trang_thai = "OK" if code == 201 else "LỖI"
            print("[%s] %s  không khí %7.1f ppm  TDS %6.1f ppm  -> HTTP %s %s %s" % (
                time.strftime("%H:%M:%S"), ma, goi["khong_khi_ppm"], goi["tds_ppm"], code, trang_thai,
                "(vượt ngưỡng)" if kq.get("vuot_nguong") else kq.get("loi", "")))
        time.sleep(a.chu_ky)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng giả lập.")
