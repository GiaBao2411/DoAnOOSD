# =====================================================================
#  TRẠM QUAN TRẮC MÔI TRƯỜNG (Module M8) — Raspberry Pi Pico W, MicroPython
#  Bản GỬI QUA WiFi (bản chính). Nạp vào Pico W với tên main.py.
#  Đồ án: Cổng báo cáo sự cố môi trường và xử lý hiện trường
#  Sinh viên: Huỳnh Gia Bảo - 1250080014
#
#  Cảm biến:
#    - MQ135 (chất lượng không khí)  -> chân GP26 (ADC0), qua mạch chia áp 10k/20k
#    - TDS   (chất rắn hòa tan, nước) -> chân GP27 (ADC1), nối thẳng
#  Trên Wokwi: 2 cảm biến được thay bằng 2 BIẾN TRỞ (vặn để giả lập ô nhiễm).
#  Chạy trên mạch thật: giữ nguyên code, chỉ sửa WIFI_SSID, WIFI_PASS, SERVER_URL.
# =====================================================================
import time
import json
import network
from machine import ADC, Pin

try:
    import requests            # MicroPython bản mới
except ImportError:
    import urequests as requests  # MicroPython bản cũ

# ---------------- CẤU HÌNH ----------------
WIFI_SSID = "Wokwi-GUEST"      # Wokwi: mạng WiFi ảo có sẵn. Mạch thật: tên WiFi nhà bạn
WIFI_PASS = ""                 # Wokwi: để trống. Mạch thật: mật khẩu WiFi
MA_TRAM = "TRAM01"             # mã thiết bị (MaThietBi trong bảng TramQuanTrac)
KHOA_TRAM = "KhoaTram01"      # khóa của trạm (TRAM01 mẫu); trạm thêm mới thì lấy khóa ở Danh mục > Trạm quan trắc

# Địa chỉ nhận dữ liệu (xem README.md mục 3):
#  - Thử WiFi trên Wokwi: "http://httpbin.org/post" (trang thử nghiệm, chỉ trả lại gói đã nhận)
#  - Pico W thật cùng WiFi với laptop: "http://<IP laptop>:8000/api/tram/so-lieu" (chạy chay_he_thong.bat)
#  - Để trống "" nếu chỉ muốn in số liệu ra màn hình, không gửi.
SERVER_URL = "http://192.168.1.10:8000/api/tram/so-lieu"   # đổi 192.168.1.10 thành IPv4 laptop (backend in ra khi chạy)

CHU_KY_GIAY = 10               # bao nhiêu giây đọc và gửi 1 lần

NGUONG_KHONG_KHI_PPM = 1000    # vượt ngưỡng này in 'VUOT NGUONG' (máy chủ dùng ngưỡng riêng của trạm)
NGUONG_TDS_PPM = 1000          # vượt ngưỡng này coi là nước ô nhiễm (ngưỡng demo, chỉnh được)

# ---------------- CHÂN KẾT NỐI ----------------
adc_khi = ADC(26)              # GP26 = ADC0 <- MQ135
adc_nuoc = ADC(27)             # GP27 = ADC1 <- TDS
led_tren_mach = Pin("LED", Pin.OUT)  # đèn trên Pico W, nháy mỗi lần gửi

# ---------------- HẰNG SỐ CẢM BIẾN ----------------
V_ADC = 3.3                    # Pico đọc điện áp 0 - 3.3V
HE_SO_CHIA_AP_KHI = 1.5        # MQ135 qua chia áp 10k (trên) + 20k (dưới): V_that = V_doc * (10+20)/20
V_NGUON_MQ135 = 5.0
RL_MQ135 = 10.0                # điện trở tải trên module MQ135 (kΩ)
R0_MQ135 = 76.63               # điện trở chuẩn trong không khí sạch (kΩ) — chạy hieu_chuan.py để tính, rồi sửa số này
A_MQ135, B_MQ135 = 116.6020682, 2.769034857   # hệ số đường cong CO2 trong datasheet MQ135
KHI_TOI_DA_PPM = 5000.0        # giới hạn hiển thị (ngoài dải đo tin cậy của MQ135)
NHIET_DO_NUOC = 25.0           # TDS phụ thuộc nhiệt độ; chưa có cảm biến nhiệt thì giả sử 25°C
HE_SO_TDS = 1.0                # hệ số hiệu chuẩn TDS (chạy hieu_chuan.py để tính, rồi sửa số này)


def doc_dien_ap(adc, so_lan=10):
    """Đọc trung bình nhiều lần cho ổn định, trả về điện áp (V)."""
    adc.read_u16()                 # bỏ lần đọc đầu sau khi đổi kênh ADC (tránh lẫn số của cảm biến kia)
    time.sleep_ms(2)
    tong = 0
    for _ in range(so_lan):
        tong += adc.read_u16()
        time.sleep_ms(5)
    return tong / so_lan * V_ADC / 65535


def tinh_khong_khi_ppm(v_doc):
    """Đổi điện áp MQ135 ra nồng độ khí ước lượng (ppm, quy đổi theo CO2)."""
    v = max(v_doc * HE_SO_CHIA_AP_KHI, 0.01)
    rs = (V_NGUON_MQ135 - v) / v * RL_MQ135
    rs = max(rs, 0.01)
    ppm = A_MQ135 * (rs / R0_MQ135) ** (-B_MQ135)
    return min(ppm, KHI_TOI_DA_PPM)   # quá dải đo của MQ135 thì giữ ở mức tối đa


def tinh_tds_ppm(v):
    """Công thức chuẩn của cảm biến TDS (có bù nhiệt độ)."""
    v_bu = v / (1.0 + 0.02 * (NHIET_DO_NUOC - 25.0))
    return (133.42 * v_bu ** 3 - 255.86 * v_bu ** 2 + 857.39 * v_bu) * 0.5 * HE_SO_TDS


def ket_noi_wifi(cho_toi_da=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    print("Dang ket noi WiFi '%s' ..." % WIFI_SSID)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    for _ in range(cho_toi_da * 2):
        if wlan.isconnected():
            print("Da ket noi WiFi. IP cua tram:", wlan.ifconfig()[0])
            return wlan
        led_tren_mach.toggle()
        time.sleep(0.5)
    print("!! Khong ket noi duoc WiFi — van do va in so lieu, se thu lai sau.")
    return wlan


def gui_so_lieu(goi):
    """Gửi gói số liệu dạng JSON tới SERVER_URL. Trả về True nếu gửi thành công."""
    if not SERVER_URL:
        return False
    try:
        r = requests.post(SERVER_URL, data=json.dumps(goi),
                          headers={"Content-Type": "application/json"})
        ok = 200 <= r.status_code < 300
        print("   -> Gui toi may chu: HTTP", r.status_code, "(thanh cong)" if ok else "(loi)")
        r.close()
        return ok
    except Exception as e:  # mất mạng, máy chủ tắt...
        print("   -> Gui that bai:", e)
        return False


# ---------------- CHƯƠNG TRÌNH CHÍNH ----------------
print("=== TRAM QUAN TRAC %s khoi dong ===" % MA_TRAM)
wlan = ket_noi_wifi()
lan_do = 0

while True:
    lan_do += 1
    v_khi = doc_dien_ap(adc_khi)
    v_nuoc = doc_dien_ap(adc_nuoc)
    khi_ppm = tinh_khong_khi_ppm(v_khi)
    tds_ppm = tinh_tds_ppm(v_nuoc)

    khi_vuot = khi_ppm > NGUONG_KHONG_KHI_PPM
    nuoc_vuot = tds_ppm > NGUONG_TDS_PPM

    print("\n[Lan %d] Khong khi: %7.0f ppm (%.2f V) %s | Nuoc TDS: %6.0f ppm (%.2f V) %s" % (
        lan_do, khi_ppm, v_khi, "VUOT NGUONG!" if khi_vuot else "binh thuong",
        tds_ppm, v_nuoc, "VUOT NGUONG!" if nuoc_vuot else "binh thuong"))

    goi = {
        "ma_thiet_bi": MA_TRAM,
        "khoa": KHOA_TRAM,
        "khong_khi_ppm": round(khi_ppm, 1),
        "tds_ppm": round(tds_ppm, 1),
        "vuot_nguong_khong_khi": khi_vuot,
        "vuot_nguong_nuoc": nuoc_vuot,
    }
    print("   Goi du lieu:", json.dumps({k: v for k, v in goi.items() if k != "khoa"}))

    if SERVER_URL:
        if not wlan.isconnected():
            wlan = ket_noi_wifi()
        if wlan.isconnected():
            led_tren_mach.on()
            gui_so_lieu(goi)
            led_tren_mach.off()

    time.sleep(CHU_KY_GIAY)
