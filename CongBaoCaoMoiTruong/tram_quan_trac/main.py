import time
import json
import network
from machine import ADC, Pin

try:
    import requests
except ImportError:
    import urequests as requests

WIFI_SSID = "Wokwi-GUEST"
WIFI_PASS = ""
MA_TRAM = "TRAM01"
KHOA_TRAM = "KhoaTram01"

SERVER_URL = "http://192.168.1.10:8000/api/tram/so-lieu"

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
    rs = (V_NGUON_MQ135 - v) / v * RL_MQ135
    rs = max(rs, 0.01)
    ppm = A_MQ135 * (rs / R0_MQ135) ** (-B_MQ135)
    return min(ppm, KHI_TOI_DA_PPM)


def tinh_tds_ppm(v):
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
    if not SERVER_URL:
        return False
    try:
        r = requests.post(SERVER_URL, data=json.dumps(goi),
                          headers={"Content-Type": "application/json"})
        ok = 200 <= r.status_code < 300
        print("   -> Gui toi may chu: HTTP", r.status_code, "(thanh cong)" if ok else "(loi)")
        r.close()
        return ok
    except Exception as e:
        print("   -> Gui that bai:", e)
        return False


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
