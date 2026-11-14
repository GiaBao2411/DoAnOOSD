from sqlalchemy import (BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer,
                        LargeBinary, Numeric, SmallInteger, String, Unicode, UnicodeText, FetchedValue, text)
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import relationship

from .db import Base
from . import trang_thai as TT

DT = DateTime().with_variant(mssql.DATETIME2(), "mssql")
DEC96 = Numeric(9, 6, asdecimal=False)
DEC81 = Numeric(8, 1, asdecimal=False)
TINYINT = SmallInteger().with_variant(mssql.TINYINT(), "mssql")
BIGID = BigInteger().with_variant(Integer, "sqlite")
ROWVER = LargeBinary().with_variant(mssql.ROWVERSION(), "mssql")


def NV(n=None):
    return Unicode(n) if n else UnicodeText().with_variant(mssql.NVARCHAR("max"), "mssql")


def check_in(col, values, name):
    ms = CheckConstraint("%s IN (%s)" % (col, ", ".join("N'%s'" % v for v in values)), name=name).ddl_if(dialect="mssql")
    lite = CheckConstraint("%s IN (%s)" % (col, ", ".join("'%s'" % v for v in values)), name=name).ddl_if(dialect="sqlite")
    return [ms, lite]


def check(expr, name):
    return CheckConstraint(expr, name=name)


def where_in(col, values):
    return dict(mssql_where=text("%s IN (%s)" % (col, ", ".join("N'%s'" % v for v in values))),
                sqlite_where=text("%s IN (%s)" % (col, ", ".join("'%s'" % v for v in values))))


class NguoiBaoCao(Base):
    __tablename__ = "NguoiBaoCao"
    MaNguoiBaoCao = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(NV(100))
    SoDienThoai = Column(String(15))
    Email = Column(String(254))


class LoaiSuCo(Base):
    __tablename__ = "LoaiSuCo"
    MaLoai = Column(Integer, primary_key=True, autoincrement=True)
    TenLoai = Column(NV(100), nullable=False, unique=True)
    MoTa = Column(NV(500))
    DangSuDung = Column(Boolean, nullable=False, default=True, server_default=text("1"))


class DiaBan(Base):
    __tablename__ = "DiaBan"
    MaDiaBan = Column(Integer, primary_key=True, autoincrement=True)
    TenDiaBan = Column(NV(100), nullable=False)
    TinhThanh = Column(NV(100), nullable=False)
    DangSuDung = Column(Boolean, nullable=False, default=True, server_default=text("1"))


class DonViXuLy(Base):
    __tablename__ = "DonViXuLy"
    MaDonVi = Column(Integer, primary_key=True, autoincrement=True)
    MaDiaBan = Column(Integer, ForeignKey("DiaBan.MaDiaBan"))
    TenDonVi = Column(NV(150), nullable=False)
    DiaChi = Column(NV(200))
    SoDienThoai = Column(String(15))
    DangSuDung = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    dia_ban = relationship("DiaBan")


class CanBoXuLy(Base):
    __tablename__ = "CanBoXuLy"
    MaCanBo = Column(Integer, primary_key=True, autoincrement=True)
    HoTen = Column(NV(100), nullable=False)
    ChucVu = Column(NV(100))
    SoDienThoai = Column(String(15))


class TaiKhoan(Base):
    __tablename__ = "TaiKhoan"
    MaTaiKhoan = Column(Integer, primary_key=True, autoincrement=True)
    TenDangNhap = Column(String(50), nullable=False, unique=True)
    MatKhauBam = Column(String(255), nullable=False)
    LoaiTaiKhoan = Column(NV(20), nullable=False)
    MaCanBo = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"))
    MaDonVi = Column(Integer, ForeignKey("DonViXuLy.MaDonVi"))
    TrangThai = Column(NV(20), nullable=False, default=TT.TK_HOAT_DONG)
    PhaiDoiMatKhau = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    LanDangNhapCuoi = Column(DT)
    can_bo = relationship("CanBoXuLy")
    don_vi = relationship("DonViXuLy")
    __table_args__ = (
        *check_in("LoaiTaiKhoan", [TT.TK_CAN_BO, TT.TK_DON_VI], "CK_TaiKhoan_Loai"),
        *check_in("TrangThai", [TT.TK_HOAT_DONG, TT.TK_BI_KHOA], "CK_TaiKhoan_TrangThai"),
        check("(MaCanBo IS NOT NULL AND MaDonVi IS NULL) OR (MaCanBo IS NULL AND MaDonVi IS NOT NULL)", "CK_TaiKhoan_ChuSoHuu"),
        Index("UX_TaiKhoan_MaCanBo", "MaCanBo", unique=True,
              mssql_where=text("MaCanBo IS NOT NULL"), sqlite_where=text("MaCanBo IS NOT NULL")),
    )


class BaoCaoSuCo(Base):
    __tablename__ = "BaoCaoSuCo"
    MaBaoCao = Column(Integer, primary_key=True, autoincrement=True)
    MaTraCuu = Column(String(20), nullable=False, unique=True)
    MaNguoiBaoCao = Column(Integer, ForeignKey("NguoiBaoCao.MaNguoiBaoCao"))
    MaDiaBan = Column(Integer, ForeignKey("DiaBan.MaDiaBan"), nullable=False)
    MaLoai = Column(Integer, ForeignKey("LoaiSuCo.MaLoai"))
    MaCanBoTiepNhan = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"))
    MoTa = Column(NV(), nullable=False)
    DiaChi = Column(NV(250))
    ViDo = Column(DEC96)
    KinhDo = Column(DEC96)
    ThoiGianPhatHien = Column(DT, nullable=False)
    NgayGui = Column(DT, nullable=False)
    MucDoUuTien = Column(NV(20))
    TrangThai = Column(NV(30), nullable=False)
    LyDoKetThuc = Column(NV(500))
    RowVersion = Column(ROWVER, server_default=FetchedValue(), server_onupdate=FetchedValue())

    nguoi_bao_cao = relationship("NguoiBaoCao")
    dia_ban = relationship("DiaBan")
    loai = relationship("LoaiSuCo")
    can_bo_tiep_nhan = relationship("CanBoXuLy")
    minh_chung = relationship("MinhChungBaoCao", back_populates="bao_cao", order_by="MinhChungBaoCao.MaMinhChung")
    lich_su = relationship("LichSuTrangThai", back_populates="bao_cao", order_by="LichSuTrangThai.MaLichSu")
    phan_cong = relationship("PhanCongXuLy", back_populates="bao_cao", order_by="PhanCongXuLy.MaPhanCong")
    yeu_cau_bo_sung = relationship("YeuCauBoSung", back_populates="bao_cao", order_by="YeuCauBoSung.MaYeuCau")
    kiem_duyet = relationship("KiemDuyet", back_populates="bao_cao", order_by="KiemDuyet.MaKiemDuyet")
    __table_args__ = (
        *check_in("TrangThai", TT.BC_ALL, "CK_BaoCao_TrangThai"),
        *check_in("MucDoUuTien", TT.UU_TIEN, "CK_BaoCao_UuTien"),
        check("ThoiGianPhatHien <= NgayGui", "CK_BaoCao_ThoiGian"),
        check("ViDo IS NULL OR (ViDo BETWEEN -90 AND 90)", "CK_BaoCao_ViDo"),
        check("KinhDo IS NULL OR (KinhDo BETWEEN -180 AND 180)", "CK_BaoCao_KinhDo"),
        Index("IX_BaoCao_TrangThai_NgayGui", "TrangThai", "NgayGui"),
        Index("IX_BaoCao_DiaBan_NgayGui", "MaDiaBan", "NgayGui"),
    )


class YeuCauBoSung(Base):
    __tablename__ = "YeuCauBoSung"
    MaYeuCau = Column(Integer, primary_key=True, autoincrement=True)
    MaBaoCao = Column(Integer, ForeignKey("BaoCaoSuCo.MaBaoCao"), nullable=False)
    MaCanBo = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"), nullable=False)
    NoiDungYeuCau = Column(NV(1000), nullable=False)
    NgayYeuCau = Column(DT, nullable=False)
    HanBoSung = Column(DT, nullable=False)
    NoiDungPhanHoi = Column(NV())
    NgayPhanHoi = Column(DT)
    TrangThai = Column(NV(20), nullable=False)
    bao_cao = relationship("BaoCaoSuCo", back_populates="yeu_cau_bo_sung")
    can_bo = relationship("CanBoXuLy")
    __table_args__ = (
        *check_in("TrangThai", TT.YC_ALL, "CK_YeuCauBoSung_TrangThai"),
        check("HanBoSung > NgayYeuCau", "CK_YeuCauBoSung_Han"),
    )


class MinhChungBaoCao(Base):
    __tablename__ = "MinhChungBaoCao"
    MaMinhChung = Column(Integer, primary_key=True, autoincrement=True)
    MaBaoCao = Column(Integer, ForeignKey("BaoCaoSuCo.MaBaoCao"), nullable=False)
    MaYeuCau = Column(Integer, ForeignKey("YeuCauBoSung.MaYeuCau"))
    TenTep = Column(NV(255), nullable=False)
    LoaiTep = Column(String(10), nullable=False)
    KichThuoc = Column(BigInteger, nullable=False)
    DuongDan = Column(String(500), nullable=False)
    NgayTaiLen = Column(DT, nullable=False)
    DuocCongKhai = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    bao_cao = relationship("BaoCaoSuCo", back_populates="minh_chung")
    __table_args__ = (
        *check_in("LoaiTep", ["jpg", "png", "mp4"], "CK_MinhChungBaoCao_LoaiTep"),
        check("KichThuoc > 0", "CK_MinhChungBaoCao_KichThuoc"),
    )


class PhanCongXuLy(Base):
    __tablename__ = "PhanCongXuLy"
    MaPhanCong = Column(Integer, primary_key=True, autoincrement=True)
    MaBaoCao = Column(Integer, ForeignKey("BaoCaoSuCo.MaBaoCao"), nullable=False)
    MaCanBo = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"), nullable=False)
    MaDonVi = Column(Integer, ForeignKey("DonViXuLy.MaDonVi"), nullable=False)
    NoiDungNhiemVu = Column(NV(1000), nullable=False)
    NgayPhanCong = Column(DT, nullable=False)
    NgayTiepNhan = Column(DT)
    TrangThai = Column(NV(20), nullable=False)
    LyDoTraLai = Column(NV(500))
    RowVersion = Column(ROWVER, server_default=FetchedValue(), server_onupdate=FetchedValue())
    bao_cao = relationship("BaoCaoSuCo", back_populates="phan_cong")
    can_bo = relationship("CanBoXuLy")
    don_vi = relationship("DonViXuLy")
    cap_nhat = relationship("CapNhatXuLy", back_populates="phan_cong", order_by="CapNhatXuLy.MaCapNhat")
    nghiem_thu = relationship("NghiemThu", back_populates="phan_cong", order_by="NghiemThu.MaNghiemThu")
    __table_args__ = (
        *check_in("TrangThai", TT.PC_ALL, "CK_PhanCong_TrangThai"),
        Index("UX_PhanCong_HieuLuc", "MaBaoCao", unique=True, **where_in("TrangThai", TT.PC_HIEU_LUC)),
        Index("IX_PhanCong_DonVi_TrangThai", "MaDonVi", "TrangThai"),
    )


class CapNhatXuLy(Base):
    __tablename__ = "CapNhatXuLy"
    MaCapNhat = Column(Integer, primary_key=True, autoincrement=True)
    MaPhanCong = Column(Integer, ForeignKey("PhanCongXuLy.MaPhanCong"), nullable=False)
    MaTaiKhoan = Column(Integer, ForeignKey("TaiKhoan.MaTaiKhoan"), nullable=False)
    LoaiCapNhat = Column(NV(30), nullable=False)
    ThoiGian = Column(DT, nullable=False)
    PhanTramTienDo = Column(TINYINT)
    NoiDung = Column(NV(), nullable=False)
    ViDo = Column(DEC96)
    KinhDo = Column(DEC96)
    phan_cong = relationship("PhanCongXuLy", back_populates="cap_nhat")
    tai_khoan = relationship("TaiKhoan")
    minh_chung = relationship("MinhChungXuLy", back_populates="cap_nhat", order_by="MinhChungXuLy.MaMinhChung")
    __table_args__ = (
        *check_in("LoaiCapNhat", TT.CN_ALL, "CK_CapNhat_Loai"),
        check("PhanTramTienDo IS NULL OR (PhanTramTienDo BETWEEN 0 AND 100)", "CK_CapNhat_TienDo"),
    )


class MinhChungXuLy(Base):
    __tablename__ = "MinhChungXuLy"
    MaMinhChung = Column(Integer, primary_key=True, autoincrement=True)
    MaCapNhat = Column(Integer, ForeignKey("CapNhatXuLy.MaCapNhat"), nullable=False)
    GiaiDoan = Column(NV(10), nullable=False)
    TenTep = Column(NV(255), nullable=False)
    LoaiTep = Column(String(10), nullable=False)
    DuongDan = Column(String(500), nullable=False)
    NgayTaiLen = Column(DT, nullable=False)
    DuocCongKhai = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    cap_nhat = relationship("CapNhatXuLy", back_populates="minh_chung")
    __table_args__ = (
        *check_in("GiaiDoan", [TT.GD_TRUOC, TT.GD_SAU], "CK_MinhChungXuLy_GiaiDoan"),
        *check_in("LoaiTep", ["jpg", "png", "mp4"], "CK_MinhChungXuLy_LoaiTep"),
    )


class NghiemThu(Base):
    __tablename__ = "NghiemThu"
    MaNghiemThu = Column(Integer, primary_key=True, autoincrement=True)
    MaPhanCong = Column(Integer, ForeignKey("PhanCongXuLy.MaPhanCong"), nullable=False)
    MaCanBo = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"), nullable=False)
    ThoiGian = Column(DT, nullable=False)
    KetQua = Column(NV(30), nullable=False)
    NhanXet = Column(NV(1000))
    phan_cong = relationship("PhanCongXuLy", back_populates="nghiem_thu")
    can_bo = relationship("CanBoXuLy")
    __table_args__ = (*check_in("KetQua", TT.NT_ALL, "CK_NghiemThu_KetQua"),)


class KiemDuyet(Base):
    __tablename__ = "KiemDuyet"
    MaKiemDuyet = Column(Integer, primary_key=True, autoincrement=True)
    MaBaoCao = Column(Integer, ForeignKey("BaoCaoSuCo.MaBaoCao"), nullable=False)
    MaCanBo = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"), nullable=False)
    TieuDeCongKhai = Column(NV(200), nullable=False)
    NoiDungCongKhai = Column(NV(), nullable=False)
    DaKiemTraAnDanh = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    TrangThai = Column(NV(20), nullable=False)
    LyDo = Column(NV(500))
    ThoiGian = Column(DT, nullable=False)
    DangHienThi = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    bao_cao = relationship("BaoCaoSuCo", back_populates="kiem_duyet")
    can_bo = relationship("CanBoXuLy")
    __table_args__ = (
        *check_in("TrangThai", TT.KD_ALL, "CK_KiemDuyet_TrangThai"),
        check("DangHienThi = 0 OR DaKiemTraAnDanh = 1", "CK_KiemDuyet_AnDanh"),
        Index("UX_KiemDuyet_HienThi", "MaBaoCao", unique=True,
              mssql_where=text("DangHienThi = 1"), sqlite_where=text("DangHienThi = 1")),
    )


class LichSuTrangThai(Base):
    __tablename__ = "LichSuTrangThai"
    MaLichSu = Column(BIGID, primary_key=True, autoincrement=True)
    MaBaoCao = Column(Integer, ForeignKey("BaoCaoSuCo.MaBaoCao"), nullable=False)
    TrangThaiCu = Column(NV(30))
    TrangThaiMoi = Column(NV(30), nullable=False)
    ThoiGian = Column(DT, nullable=False)
    MaTaiKhoan = Column(Integer, ForeignKey("TaiKhoan.MaTaiKhoan"))
    GhiChu = Column(NV(500))
    bao_cao = relationship("BaoCaoSuCo", back_populates="lich_su")
    tai_khoan = relationship("TaiKhoan")
    __table_args__ = (Index("IX_LichSu_BaoCao_ThoiGian", "MaBaoCao", "ThoiGian"),)


class ThamSoHeThong(Base):
    __tablename__ = "ThamSoHeThong"
    MaThamSo = Column(String(50), primary_key=True)
    GiaTri = Column(NV(200), nullable=False)
    MoTa = Column(NV(500))
    MaCanBoCapNhat = Column(Integer, ForeignKey("CanBoXuLy.MaCanBo"))
    NgayCapNhat = Column(DT)
    can_bo = relationship("CanBoXuLy")


class TramQuanTrac(Base):
    __tablename__ = "TramQuanTrac"
    MaTram = Column(Integer, primary_key=True, autoincrement=True)
    MaDiaBan = Column(Integer, ForeignKey("DiaBan.MaDiaBan"), nullable=False)
    MaThietBi = Column(String(20), nullable=False, unique=True)
    TenTram = Column(NV(100), nullable=False)
    KhoaBam = Column(String(255), nullable=False)
    ViDo = Column(DEC96)
    KinhDo = Column(DEC96)
    NguongKhongKhi = Column(DEC81, nullable=False, default=TT.NGUONG_MAC_DINH, server_default=text(str(TT.NGUONG_MAC_DINH)))
    NguongTDS = Column(DEC81, nullable=False, default=TT.NGUONG_MAC_DINH, server_default=text(str(TT.NGUONG_MAC_DINH)))
    LanGuiCuoi = Column(DT)
    DangSuDung = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    dia_ban = relationship("DiaBan")
    so_lieu = relationship("SoLieuQuanTrac", back_populates="tram", order_by="SoLieuQuanTrac.ThoiGianDo")
    __table_args__ = (
        check("ViDo IS NULL OR (ViDo BETWEEN -90 AND 90)", "CK_Tram_ViDo"),
        check("KinhDo IS NULL OR (KinhDo BETWEEN -180 AND 180)", "CK_Tram_KinhDo"),
        check("NguongKhongKhi > 0 AND NguongTDS > 0", "CK_Tram_Nguong"),
    )


class SoLieuQuanTrac(Base):
    __tablename__ = "SoLieuQuanTrac"
    MaSoLieu = Column(BIGID, primary_key=True, autoincrement=True)
    MaTram = Column(Integer, ForeignKey("TramQuanTrac.MaTram"), nullable=False)
    ThoiGianDo = Column(DT, nullable=False)
    KhongKhiPPM = Column(DEC81, nullable=False)
    TdsPPM = Column(DEC81, nullable=False)
    VuotNguong = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    tram = relationship("TramQuanTrac", back_populates="so_lieu")
    __table_args__ = (
        check("KhongKhiPPM BETWEEN 0 AND %d" % TT.KHI_TOI_DA_PPM, "CK_SoLieu_KhongKhi"),
        check("TdsPPM BETWEEN 0 AND %d" % TT.TDS_TOI_DA_PPM, "CK_SoLieu_TDS"),
        Index("IX_SoLieu_Tram_ThoiGian", "MaTram", "ThoiGianDo"),
    )
