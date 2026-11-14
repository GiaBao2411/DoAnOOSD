# kiem_tra_mach.py — Tự kiểm tra mạch MQ135 + TDS trên Raspberry Pi Pico W / Pico 2
# Cách chạy: mở Thonny, bấm Stop, mở file này rồi bấm Run (chọn "This computer").
# Không cần đồng hồ đo. Không ghi đè main.py.
from machine import ADC, Pin
import time

V_ADC = 3.3
adc_khi = ADC(26)    # GP26 (chân 31) <- điểm giữa của 10 kΩ và 20 kΩ (MQ135)
adc_nuoc = ADC(27)   # GP27 (chân 32) <- chân A của TDS


def doc(adc, so_lan=50):
    """Đọc nhiều lần, trả về (trung bình, nhỏ nhất, lớn nhất) theo volt."""
    ds = []
    for _ in range(so_lan):
        ds.append(adc.read_u16() * V_ADC / 65535)
        time.sleep_ms(20)
    return sum(ds) / len(ds), min(ds), max(ds)


def kiem_tra_nguon_5v():
    """Pico W: chân WL_GPIO2 báo có 5 V ở VBUS. Pico 2: GP24."""
    for ten in ("WL_GPIO2", 24):
        try:
            return Pin(ten, Pin.IN).value() == 1
        except Exception:
            pass
    return None


print("=" * 52)
print("KIỂM TRA MẠCH THIẾT BỊ ĐO")
print("=" * 52)

# 1. Nguồn 5 V cho MQ135
co_5v = kiem_tra_nguon_5v()
if co_5v is None:
    print("[?] Nguồn 5V (VBUS): không đọc được trên mạch này, bỏ qua.")
elif co_5v:
    print("[OK] Nguồn 5V (VBUS, chân 40): CÓ ĐIỆN.")
else:
    print("[LỖI] Nguồn 5V (VBUS): KHÔNG CÓ. Pico phải cắm qua cổng USB thì chân 40 mới có 5V.")

# 2. MQ135 qua mạch chia áp
tb, nho, lon = doc(adc_khi)
print("\nMQ135 -> GP26: trung bình %.2f V (thấp nhất %.2f, cao nhất %.2f)" % (tb, nho, lon))
print("        điện áp thật ở chân AO ≈ %.2f V" % (tb * 1.5))
loi_mq = False
if tb < 0.05:
    loi_mq = True
    print("[LỖI] Gần 0 V. Kiểm tra: dây AO -> dãy 18; điện trở 10k; dây xanh dãy 14 -> chân 31; VCC -> chân 40.")
elif tb > 3.15:
    loi_mq = True
    print("[NGUY HIỂM] Gần 3,3 V: thiếu hoặc lỏng điện trở 20k xuống GND. RÚT USB NGAY và kiểm tra lại!")
else:
    print("[OK] Điện áp vào GP26 nằm trong giới hạn an toàn (dưới 3,3 V).")
    if lon - nho > 0.3:
        print("[CHÚ Ý] Số nhảy nhiều: dây lỏng, hoặc MQ135 chưa đủ nóng (đợi 2–5 phút rồi chạy lại).")

# 3. Thử phản ứng của MQ135
if not loi_mq:
    print("\nTrong 15 giây tới, hãy THỔI hơi cồn / khói nhang vào MQ135 ...")
    goc = tb
    cao_nhat = tb
    for giay in range(15, 0, -1):
        v = doc(adc_khi, 10)[0]
        cao_nhat = max(cao_nhat, v)
        print("  còn %2d giây: GP26 = %.2f V" % (giay, v))
        time.sleep_ms(800)
    if cao_nhat - goc > 0.15:
        print("[OK] MQ135 phản ứng tốt: tăng từ %.2f V lên %.2f V." % (goc, cao_nhat))
    else:
        print("[CHÚ Ý] MQ135 hầu như không đổi. Thổi gần hơn, hoặc đợi cảm biến nóng 15–30 phút rồi thử lại.")

# 4. TDS
tb2, nho2, lon2 = doc(adc_nuoc)
print("\nTDS -> GP27: trung bình %.2f V (thấp nhất %.2f, cao nhất %.2f)" % (tb2, nho2, lon2))
if tb2 < 0.02:
    print("[?] Gần 0 V: bình thường nếu que đo đang để KHÔ. Nhúng que vào nước rồi chạy lại để kiểm tra.")
elif tb2 > 3.2:
    print("[LỖI] Quá cao: kiểm tra dây TDS (+ -> chân 36 3V3, - -> chân 38 GND, A -> chân 32).")
else:
    print("[OK] TDS có tín hiệu (que đang nhúng nước).")

print("\nXong. Bấm Stop trong Thonny. Chạy lại main.py để gửi số liệu.")
