# Thiết bị đo IoT — Raspberry Pi Pico W + MQ135 + TDS

Hướng dẫn lắp mạch, nạp chương trình và cho thiết bị đo gửi số liệu vào web **bằng Visual Studio Code**.
Thiết bị đo chất lượng không khí (MQ135) và nước (TDS), cứ 10 giây gửi một lần qua WiFi tới
`POST /api/tram/so-lieu` của web. Cách chạy web: xem `README.md`.

```
MQ135 + TDS → Pico W ──WiFi──> Laptop (backend FastAPI, cổng 8000) → SQL Server
```

Các tệp trong thư mục `tram_quan_trac/`:

| Tệp | Dùng để |
|---|---|
| `main.py` | **Chương trình chính** — đo và gửi số liệu qua WiFi |
| `kiem_tra_mach.py` | Kiểm tra mạch đã nối đúng chưa (nguồn 5 V, MQ135, TDS) |
| `hieu_chuan.py` | Hiệu chuẩn cảm biến, tính `R0_MQ135` và `HE_SO_TDS` |
| `main_usb_Pico2.py` | Dự phòng cho mạch **không có WiFi**, gửi qua cáp USB (dùng kèm `tools/cau_noi_usb.py`) |
| `diagram.json` | Sơ đồ mạch để mô phỏng trên Wokwi |

---

## 1. Linh kiện

- Raspberry Pi Pico W (RP2040, đã hàn chân) và cáp micro-USB **truyền được dữ liệu** (không dùng cáp chỉ sạc).
- Cảm biến khí **MQ135**, cảm biến nước **TDS Meter** (kèm que đo).
- Breadboard 830 lỗ, dây đực–đực và đực–cái.
- Điện trở **10 kΩ** và **20 kΩ** (hoặc 3 con 10 kΩ) cho mạch chia áp của MQ135.

## 2. Cài đặt trong VS Code (làm một lần)

1. Mở VS Code → **Extensions** (Ctrl + Shift + X) → tìm và cài **MicroPico**.
2. **Nạp MicroPython vào Pico W** (chưa cắm cảm biến):
   - Tải tệp `.uf2` bản mới nhất cho **Pico W** tại https://micropython.org/download/RPI_PICO_W/
   - **Giữ nút BOOTSEL** trên mạch → cắm cáp USB vào laptop → thả nút. Máy hiện ổ đĩa **RPI-RP2**.
     Không hiện ổ nào thì cáp chỉ sạc, đổi cáp khác.
   - Kéo tệp `.uf2` vào ổ **RPI-RP2**. Mạch tự khởi động lại, ổ đĩa biến mất là xong.
3. Mở thư mục dự án trong VS Code. Rút cáp ra cắm lại (lần này **không** giữ BOOTSEL).
   Thanh trạng thái dưới cùng VS Code hiện **Pico Connected** (hoặc *Board Connected*), tab **Terminal** có
   **MicroPico vREPL** với dòng `MicroPython v1.xx ... Raspberry Pi Pico W` và dấu `>>>`.
   Gõ thử `print("xin chao")` rồi Enter.

> Nếu thanh dưới hiện *Pico Disconnected*: rút cáp cắm lại, hoặc nhấn Ctrl + Shift + P → **MicroPico: Connect**.

## 3. Nối dây (rút cáp USB trước khi nối)

Cắm Pico W lên breadboard **vắt ngang rãnh giữa**. Chân 1 ở góc cạnh cổng USB bên trái, đếm xuống tới chân 20,
rồi vòng sang bên phải đi ngược lên từ chân 21 tới chân 40 (chân 40 đối diện chân 1).

**Cảm biến TDS** (cắm que đo vào mạch nhỏ trước), không cần điện trở:

| Chân mạch TDS | Nối tới Pico W |
|---|---|
| `+` (VCC) | **3V3(OUT)** — chân **36** |
| `−` (GND) | **GND** — chân **38** |
| `A` (AO) | **GP27** — chân **32** |

**Cảm biến MQ135** — cần mạch chia áp để điện áp vào Pico không quá 3,3 V:

| Chân MQ135 | Nối tới |
|---|---|
| `VCC` | **VBUS** — chân **40** (5 V từ cổng USB) |
| `GND` | **GND** — chân **38** (hoặc chân GND bất kỳ: 3, 8, 13, 18, 23, 28, 33, 38) |
| `AO` | một đầu điện trở **10 kΩ**; đầu còn lại cắm vào một hàng trống — gọi là **điểm giữa** |
| `DO` | không nối |

| Điểm giữa | Nối tới |
|---|---|
| Điểm giữa | **GP26** — chân **31** |
| Điểm giữa | một đầu điện trở **20 kΩ**; đầu còn lại → **GND** |

```
MQ135 AO ──[ 10 kΩ ]──●── GP26 (chân 31)
                      │
                   [ 20 kΩ ]
                      │
                     GND
```

> Điện trở không phân biệt chiều. 10 kΩ có vạch màu **nâu–đen–cam**, 20 kΩ có vạch **đỏ–đen–cam**.
> Không có 20 kΩ thì nối tiếp 2 con 10 kΩ.
> **Trước khi cắm điện:** không có dây nào nối **VBUS (5 V)** vào chân GP hay 3V3; các dây GND đều về chân GND.

**Sơ đồ nối MQ135 trên breadboard** (Pico W ở trên, số dãy giảm dần xuống dưới; các dây TDS ở chân 36, 38, 32 giữ nguyên):

![Sơ đồ nối dây MQ135 với Pico W trên breadboard](hinh/so_do_noi_MQ135.png)

## 4. Kiểm tra mạch (chưa cần web)

1. Cắm cáp USB, chờ **Pico Connected**.
2. Trong VS Code mở `tram_quan_trac/kiem_tra_mach.py` → bấm **Run** ở thanh dưới cùng
   (hoặc Ctrl + Shift + P → **MicroPico: Run current file on Pico**).
3. Kết quả in ra ở terminal **MicroPico vREPL**: nguồn 5 V, điện áp vào GP26 (phải dưới 3,3 V), MQ135 có phản ứng
   khi thổi hơi cồn/khói nhang, TDS có tín hiệu khi nhúng que vào nước. Mỗi mục có kết luận **[OK]** hoặc **[LỖI]**.
4. Bấm **Stop** ở thanh dưới để dừng.

MQ135 mới cần **ủ 15–30 phút** (cắm điện để yên) thì số mới ổn định; cảm biến hơi ấm là bình thường.

**Hiệu chuẩn (không bắt buộc):** chạy `hieu_chuan.py` theo cách trên, làm theo lời nhắc trên màn hình.
Chương trình in ra hai số `R0_MQ135 = ...` và `HE_SO_TDS = ...`; sửa hai dòng cùng tên trong `main.py`.

## 5. Cho thiết bị gửi số liệu vào web

1. **Chạy backend** (xem `README.md`). Khi khởi động, terminal backend in ra:
   ```
    Pico W / điện thoại cùng WiFi dùng IP của laptop:
      IPv4 Address . . . : 192.168.1.11   <- IP WiFi, dùng IP này
    SERVER_URL trong main.py = "http://192.168.1.11:8000/api/tram/so-lieu"
   ```
2. Mở `tram_quan_trac/main.py`, sửa phần cấu hình ở đầu tệp:
   ```python
   WIFI_SSID = "TenWiFiCuaBan"     # WiFi 2,4 GHz (Pico W không bắt được WiFi 5 GHz)
   WIFI_PASS = "matkhauwifi"
   SERVER_URL = "http://192.168.1.11:8000/api/tram/so-lieu"   # chép đúng dòng backend in ra
   ```
   `MA_TRAM = "TRAM01"`, `KHOA_TRAM = "KhoaTram01"` là thiết bị mẫu có sẵn trong dữ liệu mẫu — giữ nguyên.
   Thiết bị thêm mới thì lấy mã và khóa ở trang **Danh mục → Thiết bị đo** trên web.
3. Bấm **Run** ở thanh dưới. Terminal MicroPico in ra:
   ```
   Da ket noi WiFi. IP cua tram: 192.168.1.19
   [Lan 1] Khong khi:  420 ppm (0.65 V) binh thuong | Nuoc TDS: 236 ppm (0.45 V) binh thuong
      -> Gui toi may chu: HTTP 201 (thanh cong)
   ```
4. Trên web: đăng nhập `canbo` / `Canbo@123` → **Thiết bị đo (IoT)** → TRAM01 hiện **Đang gửi**, số liệu mới hiện theo thời gian.

**Run và Upload khác nhau thế nào:**
- **Run** (*MicroPico: Run current file on Pico*): chạy ngay và in kết quả trong VS Code. Mỗi lần Pico kết nối với
  VS Code thì phải bấm Run lại; rút cáp là dừng.
- **Upload** (chuột phải `main.py` → **Upload current file to Pico**): lưu `main.py` vào Pico. Từ đó cứ cấp điện
  (cắm laptop, sạc điện thoại 5 V, sạc dự phòng) là Pico tự chạy, không cần VS Code.
  Sửa `main.py` (đổi WiFi, đổi IP) thì Upload lại.

> IP laptop có thể đổi khi đổi WiFi hoặc khởi động lại máy: xem lại dòng backend in ra và sửa `SERVER_URL`.
> Mẹo: dùng điện thoại phát WiFi (hotspot, băng tần 2,4 GHz) cho cả laptop và Pico W, đi đâu cũng dùng được.
> Không đưa tên và mật khẩu WiFi của mình lên GitHub.

## 6. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `Khong ket noi duoc WiFi` | Sai tên/mật khẩu; WiFi 5 GHz (Pico W chỉ bắt 2,4 GHz); để mạch gần cục phát |
| `Gui that bai: [Errno 103] ECONNABORTED` / `[Errno 113]` / timeout | Backend chưa chạy; `SERVER_URL` sai IP; laptop và Pico khác WiFi; hoặc tường lửa chặn cổng 8000 (xem dưới) |
| `HTTP 401` | Sai `MA_TRAM` / `KHOA_TRAM`, hoặc thiết bị đang *Ngừng sử dụng* |
| `HTTP 422` | Số đo ngoài dải (thường do nối sai dây MQ135 hoặc thiếu mạch chia áp) |
| Không khí luôn 0 ppm | Dây AO, điện trở chưa đúng, hoặc MQ135 chưa có VBUS 5 V |
| Không khí luôn 5000 ppm | Thiếu điện trở 20 kΩ xuống GND (điện áp vào GP26 quá cao) — rút điện kiểm tra lại ngay |
| TDS luôn 0 | Que đo chưa cắm chặt vào mạch nhỏ, hoặc que đang để khô |
| VS Code hiện *Pico Disconnected* | Rút cáp cắm lại; đóng các chương trình khác đang giữ cổng USB của Pico; Ctrl + Shift + P → **MicroPico: Connect** |
| Bấm Run nhưng thấy `>>>` đứng yên | Mở đúng tệp `main.py` trước khi bấm Run; bấm Stop rồi Run lại |

**Mở cổng 8000 trên tường lửa Windows** (khi Pico báo lỗi kết nối mà IP và WiFi đều đúng):
mở VS Code bằng **Run as administrator** (chuột phải biểu tượng VS Code), mở **Terminal → New Terminal** và gõ:
```powershell
New-NetFirewallRule -DisplayName "CongBaoCao 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
```
Kiểm tra: điện thoại cùng WiFi mở `http://<IPv4 laptop>:8000` thấy trang web là được.

## 7. Mô phỏng trên Wokwi (không bắt buộc)

Tạo dự án **Raspberry Pi Pico W – MicroPython** trên https://wokwi.com, dán nội dung `main.py`
(để `WIFI_SSID = "Wokwi-GUEST"`, `WIFI_PASS = ""`) và `diagram.json`. Trên Wokwi, hai cảm biến được thay bằng hai
biến trở (vặn để giả lập ô nhiễm). Wokwi không gửi được vào web trên laptop; muốn thử đường gửi thì đặt
`SERVER_URL = "http://httpbin.org/post"`.
