from machine import ADC
import time

adc_khi, adc_nuoc = ADC(26), ADC(27)


def doc_tb(adc, giay):
    tong, n = 0.0, 0
    adc.read_u16(); time.sleep_ms(2)
    t = time.time()
    while time.time() - t < giay:
        tong += adc.read_u16() * 3.3 / 65535
        n += 1
        time.sleep_ms(100)
    return tong / n


print("=== BƯỚC 1: MQ135 ===")
print("Cảm biến phải cắm điện ít nhất 30 phút. Đặt chỗ thoáng (gần cửa sổ), không thổi khói.")
input("Sẵn sàng thì bấm Enter...")
print("Đang đo 60 giây...")
v_ao = doc_tb(adc_khi, 60) * 1.5
v_ao = max(v_ao, 0.01)
rs = (5.0 - v_ao) / v_ao * 10.0
r0 = rs * 1.5885
print("AO = %.2f V, Rs = %.1f kΩ" % (v_ao, rs))
print(">>> Sửa trong main: R0_MQ135 = %.1f" % r0)

print("\n=== BƯỚC 2: TDS ===")
print("Pha dung dịch chuẩn: 1 gam muối ăn (khoảng 1/5 thìa cà phê) vào 1 lít nước lọc, khuấy tan.")
print("Dung dịch này khoảng 1000 ppm. Nếu có bút đo TDS thì dùng số của bút cho chính xác hơn.")
chuan = input("Nhập ppm của dung dịch chuẩn (Enter = 1000): ").strip()
chuan = float(chuan) if chuan else 1000.0
input("Nhúng que TDS vào dung dịch, đợi 10 giây rồi bấm Enter...")
v = doc_tb(adc_nuoc, 20)
ppm_do = (133.42 * v ** 3 - 255.86 * v ** 2 + 857.39 * v) * 0.5
print("TDS = %.2f V -> đo được %.0f ppm (chưa hiệu chuẩn)" % (v, ppm_do))
if ppm_do < 5:
    print("Số quá thấp: kiểm tra que đã nhúng ngập chưa, dây A -> chân 32, + -> 3V3, - -> GND.")
else:
    print(">>> Sửa trong main: HE_SO_TDS = %.3f" % (chuan / ppm_do))
print("\nXong. Sửa 2 số trên trong file main bạn đang dùng, lưu lại rồi chạy lại.")
