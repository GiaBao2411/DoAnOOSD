# =====================================================================
#  TRẠM QUAN TRẮC MÔI TRƯỜNG (Module M8) — Raspberry Pi Pico 2, MicroPython
#  PHƯƠNG ÁN DỰ PHÒNG: bản GỬI QUA CÁP USB cho mạch không WiFi (Pico 2). Nạp vào mạch với tên main.py.
#  Đồ án: Cổng báo cáo sự cố môi trường và xử lý hiện trường
#  Sinh viên: Huỳnh Gia Bảo - 1250080014
#
#  Cảm biến:
#    - MQ135 (chất lượng không khí)  -> chân GP26 (ADC0), qua mạch chia áp 10k/20k
#    - TDS   (chất rắn hòa tan, nước) -> chân GP27 (ADC1), nối thẳng
#  Mỗi chu kỳ, trạm in ra cổng USB một dòng:
#    DATA {"ma_thiet_bi": "TRAM01", "khoa": "...", "khong_khi_ppm": 452.3, "tds_ppm": 236.0}
#  Chương trình cầu nối trên máy tính (lệnh: python tools\cau_noi_usb.py)
#  đọc dòng này và gửi lên web /api/tram/so-lieu. Các dòng khác (bắt đầu bằng #) chỉ để xem.
#  Trên Wokwi: 2 cảm biến được thay bằng 2 BIẾN TRỞ, dòng DATA hiện ở ô Serial.
# =====================================================================
import time
import json
from machine import ADC, Pin

# ---------------- CẤU HÌNH ----------------
MA_TRAM = "TRAM01"             # mã thiết bị (MaThietBi trong bảng TramQuanTrac)
KHOA_TRAM = "KhoaTram01"       # khóa của trạm (TRAM01 mẫu); trạm thêm mới thì lấy khóa ở Danh mục > Trạm quan trắc
CHU_KY_GIAY = 10               # bao nhiêu giây đo và gửi 1 lần

NGUONG_KHONG_KHI_PPM = 1000    # chỉ để in cảnh báo tại trạm (máy chủ dùng ngưỡng riêng của trạm)
NGUONG_TDS_PPM = 1000

# ---------------- CHÂN KẾT NỐI ----------------
adc_khi = ADC(26)              # GP26 = ADC0 <- MQ135 (qua chia áp)
adc_nuoc = ADC(27)             # GP27 = ADC1 <- TDS
led_tren_mach = Pin("LED", Pin.OUT)  # đèn có sẵn trên mạch, nháy mỗi lần gửi

# ---------------- HẰNG SỐ CẢM BIẾN ----------------
V_ADC = 3.3                    # Pico đọc điện áp 0 - 3.3V
HE_SO_CHIA_AP_KHI = 1.5        # MQ135 qua chia áp 10k (trên) + 20k (dưới): V_that = V_doc * (10+20)/20
V_NGUON_MQ135 = 5.0
RL_MQ135 = 10.0                # điện trở tải trên module MQ135 (kΩ)
R0_MQ135 = 76.63               # điện trở chuẩn trong không khí sạch (kΩ) — chạy hieu_chuan.py để tính, rồi sửa số này
A_MQ135, B_MQ135 = 116.6020682, 2.769034857   # hệ số đường cong CO2 trong datasheet MQ135
KHI_TOI_DA_PPM = 5000.0        # giới hạn (ngoài dải đo tin cậy của MQ135)
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
    rs = max((V_NGUON_MQ135 - v) / v * RL_MQ135, 0.01)
    ppm = A_MQ135 * (rs / R0_MQ135) ** (-B_MQ135)
    return min(ppm, KHI_TOI_DA_PPM)


def tinh_tds_ppm(v):
    """Công thức chuẩn của cảm biến TDS (có bù nhiệt độ)."""
    v_bu = v / (1.0 + 0.02 * (NHIET_DO_NUOC - 25.0))
    return (133.42 * v_bu ** 3 - 255.86 * v_bu ** 2 + 857.39 * v_bu) * 0.5 * HE_SO_TDS


# ---------------- CHƯƠNG TRÌNH CHÍNH ----------------
print("# === TRAM QUAN TRAC %s khoi dong (gui qua USB) ===" % MA_TRAM)
lan_do = 0
while True:
    lan_do += 1
    v_khi = doc_dien_ap(adc_khi)
    v_nuoc = doc_dien_ap(adc_nuoc)
    khi_ppm = tinh_khong_khi_ppm(v_khi)
    tds_ppm = tinh_tds_ppm(v_nuoc)
    vuot = khi_ppm > NGUONG_KHONG_KHI_PPM or tds_ppm > NGUONG_TDS_PPM

    print("# [Lan %d] Khong khi: %.0f ppm (%.2f V) | Nuoc TDS: %.0f ppm (%.2f V) %s" % (
        lan_do, khi_ppm, v_khi, tds_ppm, v_nuoc, "VUOT NGUONG!" if vuot else "binh thuong"))
    goi = {"ma_thiet_bi": MA_TRAM, "khoa": KHOA_TRAM,
           "khong_khi_ppm": round(khi_ppm, 1), "tds_ppm": round(tds_ppm, 1)}
    led_tren_mach.on()
    print("DATA " + json.dumps(goi))      # dòng này được chương trình cầu nối gửi lên web
    led_tren_mach.off()
    time.sleep(CHU_KY_GIAY)
