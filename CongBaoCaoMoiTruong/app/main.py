import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .db import engine
from .routers import api, auth, canbo, donvi, public, quan_ly
from .services.common import NghiepVuError
from .telemetry import bat_giam_sat


def _ip_laptop():
    chinh = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        chinh = s.getsockname()[0]
    except OSError:
        pass
    finally:
        s.close()
    try:
        tat_ca = sorted({x[4][0] for x in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    except OSError:
        tat_ca = []
    return chinh, [ip for ip in tat_ca if ip != chinh and not ip.startswith("127.")]


def _in_dia_chi():
    cong = os.environ.get("PORT", "8000")
    chinh, khac = _ip_laptop()
    print("=" * 60)
    print(f" Web:     http://localhost:{cong}")
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        print(" Jaeger:  http://localhost:16686   (xem trace OpenTelemetry)")
    print(" Pico W / điện thoại cùng WiFi dùng IP của laptop:")
    if chinh:
        print(f"   IPv4 Address . . . : {chinh}   <- IP WiFi, dùng IP này")
    for ip in khac:
        print(f"   IPv4 Address . . . : {ip}")
    print(f' SERVER_URL trong main.py = "http://{chinh or "IP_LAPTOP"}:{cong}/api/tram/so-lieu"')
    print(" Ctrl+C để tắt web.")
    print("=" * 60, flush=True)


@asynccontextmanager
async def _khoi_dong(app):
    from .services.luu_tru_tep_service import don_vung_tam
    don_vung_tam()
    _in_dia_chi()
    yield


app = FastAPI(lifespan=_khoi_dong, title="Cổng báo cáo sự cố môi trường và xử lý hiện trường",
              docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie="cbcmt_session",
                   max_age=8 * 3600, same_site="lax")

for r in (public.router, auth.router, canbo.router, quan_ly.router, donvi.router, api.router):
    app.include_router(r)

bat_giam_sat(app, engine)


@app.exception_handler(NghiepVuError)
async def _loi_nghiep_vu(request: Request, exc: NghiepVuError):
    return JSONResponse({"loi": str(exc)}, status_code=400)


@app.exception_handler(StarletteHTTPException)
async def _loi_http(request: Request, exc: StarletteHTTPException):
    if not request.url.path.startswith(("/api/", "/tep/")) and exc.status_code == 404 and request.method == "GET":
        return _trang_react()
    loi = exc.detail if isinstance(exc.detail, str) else "Có lỗi xảy ra."
    if exc.status_code == 404 and loi == "Not Found":
        loi = "Không tìm thấy."
    return JSONResponse({"loi": loi}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def _loi_du_lieu(request: Request, exc: RequestValidationError):
    return JSONResponse({"loi": "Dữ liệu gửi lên không hợp lệ."}, status_code=422)


DIST = config.BASE_DIR / "frontend" / "dist"
if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")


def _trang_react():
    index = DIST / "index.html"
    if not index.exists():
        return JSONResponse({"loi": "Chưa có bản build của giao diện. Chạy: cd frontend && npm install && npm run build"},
                            status_code=503)
    return FileResponse(str(index), headers={"Cache-Control": "no-cache"})


@app.get("/", include_in_schema=False)
def trang_goc():
    return _trang_react()


@app.get("/favicon.svg", include_in_schema=False)
def bieu_tuong():
    p = DIST / "favicon.svg"
    return FileResponse(str(p)) if p.exists() else JSONResponse({}, status_code=404)
