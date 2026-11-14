# Cổng báo cáo sự cố môi trường và xử lý hiện trường

Đồ án môn Phân tích và thiết kế hướng đối tượng — Huỳnh Gia Bảo · MSSV 1250080014 · Lớp 12_CNPM1
GVHD: Th.S Phạm Trọng Huynh — Khoa Công nghệ Thông tin, Trường ĐH Tài nguyên và Môi trường TP.HCM

Hệ thống web cho **người dân** gửi phản ánh sự cố môi trường (kèm ảnh/video và vị trí trên bản đồ),
**cán bộ** tiếp nhận – phân công – duyệt kết quả – công khai, và **đơn vị xử lý** nhận nhiệm vụ,
ghi nhận hiện trường, gửi kết quả. Ngoài ra có **thiết bị đo IoT** (Raspberry Pi Pico W + cảm biến không khí
MQ135 + cảm biến nước TDS) tự gửi số liệu về hệ thống. Hệ thống có 14 use case, 16 màn hình, 18 bảng dữ liệu.

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | Python 3.10+, **FastAPI**, trả API JSON dưới `/api` (danh sách API: `/api/docs`) |
| Frontend | **React 18** (Vite, React Router), bản đồ **Leaflet + OpenStreetMap** — thư mục `frontend/` |
| Cơ sở dữ liệu | **Microsoft SQL Server** (18 bảng), SQLAlchemy 2.0 + pyodbc, đăng nhập bằng **tài khoản Windows** |
| Giám sát | **OpenTelemetry** (trace yêu cầu HTTP và câu lệnh SQL), xem trên **Jaeger** |
| Docker | `docker-compose.yml` chạy Jaeger |
| IoT | Raspberry Pi Pico W (MicroPython) gửi số liệu qua WiFi tới `POST /api/tram/so-lieu` |

---

## 1. Cài đặt (làm một lần)

### 1.1. Phần mềm cần có
- **Visual Studio Code**, cài thêm tiện ích **Python** và **MicroPico** (VS Code tự gợi ý khi mở thư mục dự án).
- **Python 3.10 trở lên** (khi cài, tick *Add python.exe to PATH*).
- **Node.js** bản LTS (để chạy giao diện React bằng `npm run dev`).
- **SQL Server** và **SQL Server Management Studio (SSMS)**, **ODBC Driver 17 (hoặc 18) for SQL Server**.
- **Docker Desktop** (chỉ để chạy Jaeger; không có Docker thì hệ thống vẫn chạy, chỉ không xem được trace).

### 1.2. Mở dự án và cài thư viện
Mở thư mục dự án trong VS Code → **Terminal → New Terminal** (PowerShell), gõ lần lượt:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 1.3. Cấu hình tệp `.env`
Tệp `.env` có sẵn trong dự án (bản mẫu, chưa có thông tin riêng). Mở `.env` trong VS Code:
- **`DATABASE_URL`**: SSMS kết nối bằng server `.` thì giữ nguyên dòng (A). Dùng `.\SQLEXPRESS` thì dùng dòng (B).
  Máy cài ODBC Driver 18 thì đổi số `17` thành `18`.
- **Gửi mã báo cáo qua Gmail** (không bắt buộc): bật *Xác minh 2 bước* cho tài khoản Google, tạo *Mật khẩu ứng dụng*
  tại https://myaccount.google.com/apppasswords, rồi điền `SMTP_USER` và `SMTP_PASSWORD`. Để trống thì không gửi thư.

> Sau khi điền Gmail và mật khẩu ứng dụng vào `.env` trên máy mình, đừng commit lại tệp này lên GitHub.

### 1.4. Tạo cơ sở dữ liệu (chọn 1 trong 2 cách, đều dùng tài khoản Windows)
- **Cách 1 – SSMS:** kết nối server `.` (Windows Authentication) → **New Query** → mở `sql/01_tao_csdl.sql` → **Execute**.
  Sau đó tạo dữ liệu mẫu bằng lệnh ở cách 2.
- **Cách 2 – lệnh trong VS Code:** tự tạo database, 18 bảng và dữ liệu mẫu nếu chưa có:
  ```powershell
  .venv\Scripts\python.exe -m app.seed
  ```

---

## 2. Chạy hệ thống (mỗi lần dùng)

Trước tiên mở **Docker Desktop**, chờ hiện *Engine running*.

**Terminal 1 – Jaeger và backend:**
```powershell
docker compose up -d
$env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Khi khởi động, backend in ra địa chỉ web và **IPv4 của laptop** (dùng cho Pico W và điện thoại cùng WiFi).

**Terminal 2 – frontend React** (bấm dấu **+** trên khung Terminal để mở thêm):
```powershell
cd frontend
npm run dev
```

| Địa chỉ | Dùng để |
|---|---|
| http://localhost:5173 | Giao diện React (chạy bằng `npm run dev`) |
| http://localhost:8000 | Giao diện React bản đã build, do backend phục vụ |
| http://localhost:8000/api/docs | Danh sách và thử các API |
| http://localhost:16686 | Jaeger: chọn service `cong-bao-cao-moi-truong` → *Find Traces* |
| `http://<IPv4 laptop>:8000` | Mở trên điện thoại cùng WiFi |

**Tắt:** bấm vào từng terminal, nhấn **Ctrl + C**, rồi gõ `docker compose down`.

> Không mở `http://0.0.0.0:8000` trên trình duyệt; dùng `localhost` hoặc IPv4 của laptop.

### Tài khoản mẫu

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Cán bộ | `canbo` | `Canbo@123` |
| Đơn vị xử lý | `donvi.binhdong`, `donvi.chanhhung`, `donvi.rachong`, `donvi.phudinh` | `Donvi@123` |
| Người dân | không cần tài khoản | dùng mã báo cáo |
| Thiết bị đo | `TRAM01`, `TRAM02`, `TRAM03` | khóa `KhoaTram01`, `KhoaTram02`, `KhoaTram03` |

Đây là dữ liệu mẫu để chạy thử; lệnh `python -m app.seed` in ra danh sách báo cáo mẫu và lưu vào `TAI_KHOAN_VA_DU_LIEU_MAU.txt`.

---

## 3. Thiết bị đo Pico W

Cách lắp mạch, nạp chương trình và cho thiết bị gửi số liệu vào web: xem **`README_IOT.md`**.

Chưa có mạch thì giả lập thiết bị đo gửi số liệu (trong lúc backend đang chạy), mở thêm một terminal và gõ:
```powershell
.venv\Scripts\python.exe tools\gia_lap_tram.py
```
Bấm **Ctrl + C** để dừng. Số liệu hiện ở trang **Thiết bị đo (IoT)** (đăng nhập `canbo`).

---

## 4. Kiểm thử

```powershell
.venv\Scripts\python.exe tests\test_he_thong.py
```
Chạy 40 trường hợp kiểm thử qua API trên một CSDL SQLite tạm (không đụng dữ liệu thật, không gửi thư thật).
Kết quả đúng: `TẤT CẢ KIỂM THỬ ĐỀU ĐẠT`.

Các lệnh khác:
- `.venv\Scripts\python.exe -m app.seed --reset` — **xóa sạch** dữ liệu và tạo lại dữ liệu mẫu.
- Trong VS Code có sẵn các tác vụ: **Terminal → Run Task** (tạo dữ liệu, giả lập thiết bị đo, kiểm thử, bật/tắt Jaeger…).

---

## 5. Cấu trúc mã nguồn

```
app/                       BACKEND (FastAPI)
  main.py                  khởi động, gắn router, trả lỗi dạng JSON, phục vụ giao diện React đã build, in IPv4
  telemetry.py             OpenTelemetry: trace HTTP + SQL, sự kiện nghiệp vụ
  web.py                   phân quyền theo vai trò, chuyển dữ liệu sang JSON
  routers/                 6 router API: public · auth · canbo · quan_ly · donvi · api (thiết bị đo)
  services/                15 Service nghiệp vụ (tên giống biểu đồ tuần tự trong báo cáo)
  models.py                18 lớp = 18 bảng SQL Server
  seed.py                  tạo database + dữ liệu mẫu
frontend/                  FRONTEND (React): src/trang (màn hình), src/thanh_phan (khung, bản đồ, bảng), dist (bản build)
sql/01_tao_csdl.sql        script tạo database + 18 bảng bằng SSMS
docker-compose.yml         Jaeger (OpenTelemetry)
.vscode/                   cấu hình VS Code (tác vụ, gỡ lỗi, tiện ích gợi ý)
tests/test_he_thong.py     kiểm thử tự động 40 trường hợp qua API
tools/                     gia_lap_tram.py (giả lập thiết bị đo), cau_noi_usb.py (mạch không WiFi)
tram_quan_trac/            chương trình MicroPython cho Pico W (xem README_IOT.md)
```

| Use case | Màn hình (React) | API chính |
|---|---|---|
| UC01 Gửi báo cáo | `/gui-bao-cao` | `POST /api/bao-cao` |
| UC02 Tra cứu | `/tra-cuu`, `/quen-ma`, `/can-bo/tra-cuu` | `GET /api/tra-cuu`, `POST /api/quen-ma`, `GET /api/can-bo/tra-cuu` |
| UC03 Bổ sung thông tin | `/bo-sung` | `POST /api/bo-sung/xac-minh`, `/api/bo-sung/gui` |
| UC04 Đăng nhập | `/dang-nhap`, `/doi-mat-khau` | `POST /api/dang-nhap`, `/api/doi-mat-khau` |
| UC05 Tiếp nhận | `/can-bo/tiep-nhan` | `/api/can-bo/tiep-nhan/...` |
| UC06 Phân công | `/can-bo/phan-cong` | `/api/can-bo/phan-cong/...` |
| UC07 Duyệt kết quả | `/can-bo/nghiem-thu` | `/api/can-bo/nghiem-thu/...`, `GET /api/trang-thai-moi` |
| UC08 Kiểm duyệt, công khai | `/can-bo/kiem-duyet` | `/api/can-bo/kiem-duyet/...` |
| UC09 Danh mục | `/can-bo/danh-muc` | `/api/can-bo/danh-muc/...` |
| UC10 Tài khoản đơn vị | `/can-bo/tai-khoan` | `/api/can-bo/tai-khoan/...` |
| UC11 Hiện trường | `/don-vi/nhiem-vu` | `/api/don-vi/nhiem-vu/...` |
| UC12 Tiến độ, kết quả | `/don-vi/cap-nhat` | `/api/don-vi/cap-nhat/...` |
| UC13 Gửi số liệu | (thiết bị) | `POST /api/tram/so-lieu` |
| UC14 Theo dõi số liệu | `/can-bo/tram-quan-trac` | `GET /api/can-bo/tram-quan-trac` |

---

## 6. Lỗi thường gặp

| Thông báo | Cách xử lý |
|---|---|
| *KHÔNG KẾT NỐI ĐƯỢC CƠ SỞ DỮ LIỆU* | SQL Server chưa chạy hoặc sai tên server trong `DATABASE_URL` (`.env`) |
| `Data source name not found` | Máy có ODBC Driver 18: đổi `17` thành `18` trong `DATABASE_URL` |
| `failed to connect to the docker API ... dockerDesktopLinuxEngine` | Docker Desktop chưa mở: mở Docker Desktop, chờ *Engine running* rồi chạy lại `docker compose up -d` |
| `npm` không nhận | Chưa cài Node.js, hoặc cài xong chưa mở lại VS Code |
| Cổng 8000 đã bị dùng | Còn một terminal khác đang chạy backend: tắt bằng Ctrl + C |
| Bản đồ không hiện | Máy không có Internet (nền OpenStreetMap tải từ mạng) |
| Thiết bị báo `HTTP 401` | Sai `MA_TRAM` / `KHOA_TRAM` trong `main.py`, hoặc thiết bị đang *Ngừng sử dụng* |
| Pico W báo `ECONNABORTED` / lỗi kết nối | Xem mục *Lỗi thường gặp* trong `README_IOT.md` |
