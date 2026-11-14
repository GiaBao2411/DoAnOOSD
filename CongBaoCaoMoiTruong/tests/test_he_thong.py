"""Kiểm thử toàn bộ luồng nghiệp vụ qua API JSON mà giao diện React gọi (chạy bằng SQLite tạm).

    python -m pytest tests -q        (hoặc: python tests/test_he_thong.py)

Mỗi khối có ghi mã trường hợp kiểm thử (TC01–TC40) tương ứng bảng test case trong báo cáo.
"""
import os
import shutil
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp())
os.environ["DATABASE_URL"] = "sqlite:///" + str(TMP / "test.db")
os.environ["UPLOAD_DIR"] = str(TMP / "uploads")
os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app import models as M  # noqa: E402
from app import trang_thai as TT  # noqa: E402
from app import seed  # noqa: E402
from app.db import SessionLocal, now  # noqa: E402
from app.main import app  # noqa: E402
from app import config  # noqa: E402
from app.services import email_service  # noqa: E402

# Không gửi thư thật khi kiểm thử: thay máy chủ SMTP bằng hàm ghi lại thư
THU_DA_GUI = []
config.SMTP_USER, config.SMTP_PASSWORD = "kiemthu@gmail.com", "matkhauungdung"
email_service._gui_smtp = lambda den, tieu_de, van_ban, trang_html: THU_DA_GUI.append((den, tieu_de, van_ban))

ASSETS = ROOT / "app" / "seed_assets"


def anh(ten="rac_truoc.jpg"):
    return ("tep", (ten, (ASSETS / ten).read_bytes(), "image/jpeg"))


def dang_nhap(ten, mk):
    c = TestClient(app)
    r = c.post("/api/dang-nhap", data={"ten": ten, "mat_khau": mk})
    assert r.status_code == 200, r.text[:300]
    return c


def ok(r, chua=None):
    assert r.status_code in (200, 201), (r.status_code, r.text[:500])
    if chua:
        assert chua in r.text, "Không thấy “%s” trong %s" % (chua, r.text[:300])
    return r.json()


def loi(r, chua, ma=400):
    assert r.status_code == ma, (r.status_code, r.text[:300])
    assert chua in r.json()["loi"], (chua, r.json())


def bc_by(ma):
    db = SessionLocal()
    b = db.scalar(select(M.BaoCaoSuCo).where(M.BaoCaoSuCo.MaTraCuu == ma))
    db.close()
    return b


def test_toan_bo():
    sys.argv = ["seed", "--reset"]
    seed.main()
    dan = TestClient(app)

    # ---- giao diện React được phục vụ ở mọi đường dẫn không phải /api (nếu đã build)
    r = dan.get("/can-bo/tiep-nhan")
    assert r.status_code in (200, 503)
    ok(dan.get("/api/cau-hinh"), "ds_dia_ban")
    ok(dan.get("/api/trang-chu"), "BC2026-000001")

    # ---- TC01–TC07 UC01 gửi báo cáo
    db = SessionLocal()
    ma_db = db.scalar(select(M.DiaBan.MaDiaBan))
    db.close()
    du_lieu = {"mo_ta": "Rác đổ trộm ven đường", "thoi_gian_phat_hien": (now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
               "ma_dia_ban": str(ma_db), "dia_chi": "", "vi_do": "10.74", "kinh_do": "106.65"}
    loi(dan.post("/api/bao-cao", data=du_lieu), "ít nhất một ảnh")                                              # TC01
    loi(dan.post("/api/bao-cao", data=du_lieu, files=[("tep", ("x.txt", b"hello", "text/plain"))]), "không đúng định dạng")  # TC02
    loi(dan.post("/api/bao-cao", data=du_lieu, files=[("tep", ("gia.jpg", b"not an image at all", "image/jpeg"))]), "không phải ảnh")  # TC03
    loi(dan.post("/api/bao-cao", data=dict(du_lieu, vi_do="", kinh_do=""), files=[anh()]), "vị trí trên bản đồ hoặc nhập địa chỉ")  # TC04
    tuong_lai = dict(du_lieu, thoi_gian_phat_hien=(now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"))
    loi(dan.post("/api/bao-cao", data=tuong_lai, files=[anh()]), "không được sau")                                # TC05
    loi(dan.post("/api/bao-cao", data=dict(du_lieu, email="khong-phai-email"), files=[anh()]), "Địa chỉ email không hợp lệ")  # TC06
    kq = ok(dan.post("/api/bao-cao", data=dict(du_lieu, email="Nguoi.Dan@Gmail.com"), files=[anh(), anh("rac_truoc_2.jpg")]))  # TC07
    ma = kq["ma_tra_cuu"]
    assert kq["email"] == "nguoi.dan@gmail.com" and kq["mail_bat"]
    assert THU_DA_GUI[-1][0] == "nguoi.dan@gmail.com" and ma in THU_DA_GUI[-1][1] and ma in THU_DA_GUI[-1][2]
    b = bc_by(ma)
    assert b.TrangThai == TT.BC_MOI_GUI

    # ---- TC08–TC10 UC02 tra cứu, lấy lại mã
    ok(dan.get("/api/tra-cuu?ma=BC2026-000001"), "cong_khai")                                                  # TC08
    loi(dan.get("/api/tra-cuu?ma=KHONGCO"), "Không tìm thấy", 404)
    assert ok(dan.get("/api/tra-cuu?ma=" + ma))["trang_thai"] == TT.BC_MOI_GUI
    so_thu = len(THU_DA_GUI)
    assert ok(dan.post("/api/quen-ma", data={"email": "nguoi.dan@gmail.com"}))["da_gui"]                        # TC09
    assert len(THU_DA_GUI) == so_thu + 1 and ma in THU_DA_GUI[-1][2]
    assert ok(dan.post("/api/quen-ma", data={"email": "khong.co@gmail.com"}))["da_gui"]                         # TC10
    assert len(THU_DA_GUI) == so_thu + 1
    loi(dan.post("/api/quen-ma", data={"email": "sai"}), "không hợp lệ")

    # ---- TC11–TC12 UC04 đăng nhập, quyền xem tệp
    db = SessionLocal()
    mc = db.scalar(select(M.MinhChungBaoCao).where(M.MinhChungBaoCao.MaBaoCao == b.MaBaoCao))
    db.close()
    assert dan.get("/tep/bc/%d" % mc.MaMinhChung).status_code == 404                                          # TC12
    assert dan.get("/api/can-bo/tiep-nhan").status_code == 401
    loi(dan.post("/api/dang-nhap", data={"ten": "canbo", "mat_khau": "sai"}), "Sai tên đăng nhập")               # TC11
    cb = dang_nhap("canbo", "Canbo@123")
    ok(cb.get("/api/trang-chinh"), "can_bo")
    assert cb.get("/tep/bc/%d" % mc.MaMinhChung).status_code == 200
    db = SessionLocal()
    assert db.scalar(select(func.count()).select_from(M.TaiKhoan).where(M.TaiKhoan.LoaiTaiKhoan == TT.TK_CAN_BO)) == 1
    db.close()

    # ---- TC13 UC05 tiếp nhận -> yêu cầu bổ sung
    ok(cb.get("/api/can-bo/tiep-nhan?tab=moi"), ma)
    ok(cb.post("/api/can-bo/tiep-nhan/%d/nhan" % b.MaBaoCao))
    assert bc_by(ma).TrangThai == TT.BC_DANG_XEM_XET
    loi(cb.post("/api/can-bo/tiep-nhan/%d/bo-sung" % b.MaBaoCao, data={"noi_dung": ""}), "Vui lòng nhập nội dung yêu cầu bổ sung")
    ok(cb.post("/api/can-bo/tiep-nhan/%d/bo-sung" % b.MaBaoCao, data={"noi_dung": "Gửi thêm ảnh rộng"}))
    assert bc_by(ma).TrangThai == TT.BC_CHO_BO_SUNG

    # ---- TC14–TC15 UC03 bổ sung bằng mã báo cáo
    loi(dan.post("/api/bo-sung/xac-minh", data={"ma": "BC2000-999999"}), "Không tìm thấy báo cáo")               # TC14
    ok(dan.post("/api/bo-sung/xac-minh", data={"ma": ma}))
    ok(dan.get("/api/bo-sung"), "Gửi thêm ảnh rộng")
    ok(dan.post("/api/bo-sung/gui", data={"noi_dung": "Đây là ảnh rộng"}, files=[anh("rac_truoc_2.jpg")]), "Đã gửi bổ sung")  # TC15
    assert bc_by(ma).TrangThai == TT.BC_DANG_XEM_XET
    ok(cb.get("/api/can-bo/tiep-nhan?tab=da-bo-sung"), ma)

    # ---- TC16 UC05 hợp lệ
    db = SessionLocal()
    ma_loai = db.scalar(select(M.LoaiSuCo.MaLoai))
    dv = db.scalar(select(M.DonViXuLy).where(M.DonViXuLy.TenDonVi.like("%Bình Đông%")))
    dv2 = db.scalar(select(M.DonViXuLy).where(M.DonViXuLy.TenDonVi.like("%Phú Định%")))
    db.close()
    loi(cb.post("/api/can-bo/tiep-nhan/%d/hop-le" % b.MaBaoCao, data={"ma_loai": "", "uu_tien": "Cao"}), "Vui lòng chọn loại sự cố")
    ok(cb.post("/api/can-bo/tiep-nhan/%d/hop-le" % b.MaBaoCao, data={"ma_loai": str(ma_loai), "uu_tien": "Cao"}))
    assert bc_by(ma).TrangThai == TT.BC_CHO_PHAN_CONG

    # ---- TC18–TC20 UC06 giao Phú Định -> trả lại -> giao lại Bình Đông
    d = ok(cb.get("/api/can-bo/phan-cong?ma=%d" % b.MaBaoCao))
    assert any(x["goi_y"] for x in d["chon"]["don_vi"]) and "thoi_han" not in str(d)                             # TC18
    loi(cb.post("/api/can-bo/phan-cong/%d/giao" % b.MaBaoCao, data={"ma_don_vi": str(dv2.MaDonVi), "noi_dung": ""}),
        "Vui lòng nhập nội dung nhiệm vụ")
    ok(cb.post("/api/can-bo/phan-cong/%d/giao" % b.MaBaoCao, data={"ma_don_vi": str(dv2.MaDonVi), "noi_dung": "Thu gom"}))
    assert bc_by(ma).TrangThai == TT.BC_DA_PHAN_CONG
    pd = dang_nhap("donvi.phudinh", "Donvi@123")
    db = SessionLocal()
    pc1 = db.scalar(select(M.PhanCongXuLy).where(M.PhanCongXuLy.MaBaoCao == b.MaBaoCao))
    db.close()
    ok(pd.get("/api/don-vi/nhiem-vu/%d" % pc1.MaPhanCong), TT.PC_CHO_TIEP_NHAN)
    loi(pd.post("/api/don-vi/nhiem-vu/%d/tra-lai" % pc1.MaPhanCong, data={"ly_do": ""}), "Vui lòng nhập lý do trả lại")  # TC19
    ok(pd.post("/api/don-vi/nhiem-vu/%d/tra-lai" % pc1.MaPhanCong, data={"ly_do": "Không thuộc địa bàn"}))
    assert bc_by(ma).TrangThai == TT.BC_CHO_PHAN_CONG
    ok(cb.post("/api/can-bo/phan-cong/%d/giao" % b.MaBaoCao, data={"ma_don_vi": str(dv.MaDonVi), "noi_dung": "Thu gom rác"}))
    db = SessionLocal()
    pc = db.scalar(select(M.PhanCongXuLy).where(M.PhanCongXuLy.MaBaoCao == b.MaBaoCao,
                                                M.PhanCongXuLy.TrangThai == TT.PC_CHO_TIEP_NHAN))
    db.close()
    loi(pd.get("/api/don-vi/nhiem-vu/%d" % pc.MaPhanCong), "không thuộc đơn vị")                              # TC20

    # ---- TC21 UC11 nhận, ghi nhận hiện trường
    bd = dang_nhap("donvi.binhdong", "Donvi@123")
    ok(bd.post("/api/don-vi/nhiem-vu/%d/nhan" % pc.MaPhanCong))
    assert bc_by(ma).TrangThai == TT.BC_DANG_XU_LY
    ok(bd.post("/api/don-vi/nhiem-vu/%d/ghi-nhan" % pc.MaPhanCong,
               data={"hanh_dong": "ghi-nhan", "nhan_xet": "Có rác", "vi_do": "10.7401", "kinh_do": "106.6502"},
               files=[anh("hien_truong.jpg")]), "Đã lưu ghi nhận")
    ct = ok(bd.get("/api/don-vi/nhiem-vu/%d" % pc.MaPhanCong))
    assert ct["cap_nhat"][-1]["khoang_cach"] is not None

    # ---- TC22–TC24 UC12 tiến độ, kết quả; trang cán bộ tự cập nhật
    loi(bd.post("/api/don-vi/cap-nhat/%d/tien-do" % pc.MaPhanCong, data={"phan_tram": "150", "noi_dung": "x"}), "0 đến 100")
    ok(bd.post("/api/don-vi/cap-nhat/%d/tien-do" % pc.MaPhanCong, data={"phan_tram": "50", "noi_dung": "Được nửa"}), "Đã lưu tiến độ")
    assert bd.post("/api/don-vi/cap-nhat/%d/gia-han" % pc.MaPhanCong, data={}).status_code in (404, 405)   # đã bỏ gia hạn
    truoc = cb.get("/api/trang-thai-moi").json()
    assert bd.get("/api/trang-thai-moi").json()["dem"] == {"cho_nhan": 0}
    loi(bd.post("/api/don-vi/cap-nhat/%d/ket-qua" % pc.MaPhanCong, data={"ket_qua": "Xong"}), "ít nhất một ảnh sau")
    ok(bd.post("/api/don-vi/cap-nhat/%d/ket-qua" % pc.MaPhanCong, data={"ket_qua": "Đã thu gom"}, files=[anh("rac_sau.jpg")]),
       "Chờ duyệt kết quả")
    assert bc_by(ma).TrangThai == TT.BC_CHO_NGHIEM_THU
    sau = cb.get("/api/trang-thai-moi").json()                                                              # TC24
    assert sau["dau"] != truoc["dau"] and sau["dem"]["nghiem_thu"] == truoc["dem"]["nghiem_thu"] + 1, (truoc, sau)
    assert TestClient(app).get("/api/trang-thai-moi").status_code == 401

    # ---- TC25–TC26 UC07 chưa đạt -> làm lại -> đạt
    ok(cb.get("/api/can-bo/nghiem-thu?pc=%d" % pc.MaPhanCong), "Đã thu gom")
    loi(cb.post("/api/can-bo/nghiem-thu/%d" % pc.MaPhanCong, data={"ket_qua": TT.NT_CHUA_DAT, "nhan_xet": ""}), "Vui lòng nhập yêu cầu")
    ok(cb.post("/api/can-bo/nghiem-thu/%d" % pc.MaPhanCong, data={"ket_qua": TT.NT_CHUA_DAT, "nhan_xet": "Còn rác"}))
    assert bc_by(ma).TrangThai == TT.BC_DANG_XU_LY
    ok(bd.post("/api/don-vi/cap-nhat/%d/ket-qua" % pc.MaPhanCong, data={"ket_qua": "Đã dọn hết"}, files=[anh("rac_sau.jpg")]))
    loi(cb.post("/api/can-bo/nghiem-thu/%d" % pc.MaPhanCong, data={"ket_qua": TT.NT_KHONG_CO_SU_CO}), "không báo")
    d = ok(cb.post("/api/can-bo/nghiem-thu/%d" % pc.MaPhanCong, data={"ket_qua": TT.NT_DAT, "nhan_xet": "Đạt"}), "Chờ công khai")
    assert d["chuyen_den"] == "/can-bo/kiem-duyet?ma=%d" % b.MaBaoCao                                      # duyệt đạt -> sang bước công khai
    assert bc_by(ma).TrangThai == TT.BC_CHO_CONG_KHAI

    # ---- TC27–TC29 UC08 kiểm duyệt
    d = ok(cb.get("/api/can-bo/kiem-duyet?ma=%d" % b.MaBaoCao))
    assert "nguoi.dan@gmail.com" not in d["chon"]["noi_dung"] and "nguoi.dan@gmail.com" not in d["chon"]["tieu_de"]
    form = {"tieu_de": "Đã thu gom rác", "noi_dung": "Đã xử lý", "ly_do": ""}
    loi(cb.post("/api/can-bo/kiem-duyet/%d" % b.MaBaoCao, data=dict(form, hanh_dong="duyet")), "Phải xác nhận")   # TC27
    ok(cb.post("/api/can-bo/kiem-duyet/%d" % b.MaBaoCao, data=dict(form, hanh_dong="khong-duyet", ly_do="Ảnh lộ biển số")),
       "không duyệt")                                                                                       # TC28
    db = SessionLocal()
    xl = [m.MaMinhChung for m in db.scalars(select(M.MinhChungXuLy))][-1]
    db.close()
    ok(cb.post("/api/can-bo/kiem-duyet/%d" % b.MaBaoCao,
               data=dict(form, hanh_dong="duyet", da_kiem_tra="1", anh="xl-%d" % xl)), "Đã duyệt và công khai")  # TC29
    assert bc_by(ma).TrangThai == TT.BC_HOAN_TAT
    r = dan.get("/api/tra-cuu?ma=" + ma)
    assert r.json()["cong_khai"]["tieu_de"] == "Đã thu gom rác" and "nguoi.dan@gmail.com" not in r.text
    la = TestClient(app)
    assert la.get("/tep/xl/%d" % xl).status_code == 200
    assert la.get("/tep/bc/%d" % mc.MaMinhChung).status_code == 404
    assert dan.get("/tep/bc/%d" % mc.MaMinhChung).status_code == 200

    # ---- UC02 nội bộ
    ok(cb.get("/api/can-bo/tra-cuu?q=BC&trang_thai=Hoàn tất"), "Hoàn tất")
    ok(cb.get("/api/can-bo/bao-cao/%d" % b.MaBaoCao), "lich_su")

    # ---- TC17 đóng hồ sơ quá hạn bổ sung (báo cáo mẫu số 9)
    b9 = bc_by("BC2026-000009")
    ok(cb.get("/api/can-bo/tiep-nhan?tab=qua-han"), "BC2026-000009")
    ok(cb.post("/api/can-bo/tiep-nhan/%d/dong" % b9.MaBaoCao))
    assert bc_by("BC2026-000009").TrangThai == TT.BC_DA_DONG

    # ---- TC30–TC35 UC09, UC10 (cán bộ quản lý)
    assert bd.get("/api/can-bo/danh-muc").status_code == 403                                               # TC30
    assert bd.get("/api/can-bo/tai-khoan").status_code == 403
    assert bd.get("/api/can-bo/danh-muc?tab=tram").status_code == 403
    for tab in ("loai", "dia-ban", "don-vi", "tram", "tham-so"):
        ok(cb.get("/api/can-bo/danh-muc?tab=" + tab))
    loi(cb.post("/api/can-bo/danh-muc/loai", data={"ma": "", "ten": "Rác thải", "dang_dung": "1"}), "đã tồn tại")    # TC31
    ok(cb.post("/api/can-bo/danh-muc/loai", data={"ma": "", "ten": "Mùi hôi", "dang_dung": "1"}), "Đã lưu loại")
    loi(cb.post("/api/can-bo/danh-muc/tham-so", data={"ma": "HAN_BO_SUNG_NGAY", "gia_tri": "0"}), "số nguyên dương")  # TC32
    ok(cb.post("/api/can-bo/danh-muc/tham-so", data={"ma": "HAN_BO_SUNG_NGAY", "gia_tri": "5"}), "Đã cập nhật tham số")
    loi(cb.post("/api/can-bo/tai-khoan/them", data={"ten": "donvi.moi", "ma_don_vi": ""}), "Vui lòng chọn đơn vị")  # TC33
    mk = ok(cb.post("/api/can-bo/tai-khoan/them", data={"ten": "donvi.moi", "ma_don_vi": str(dv.MaDonVi)}))["mat_khau_tam"][1]
    loi(cb.post("/api/can-bo/tai-khoan/them", data={"ten": "donvi.moi", "ma_don_vi": str(dv.MaDonVi)}), "đã tồn tại")
    moi = dang_nhap("donvi.moi", mk)                                                                       # TC34
    assert moi.get("/api/toi").json()["tai_khoan"]["phai_doi_mat_khau"] is True
    loi(moi.get("/api/don-vi/nhiem-vu"), "đổi mật khẩu", 403)
    ok(moi.post("/api/doi-mat-khau", data={"cu": mk, "moi": "Matkhau123", "nhap_lai": "Matkhau123"}))
    ok(moi.get("/api/don-vi/nhiem-vu"))
    db = SessionLocal()
    moi_tk = db.scalar(select(M.TaiKhoan).where(M.TaiKhoan.TenDangNhap == "donvi.moi"))
    tk_cb = db.scalar(select(M.TaiKhoan).where(M.TaiKhoan.TenDangNhap == "canbo"))
    db.close()
    assert moi_tk.LoaiTaiKhoan == TT.TK_DON_VI
    ok(cb.post("/api/can-bo/tai-khoan/%d/khoa" % moi_tk.MaTaiKhoan), "bị khóa")                              # TC35
    assert moi.get("/api/don-vi/nhiem-vu").status_code == 401                                              # bị khóa thì mất phiên
    loi(cb.post("/api/can-bo/tai-khoan/%d/khoa" % tk_cb.MaTaiKhoan), "Không tìm thấy tài khoản đơn vị")

    # ---- mọi màn hình đều có dữ liệu
    for u in ["/api/can-bo/tiep-nhan?tab=moi", "/api/can-bo/tiep-nhan?tab=qua-han", "/api/can-bo/phan-cong",
              "/api/can-bo/tra-cuu?trang_thai=o-don-vi", "/api/can-bo/nghiem-thu", "/api/can-bo/kiem-duyet", "/api/can-bo/tra-cuu"]:
        ok(cb.get(u))
    for u in ["/api/trang-chinh", "/api/don-vi/nhiem-vu", "/api/don-vi/nhiem-vu?tat_ca=1", "/api/don-vi/cap-nhat"]:
        ok(bd.get(u))
    ok(cb.get("/api/can-bo/tai-khoan"), "donvi.binhdong")

    # ---- TC36–TC40 UC13, UC14, UC09 (thiết bị đo IoT — module M8)
    api = TestClient(app)
    goi = {"ma_thiet_bi": "TRAM01", "khoa": "KhoaTram01", "khong_khi_ppm": 450.5, "tds_ppm": 210}
    r = api.post("/api/tram/so-lieu", json=goi)
    assert r.status_code == 201 and r.json()["vuot_nguong"] is False, r.text                               # TC36
    r = api.post("/api/tram/so-lieu", json=dict(goi, khong_khi_ppm=1500))
    assert r.status_code == 201 and r.json()["vuot_nguong"] is True
    assert api.post("/api/tram/so-lieu", json=dict(goi, khoa="sai")).status_code == 401                    # TC37
    assert api.post("/api/tram/so-lieu", json=dict(goi, ma_thiet_bi="KHONGCO")).status_code == 401
    assert api.post("/api/tram/so-lieu", json=dict(goi, tds_ppm=-5)).status_code == 422                    # TC38
    assert api.post("/api/tram/so-lieu", json=dict(goi, khong_khi_ppm="abc")).status_code == 422
    assert api.post("/api/tram/so-lieu", content=b"khong-phai-json").status_code == 400
    d = ok(cb.get("/api/can-bo/tram-quan-trac"))                                                           # TC39
    trang_thai = {x["tram"]["ma_thiet_bi"]: x["mat_ket_noi"] for x in d["tq"]}
    assert trang_thai["TRAM01"] is False and trang_thai["TRAM03"] is True
    d = ok(cb.get("/api/can-bo/tram-quan-trac?tram=1&vuot=1"))
    assert d["rows"] and all(x["vuot"] for x in d["rows"])
    assert "Từ thời điểm phải trước" in cb.get("/api/can-bo/tram-quan-trac?tram=1&tu=2026-12-01T00:00&den=2026-11-01T00:00").json()["loi"]
    assert ok(cb.get("/api/trang-chinh"))["so"]["tram_mat"] >= 1
    kq = ok(cb.post("/api/can-bo/danh-muc/tram", data={"ma_thiet_bi": "tram09", "ten": "Thiết bị đo kiểm thử", "ma_dia_ban": "1",
                                                       "nguong_kk": "800", "nguong_tds": "900", "dang_dung": "1"}))  # TC40
    khoa = kq["khoa"][1]
    loi(cb.post("/api/can-bo/danh-muc/tram", data={"ma_thiet_bi": "TRAM09", "ten": "Trùng", "ma_dia_ban": "1",
                                                   "nguong_kk": "800", "nguong_tds": "900"}), "đã tồn tại")
    assert api.post("/api/tram/so-lieu", json={"ma_thiet_bi": "TRAM09", "khoa": khoa, "khong_khi_ppm": 850, "tds_ppm": 100}).json()["vuot_nguong"]
    db = SessionLocal()
    t9 = db.scalar(select(M.TramQuanTrac).where(M.TramQuanTrac.MaThietBi == "TRAM09"))
    assert t9.LanGuiCuoi is not None and len(t9.so_lieu) == 1 and t9.KhoaBam != khoa                         # khóa chỉ lưu dạng băm
    db.close()
    ok(cb.post("/api/can-bo/danh-muc/tram/%d/cap-khoa" % t9.MaTram), "cấp khóa mới")
    assert api.post("/api/tram/so-lieu", json={"ma_thiet_bi": "TRAM09", "khoa": khoa, "khong_khi_ppm": 1, "tds_ppm": 1}).status_code == 401
    ok(cb.post("/api/can-bo/danh-muc/tram", data={"ma": str(t9.MaTram), "ma_thiet_bi": "TRAM09", "ten": "Thiết bị đo kiểm thử",
                                                  "ma_dia_ban": "1", "nguong_kk": "800", "nguong_tds": "900"}), "Đã lưu thiết bị")
    db = SessionLocal()
    assert db.get(M.TramQuanTrac, t9.MaTram).DangSuDung is False
    db.close()

    # ---- toàn vẹn: mỗi báo cáo tối đa một phân công hiệu lực, một bản công khai hiển thị
    db = SessionLocal()
    for bc in db.scalars(select(M.BaoCaoSuCo)):
        assert sum(p.TrangThai in TT.PC_HIEU_LUC for p in bc.phan_cong) <= 1
        assert sum(bool(k.DangHienThi) for k in bc.kiem_duyet) <= 1
        assert bc.lich_su and bc.lich_su[-1].TrangThaiMoi == bc.TrangThai
        assert len(bc.minh_chung) >= 1
    db.close()
    print("TẤT CẢ KIỂM THỬ ĐỀU ĐẠT")


if __name__ == "__main__":
    try:
        test_toan_bo()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
