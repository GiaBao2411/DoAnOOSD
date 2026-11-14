import time
import json
from machine import ADC, Pin

MA_TRAM = "TRAM01"
KHOA_TRAM = "KhoaTram01"
CHU_KY_GIAY = 10

NGUONG_KHONG_KHI_PPM = 1000
NGUONG_TDS_PPM = 1000

adc_khi = ADC(26)
adc_nuoc = ADC(27)
led_tren_mach = Pin("LED", Pin.OUT)

V_ADC = 3.3
HE_SO_CHIA_AP_KHI = 1.5
V_NGUON_MQ135 = 5.0
RL_MQ135 = 10.0
R0_MQ135 = 76.63
A_MQ135, B_MQ135 = 116.6020682, 2.769034857
KHI_TOI_DA_PPM = 5000.0
NHIET_DO_NUOC = 25.0
HE_SO_TDS = 1.0


def doc_dien_ap(adc, so_lan=10):
    adc.read_u16()
    time.sleep_ms(2)
    tong = 0
    for _ in range(so_lan):
        tong += adc.read_u16()
        time.sleep_ms(5)
    return tong / so_lan * V_ADC / 65535


def tinh_khong_khi_ppm(v_doc):
    v = max(v_doc * HE_SO_CHIA_AP_KHI, 0.01)
    rs = max((V_NGUON_MQ135 - v) / v * RL_MQ135, 0.01)
    ppm = A_MQ135 * (rs / R0_MQ135) ** (-B_MQ135)
    return min(ppm, KHI_TOI_DA_PPM)


def tinh_tds_ppm(v):
    v_bu = v / (1.0 + 0.02 * (NHIET_DO_NUOC - 25.0))
    return (133.42 * v_bu ** 3 - 255.86 * v_bu ** 2 + 857.39 * v_bu) * 0.5 * HE_SO_TDS


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
    print("DATA " + json.dumps(goi))
    led_tren_mach.off()
    time.sleep(CHU_KY_GIAY)
