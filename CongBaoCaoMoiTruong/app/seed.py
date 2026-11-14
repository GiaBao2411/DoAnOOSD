import io
import math
import random
import shutil
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import inspect, select, text, update, func

from . import config
from . import models as M
from . import trang_thai as TT
from .db import Base, SessionLocal, engine, now
from .services import (bao_cao_service, bo_sung_service, cap_nhat_xu_ly_service, hien_truong_service,
                       kiem_duyet_service, nghiem_thu_service, phan_cong_service, tiep_nhan_service)
from .services.common import bam

ASSETS = Path(__file__).parent / "seed_assets"


class TepMau:
    def __init__(self, ten):
        self.filename = ten
        self.file = io.BytesIO((ASSETS / ten).read_bytes())


def teps(*ten):
    return [TepMau(t) for t in ten]


def dt_str(d):
    return d.strftime("%Y-%m-%dT%H:%M")


def lui_thoi_gian(db, ma_bc, ngay):
    dlt = timedelta(days=ngay)
    bc = db.get(M.BaoCaoSuCo, ma_bc)
    bc.NgayGui -= dlt
    bc.ThoiGianPhatHien -= dlt
    for h in bc.lich_su:
        h.ThoiGian -= dlt
    for y in bc.yeu_cau_bo_sung:
        y.NgayYeuCau -= dlt
        y.HanBoSung -= dlt
        if y.NgayPhanHoi:
            y.NgayPhanHoi -= dlt
    for m in bc.minh_chung:
        m.NgayTaiLen -= dlt
    for k in bc.kiem_duyet:
        k.ThoiGian -= dlt
    for p in bc.phan_cong:
        p.NgayPhanCong -= dlt
        if p.NgayTiepNhan:
            p.NgayTiepNhan -= dlt
        for c in p.cap_nhat:
            c.ThoiGian -= dlt
            for m in c.minh_chung:
                m.NgayTaiLen -= dlt
        for n in p.nghiem_thu:
            n.ThoiGian -= dlt
    db.commit()


def tao_danh_muc(db):
    for ma, gt, mt in TT.THAM_SO_MAC_DINH:
        db.add(M.ThamSoHeThong(MaThamSo=ma, GiaTri=gt, MoTa=mt))
    for ten, mt in [("Rác thải", "Đổ, tập kết rác trái phép"), ("Nước thải", "Xả nước thải chưa xử lý ra kênh, cống"),
                    ("Khói bụi", "Đốt rác, bụi công trình"), ("Tiếng ồn", "Ồn quá giờ quy định"),
                    ("Chất thải nguy hại", "Dầu nhớt, hóa chất, pin")]:
        db.add(M.LoaiSuCo(TenLoai=ten, MoTa=mt, DangSuDung=True))
    db_ = {}
    for ten in ["Phường Bình Đông", "Phường Chánh Hưng", "Phường Rạch Ông", "Phường Phú Định", "Phường Bình Tây"]:
        db_[ten] = M.DiaBan(TenDiaBan=ten, TinhThanh="TP. Hồ Chí Minh", DangSuDung=True)
        db.add(db_[ten])
    db.flush()
    dv = {}
    for ma, ten, dban in [("binhdong", "Đội vệ sinh môi trường Bình Đông", "Phường Bình Đông"),
                                 ("chanhhung", "Đội thu gom Chánh Hưng", "Phường Chánh Hưng"),
                                 ("rachong", "Đội công ích Rạch Ông", "Phường Rạch Ông"),
                                 ("phudinh", "Đội vệ sinh Phú Định", "Phường Phú Định")]:
        dv[ma] = M.DonViXuLy(TenDonVi=ten, MaDiaBan=db_[dban].MaDiaBan, DiaChi=dban + ", TP. Hồ Chí Minh",
                             SoDienThoai="028 3800 0000", DangSuDung=True)
        db.add(dv[ma])
    cb = M.CanBoXuLy(HoTen="Trần Thị Mai", ChucVu="Cán bộ quản lý môi trường")
    db.add(cb)
    db.flush()
    db.add(M.TaiKhoan(TenDangNhap="canbo", MatKhauBam=bam("Canbo@123"), LoaiTaiKhoan=TT.TK_CAN_BO,
                      MaCanBo=cb.MaCanBo, TrangThai=TT.TK_HOAT_DONG, PhaiDoiMatKhau=False))
    for ma, d in dv.items():
        db.add(M.TaiKhoan(TenDangNhap="donvi." + ma, MatKhauBam=bam("Donvi@123"), LoaiTaiKhoan=TT.TK_DON_VI,
                          MaDonVi=d.MaDonVi, TrangThai=TT.TK_HOAT_DONG, PhaiDoiMatKhau=False))
    db.commit()


def tao_bao_cao_mau(db):
    tk_cb = db.scalar(select(M.TaiKhoan).where(M.TaiKhoan.TenDangNhap == "canbo"))
    don_vi_tk = {t.TenDangNhap.split(".")[1]: t for t in db.scalars(select(M.TaiKhoan).where(M.TaiKhoan.MaDonVi != None))}
    dia_ban = {d.TenDiaBan: d.MaDiaBan for d in db.scalars(select(M.DiaBan))}
    loai = {l.TenLoai: l.MaLoai for l in db.scalars(select(M.LoaiSuCo))}
    dv = {t: tk.MaDonVi for t, tk in don_vi_tk.items()}
    ghi = []

    def gui(mo_ta, dban, dia_chi, lat, lng, anh, ho_ten=None):
        bc = bao_cao_service.gui_bao_cao(db, mo_ta, dt_str(now() - timedelta(hours=2)), dia_ban[dban], dia_chi,
                                         lat, lng, ho_ten, None, teps(*anh))
        ghi.append((bc.MaTraCuu,))
        return bc

    def hop_le(bc, l, ut):
        tiep_nhan_service.tiep_nhan(db, bc.MaBaoCao, tk_cb)
        tiep_nhan_service.xac_nhan_hop_le(db, bc.MaBaoCao, loai[l], ut, tk_cb)

    def giao(bc, ma_dv, nd):
        return phan_cong_service.giao_nhiem_vu(db, bc.MaBaoCao, dv[ma_dv], nd, tk_cb)

    def xu_ly(pc, ma_dv, ket_qua, anh_sau, tien_do=True):
        tk = don_vi_tk[ma_dv]
        hien_truong_service.nhan_nhiem_vu(db, pc.MaPhanCong, tk)
        hien_truong_service.ghi_nhan_hien_truong(db, pc.MaPhanCong, "Đã tới hiện trường, xác nhận sự cố đúng như phản ánh.",
                                                 pc.bao_cao.ViDo, pc.bao_cao.KinhDo, teps("hien_truong.jpg"), tk)
        if tien_do:
            cap_nhat_xu_ly_service.luu_tien_do(db, pc.MaPhanCong, 60, "Đã xử lý được phần lớn khối lượng.", tk)
        if ket_qua:
            cap_nhat_xu_ly_service.gui_ket_qua(db, pc.MaPhanCong, ket_qua, teps(*anh_sau), tk)

    def cong_khai(bc, tieu_de, noi_dung):
        anh = ["%s-%d" % (b, m.MaMinhChung) for b, m, _ in kiem_duyet_service.tat_ca_anh(db.get(M.BaoCaoSuCo, bc.MaBaoCao))
               if b == "xl"]
        kiem_duyet_service.quyet_dinh(db, bc.MaBaoCao, tieu_de, noi_dung, "1", anh, True, None, tk_cb)

    b = gui("Rác thải sinh hoạt tập kết trái phép ven kênh Đôi, bốc mùi hôi, một phần tràn xuống lòng kênh.",
            "Phường Bình Đông", "Đường số 5, gần cầu Kênh Đôi", 10.739512, 106.647031, ["rac_truoc.jpg", "rac_truoc_2.jpg"],
            "Nguyễn Văn An")
    hop_le(b, "Rác thải", "Cao")
    pc = giao(b, "binhdong", "Thu gom toàn bộ rác ven kênh, vớt rác dưới lòng kênh, phun khử mùi; chụp ảnh trước và sau.")
    xu_ly(pc, "binhdong", "Đã thu gom khoảng 2 tấn rác, vớt rác dưới kênh, phun khử mùi và lắp biển cấm đổ rác.", ["rac_sau.jpg"])
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_DAT, "Khu vực sạch, đạt yêu cầu.", tk_cb)
    cong_khai(b, "Đã thu gom rác thải tập kết ven kênh Đôi, Phường Bình Đông",
              "Đơn vị đã thu gom khoảng 2 tấn rác, vớt rác dưới lòng kênh, phun khử mùi và lắp biển cấm đổ rác. "
              "Khu vực sẽ được kiểm tra định kỳ hằng tuần.")
    lui_thoi_gian(db, b.MaBaoCao, 20)

    b = gui("Cống xả nước thải màu đen, mùi hôi chảy thẳng ra kênh vào ban đêm.", "Phường Chánh Hưng",
            "Hẻm 120 Phạm Hùng", 10.745210, 106.678830, ["nuoc_thai.jpg"])
    hop_le(b, "Nước thải", "Khẩn cấp")
    pc = giao(b, "chanhhung", "Kiểm tra nguồn xả, chặn cống tạm thời, lập danh sách hộ xả thải.")
    xu_ly(pc, "chanhhung", "Đã xác định nguồn xả từ cơ sở giặt ủi, chặn cống tạm và chuyển hồ sơ cho phường xử lý.", ["nuoc_sau.jpg"])
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_DAT, None, tk_cb)
    cong_khai(b, "Đã chặn cống xả nước thải ra kênh tại Phường Chánh Hưng",
              "Đơn vị xác định nguồn xả, chặn cống tạm thời và chuyển hồ sơ cho chính quyền địa phương xử lý theo quy định.")
    lui_thoi_gian(db, b.MaBaoCao, 12)

    b = gui("Bãi đất trống thường xuyên bị đốt rác, khói bay vào khu dân cư.", "Phường Rạch Ông", "Cuối đường Âu Dương Lân",
            10.748420, 106.689620, ["khoi_bui.jpg"])
    hop_le(b, "Khói bụi", "Trung bình")
    pc = giao(b, "rachong", "Dập lửa, thu dọn bãi rác, lắp biển cấm đốt rác.")
    xu_ly(pc, "rachong", "Đã dập lửa.", ["khoi_sau.jpg"])
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_CHUA_DAT, "Còn rác chưa dọn, cần thu dọn hết và lắp biển.", tk_cb)
    cap_nhat_xu_ly_service.gui_ket_qua(db, pc.MaPhanCong, "Đã thu dọn toàn bộ bãi và lắp biển cấm đốt rác.",
                                       teps("khoi_sau.jpg"), don_vi_tk["rachong"])
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_DAT, "Đạt.", tk_cb)
    cong_khai(b, "Đã xử lý điểm đốt rác tại Phường Rạch Ông",
              "Đơn vị đã dập lửa, thu dọn toàn bộ bãi rác và lắp biển cấm đốt rác.")
    lui_thoi_gian(db, b.MaBaoCao, 6)

    b = gui("Rác xây dựng đổ dưới chân cầu, lấn ra lòng đường.", "Phường Phú Định", "Chân cầu Nhị Thiên Đường",
            10.733900, 106.633200, ["rac_truoc_2.jpg"])
    hop_le(b, "Rác thải", "Cao")
    pc = giao(b, "phudinh", "Thu gom rác xây dựng, trả lại mặt đường.")
    xu_ly(pc, "phudinh", "Đã thu gom 3 xe rác xây dựng, mặt đường thông thoáng.", ["rac_sau.jpg"])
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_DAT, "Đạt.", tk_cb)
    lui_thoi_gian(db, b.MaBaoCao, 4)

    b = gui("Rác tồn đọng nhiều ngày tại điểm tập kết, ruồi nhặng nhiều.", "Phường Bình Đông", "Chợ Bình Đông, cổng sau",
            10.742300, 106.641800, ["rac_truoc.jpg"])
    hop_le(b, "Rác thải", "Trung bình")
    pc = giao(b, "binhdong", "Thu gom rác tồn đọng, vệ sinh điểm tập kết.")
    xu_ly(pc, "binhdong", "Đã thu gom rác tồn, rửa và phun khử trùng điểm tập kết.", ["rac_sau.jpg"])
    lui_thoi_gian(db, b.MaBaoCao, 3)

    b = gui("Bùn và rác đọng kín miệng cống thoát nước, mưa là ngập.", "Phường Chánh Hưng", "Đường Tạ Quang Bửu",
            10.738800, 106.669500, ["nuoc_thai.jpg"])
    hop_le(b, "Nước thải", "Cao")
    pc = giao(b, "chanhhung", "Nạo vét miệng cống, thu gom bùn rác.")
    xu_ly(pc, "chanhhung", None, None)
    lui_thoi_gian(db, b.MaBaoCao, 2)

    b = gui("Có người đổ dầu nhớt thải xuống cống trước tiệm sửa xe.", "Phường Phú Định", "Đường Phú Định",
            10.731500, 106.628900, ["nuoc_thai.jpg"])
    hop_le(b, "Chất thải nguy hại", "Khẩn cấp")
    giao(b, "phudinh", "Kiểm tra, thu hồi dầu nhớt, nhắc nhở cơ sở.")
    lui_thoi_gian(db, b.MaBaoCao, 3)

    b = gui("Tiếng ồn từ xưởng cơ khí hoạt động sau 22 giờ.", "Phường Rạch Ông", "Đường Dương Bá Trạc",
            10.746100, 106.692300, ["binh_thuong.jpg"])
    hop_le(b, "Tiếng ồn", "Thấp")
    lui_thoi_gian(db, b.MaBaoCao, 1)

    b = gui("Có mùi lạ gần trường học.", "Phường Bình Tây", None, 10.750100, 106.636500, ["binh_thuong.jpg"])
    tiep_nhan_service.tiep_nhan(db, b.MaBaoCao, tk_cb)
    tiep_nhan_service.yeu_cau_bo_sung(db, b.MaBaoCao, "Vui lòng cho biết thời điểm có mùi và gửi thêm ảnh khu vực.",
                                      None, tk_cb)
    lui_thoi_gian(db, b.MaBaoCao, 8)

    b = gui("Có đống rác lạ gần nhà văn hóa.", "Phường Bình Đông", None, 10.741000, 106.645500, ["rac_truoc.jpg"])
    tiep_nhan_service.tiep_nhan(db, b.MaBaoCao, tk_cb)
    tiep_nhan_service.yeu_cau_bo_sung(db, b.MaBaoCao, "Vui lòng ghi rõ địa chỉ và gửi ảnh chụp rộng hơn.", None, tk_cb)

    b = gui("Hàng xóm phơi đồ ra lối đi.", "Phường Bình Tây", "Hẻm 12", None, None, ["binh_thuong.jpg"])
    tiep_nhan_service.tiep_nhan(db, b.MaBaoCao, tk_cb)
    tiep_nhan_service.tu_choi(db, b.MaBaoCao, "Nội dung không thuộc phạm vi sự cố môi trường.", tk_cb)
    lui_thoi_gian(db, b.MaBaoCao, 9)

    b = gui("Nghi có người đổ rác ban đêm ở góc đường.", "Phường Rạch Ông", "Góc Âu Dương Lân – Phạm Thế Hiển",
            10.744800, 106.686900, ["rac_truoc_2.jpg"])
    hop_le(b, "Rác thải", "Thấp")
    pc = giao(b, "rachong", "Kiểm tra góc đường, thu gom nếu có.")
    tk = don_vi_tk["rachong"]
    hien_truong_service.nhan_nhiem_vu(db, pc.MaPhanCong, tk)
    hien_truong_service.bao_khong_co_su_co(db, pc.MaPhanCong, "Kiểm tra 2 lần, khu vực sạch, không phát hiện rác.",
                                           10.744820, 106.686950, teps("binh_thuong.jpg"), tk)
    nghiem_thu_service.nghiem_thu(db, pc.MaPhanCong, TT.NT_KHONG_CO_SU_CO, "Đồng ý với kết quả kiểm tra.", tk_cb)
    lui_thoi_gian(db, b.MaBaoCao, 10)

    gui("Khói đen từ ống khói lò nấu, bụi bám đầy mái nhà.", "Phường Chánh Hưng", "Đường Phạm Hùng", 10.747900, 106.676100,
        ["khoi_bui.jpg"], "Phạm Thị Lan")
    gui("Rác thải bị vứt đầy dưới gầm cầu, có cả túi ni-lông và xốp.", "Phường Bình Đông", "Gầm cầu Chà Và",
        10.746900, 106.652300, ["rac_truoc.jpg", "rac_truoc_2.jpg"])
    return ghi


def tao_csdl_neu_chua_co():
    if not config.DATABASE_URL.startswith("mssql"):
        return
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    url = make_url(config.DATABASE_URL)
    ten = url.database
    eng = create_engine(url.set(database="master"), isolation_level="AUTOCOMMIT")
    try:
        with eng.connect() as c:
            if c.scalar(text("SELECT DB_ID(:t)"), {"t": ten}) is None:
                c.execute(text("CREATE DATABASE [%s]" % ten.replace("]", "]]")))
                print("Đã tạo database %s trên SQL Server." % ten)
            else:
                print("Database %s đã có sẵn." % ten)
    finally:
        eng.dispose()


TRAM_MAU = [
    ("TRAM01", "KhoaTram01", "Thiết bị đo kênh Đôi", "Phường Bình Đông", 10.739400, 106.647000, "khoi"),
    ("TRAM02", "KhoaTram02", "Thiết bị đo chợ Phạm Thế Hiển", "Phường Chánh Hưng", 10.745200, 106.664800, "on_dinh"),
    ("TRAM03", "KhoaTram03", "Thiết bị đo rạch Ông Lớn", "Phường Rạch Ông", 10.742300, 106.689000, "nuoc_thai"),
]


def tao_tram_mau(db):
    for ma, gt, mt in TT.THAM_SO_MAC_DINH:
        if not db.get(M.ThamSoHeThong, ma):
            db.add(M.ThamSoHeThong(MaThamSo=ma, GiaTri=gt, MoTa=mt))
    dia_ban = {d.TenDiaBan: d.MaDiaBan for d in db.scalars(select(M.DiaBan))}
    rnd = random.Random(2026)
    t_now = now()
    for ma, khoa, ten, ph, lat, lng, kieu in TRAM_MAU:
        tr = M.TramQuanTrac(MaThietBi=ma, KhoaBam=bam(khoa), TenTram=ten, MaDiaBan=dia_ban[ph], ViDo=lat, KinhDo=lng,
                            NguongKhongKhi=TT.NGUONG_MAC_DINH, NguongTDS=TT.NGUONG_MAC_DINH, DangSuDung=True)
        db.add(tr)
        db.flush()
        rows = []
        for k in range(180, 0, -1):
            if kieu == "nuoc_thai" and k < 70:
                continue
            t = t_now - timedelta(minutes=k)
            kk = 420 + 40 * math.sin(k / 9) + rnd.uniform(-15, 15)
            tds = 300 + rnd.uniform(-10, 10)
            if kieu == "khoi" and 60 <= k <= 100:
                kk += 1100 * math.sin(math.pi * (100 - k) / 40)
            if kieu == "on_dinh":
                tds = 180 + rnd.uniform(-8, 8)
            if kieu == "nuoc_thai":
                tds = 650 + 600 * max(0, math.sin(math.pi * (180 - k) / 110)) + rnd.uniform(-20, 20)
            kk, tds = round(max(kk, 0), 1), round(max(tds, 0), 1)
            rows.append(M.SoLieuQuanTrac(MaTram=tr.MaTram, ThoiGianDo=t, KhongKhiPPM=kk, TdsPPM=tds,
                                         VuotNguong=kk > tr.NguongKhongKhi or tds > tr.NguongTDS))
        db.add_all(rows)
        tr.LanGuiCuoi = rows[-1].ThoiGianDo
    db.commit()
    return ["  %s — khóa: %s   (%s, %s)" % (ma, khoa, ten, ph) for ma, khoa, ten, ph, *_ in TRAM_MAU]


def _sqlite_dung_lai_bang(bang):
    from sqlalchemy.schema import CreateIndex, CreateTable
    ten, tam = bang.name, bang.name + "_moi"
    tao = str(CreateTable(bang).compile(engine)).replace('CREATE TABLE "%s"' % ten, 'CREATE TABLE "%s"' % tam, 1)
    cot = ", ".join('"%s"' % c.name for c in bang.columns)
    raw = engine.raw_connection()
    try:
        con = raw.driver_connection
        con.isolation_level = None
        con.execute("PRAGMA foreign_keys = OFF")
        con.execute("BEGIN")
        con.execute(tao)
        con.execute('INSERT INTO "%s" (%s) SELECT %s FROM "%s"' % (tam, cot, cot, ten))
        con.execute('DROP TABLE "%s"' % ten)
        con.execute('ALTER TABLE "%s" RENAME TO "%s"' % (tam, ten))
        for ix in bang.indexes:
            con.execute(str(CreateIndex(ix).compile(engine)))
        con.execute("COMMIT")
        con.execute("PRAGMA foreign_keys = ON")
    finally:
        raw.close()


def nang_cap_csdl_cu():
    mssql = engine.dialect.name == "mssql"
    cot = lambda bang: [c["name"] for c in inspect(engine).get_columns(bang)]
    if "MaBiMatBam" in cot("BaoCaoSuCo"):
        with engine.begin() as c:
            c.execute(text("ALTER TABLE BaoCaoSuCo DROP COLUMN MaBiMatBam"))
        print("Đã xóa cột mã bí mật cũ (MaBiMatBam).")
    if "Email" not in cot("NguoiBaoCao"):
        with engine.begin() as c:
            c.execute(text("ALTER TABLE NguoiBaoCao ADD %s VARCHAR(254) NULL" % ("Email" if mssql else "COLUMN Email")))
        print("Đã thêm cột Email cho bảng NguoiBaoCao.")
    cu, moi = "Chờ nghiệm thu", TT.BC_CHO_NGHIEM_THU
    if mssql:
        with engine.begin() as c:
            for bang, ck, ds in (("BaoCaoSuCo", "CK_BaoCao_TrangThai", TT.BC_ALL), ("PhanCongXuLy", "CK_PhanCong_TrangThai", TT.PC_ALL)):
                dinh_nghia = c.execute(text("SELECT definition FROM sys.check_constraints WHERE name = :n"), {"n": ck}).scalar()
                if dinh_nghia and cu in dinh_nghia:
                    if bang == "PhanCongXuLy":
                        for ix in ("UX_PhanCong_HieuLuc", "IX_PhanCong_ThoiHan"):
                            if c.execute(text("SELECT 1 FROM sys.indexes WHERE name = :n"), {"n": ix}).scalar():
                                c.execute(text("DROP INDEX %s ON PhanCongXuLy" % ix))
                    c.execute(text("ALTER TABLE %s DROP CONSTRAINT %s" % (bang, ck)))
                    c.execute(text("UPDATE %s SET TrangThai = :moi WHERE TrangThai = :cu" % bang), {"moi": moi, "cu": cu})
                    c.execute(text("ALTER TABLE %s ADD CONSTRAINT %s CHECK (TrangThai IN (%s))"
                                   % (bang, ck, ", ".join("N'%s'" % v for v in ds))))
                    if bang == "PhanCongXuLy":
                        loc = ", ".join("N'%s'" % v for v in TT.PC_HIEU_LUC)
                        c.execute(text("CREATE UNIQUE INDEX UX_PhanCong_HieuLuc ON PhanCongXuLy (MaBaoCao) WHERE TrangThai IN (%s)" % loc))
                    print("Đã đổi trạng thái '%s' thành '%s' trong bảng %s." % (cu, moi, bang))
            c.execute(text("UPDATE LichSuTrangThai SET TrangThaiCu = :moi WHERE TrangThaiCu = :cu"), {"moi": moi, "cu": cu})
            c.execute(text("UPDATE LichSuTrangThai SET TrangThaiMoi = :moi WHERE TrangThaiMoi = :cu"), {"moi": moi, "cu": cu})
    if "ThoiHanXuLy" in cot("PhanCongXuLy"):
        with engine.begin() as c:
            if mssql:
                if c.execute(text("SELECT 1 FROM sys.indexes WHERE name = 'IX_PhanCong_ThoiHan'")).scalar():
                    c.execute(text("DROP INDEX IX_PhanCong_ThoiHan ON PhanCongXuLy"))
                if c.execute(text("SELECT 1 FROM sys.check_constraints WHERE name = 'CK_PhanCong_ThoiHan'")).scalar():
                    c.execute(text("ALTER TABLE PhanCongXuLy DROP CONSTRAINT CK_PhanCong_ThoiHan"))
                c.execute(text("ALTER TABLE PhanCongXuLy DROP COLUMN ThoiHanXuLy"))
            c.execute(text("DELETE FROM ThamSoHeThong WHERE MaThamSo IN "
                           "('HAN_KHAN_CAP_NGAY', 'HAN_CAO_NGAY', 'HAN_TRUNG_BINH_NGAY', 'HAN_THAP_NGAY')"))
        if not mssql:
            _sqlite_dung_lai_bang(M.PhanCongXuLy.__table__)
        print("Đã bỏ thời hạn xử lý (cột ThoiHanXuLy) khỏi bảng PhanCongXuLy.")


def main():
    reset = "--reset" in sys.argv
    try:
        tao_csdl_neu_chua_co()
        with engine.connect():
            pass
    except Exception as e:
        print("\nKHÔNG KẾT NỐI ĐƯỢC CƠ SỞ DỮ LIỆU:\n  %s\n" % str(e).splitlines()[0][:400])
        print("Kiểm tra lại:\n"
              "  1. SQL Server (SQLEXPRESS) đã cài và đang chạy (services.msc > SQL Server (SQLEXPRESS)).\n"
              "  2. Đã cài 'ODBC Driver 17 for SQL Server' (hoặc 18 thì sửa driver trong .env).\n"
              "  3. DATABASE_URL trong tệp .env đúng tên máy chủ\\instance (xem README.md, mục 5).")
        sys.exit(1)
    if reset:
        with engine.begin() as c:
            for t in ("ThongBao", "YeuCauGiaHan"):
                if inspect(engine).has_table(t):
                    c.execute(text("DROP TABLE %s" % t))
        Base.metadata.drop_all(engine)
        shutil.rmtree(config.UPLOAD_DIR / "bang_chung", ignore_errors=True)
        print("Đã xóa các bảng cũ.")
    Base.metadata.create_all(engine)
    nang_cap_csdl_cu()
    print("Đã tạo/kiểm tra 18 bảng.")
    db = SessionLocal()
    try:
        if db.scalar(select(func.count()).select_from(M.TaiKhoan)) > 0:
            if db.scalar(select(func.count()).select_from(M.TramQuanTrac)) == 0:
                print("Bổ sung thiết bị đo mẫu vào CSDL đã có:")
                print("\n".join(tao_tram_mau(db)))
            print("CSDL đã có dữ liệu — bỏ qua tạo dữ liệu mẫu. (Dùng --reset để làm lại từ đầu.)")
            return
        tao_danh_muc(db)
        ghi = tao_bao_cao_mau(db)
        tram = tao_tram_mau(db)
        lines = ["TÀI KHOẢN MẪU (đăng nhập tại /dang-nhap)",
                 "  canbo / Canbo@123              cán bộ quản lý (xử lý báo cáo + danh mục, tài khoản đơn vị, thiết bị IoT)",
                 "  donvi.binhdong / Donvi@123     đơn vị (tương tự donvi.chanhhung, donvi.rachong, donvi.phudinh)",
                 "", "BÁO CÁO MẪU (mã báo cáo   (trạng thái lúc tạo)):"]
        tt = dict(db.execute(select(M.BaoCaoSuCo.MaTraCuu, M.BaoCaoSuCo.TrangThai)).all())
        lines += ["  %s   (%s)" % (g[0], tt.get(g[0], "")) for g in ghi]
        lines.append("  (Báo cáo đang Chờ bổ sung còn hạn là %s — dùng để thử chức năng Bổ sung thông tin.)" % ghi[9][0])
        lines += ["", "THIẾT BỊ ĐO IoT MẪU (mã thiết bị — khóa, dùng cho mạch Pico / Wokwi / tệp giả lập):"] + tram
        lines.append("  (Số liệu mẫu là 3 giờ trước lúc tạo; chạy python tools\\gia_lap_tram.py để có số liệu mới mỗi 10 giây.)")
        txt = "\n".join(lines)
        (config.BASE_DIR / "TAI_KHOAN_VA_DU_LIEU_MAU.txt").write_text(txt + "\n", encoding="utf-8")
        print(txt)
        print("\nĐã lưu danh sách trên vào tệp TAI_KHOAN_VA_DU_LIEU_MAU.txt")
    finally:
        db.close()


if __name__ == "__main__":
    main()
