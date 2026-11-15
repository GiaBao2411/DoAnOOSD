IF DB_ID(N'CongBaoCaoMoiTruong') IS NULL CREATE DATABASE CongBaoCaoMoiTruong;
GO
USE CongBaoCaoMoiTruong;
GO

CREATE TABLE [CanBoXuLy] (
	[MaCanBo] INTEGER NOT NULL IDENTITY,
	[HoTen] NVARCHAR(100) NOT NULL,
	[ChucVu] NVARCHAR(100) NULL,
	[SoDienThoai] VARCHAR(15) NULL,
	PRIMARY KEY ([MaCanBo])
);
GO

CREATE TABLE [DiaBan] (
	[MaDiaBan] INTEGER NOT NULL IDENTITY,
	[TenDiaBan] NVARCHAR(100) NOT NULL,
	[TinhThanh] NVARCHAR(100) NOT NULL,
	[DangSuDung] BIT NOT NULL DEFAULT 1,
	PRIMARY KEY ([MaDiaBan])
);
GO

CREATE TABLE [LoaiSuCo] (
	[MaLoai] INTEGER NOT NULL IDENTITY,
	[TenLoai] NVARCHAR(100) NOT NULL,
	[MoTa] NVARCHAR(500) NULL,
	[DangSuDung] BIT NOT NULL DEFAULT 1,
	PRIMARY KEY ([MaLoai]),
	UNIQUE ([TenLoai])
);
GO

CREATE TABLE [NguoiBaoCao] (
	[MaNguoiBaoCao] INTEGER NOT NULL IDENTITY,
	[HoTen] NVARCHAR(100) NULL,
	[SoDienThoai] VARCHAR(15) NULL,
	[Email] VARCHAR(254) NULL,
	PRIMARY KEY ([MaNguoiBaoCao])
);
GO

CREATE TABLE [BaoCaoSuCo] (
	[MaBaoCao] INTEGER NOT NULL IDENTITY,
	[MaTraCuu] VARCHAR(20) NOT NULL,
	[MaNguoiBaoCao] INTEGER NULL,
	[MaDiaBan] INTEGER NOT NULL,
	[MaLoai] INTEGER NULL,
	[MaCanBoTiepNhan] INTEGER NULL,
	[MoTa] NVARCHAR(max) NOT NULL,
	[DiaChi] NVARCHAR(250) NULL,
	[ViDo] NUMERIC(9, 6) NULL,
	[KinhDo] NUMERIC(9, 6) NULL,
	[ThoiGianPhatHien] DATETIME2 NOT NULL,
	[NgayGui] DATETIME2 NOT NULL,
	[MucDoUuTien] NVARCHAR(20) NULL,
	[TrangThai] NVARCHAR(30) NOT NULL,
	[LyDoKetThuc] NVARCHAR(500) NULL,
	[RowVersion] ROWVERSION NULL,
	PRIMARY KEY ([MaBaoCao]),
	CONSTRAINT [CK_BaoCao_TrangThai] CHECK (TrangThai IN (N'Mới gửi', N'Đang xem xét', N'Chờ bổ sung', N'Chờ phân công', N'Đã phân công', N'Đang xử lý', N'Chờ duyệt kết quả', N'Chờ công khai', N'Hoàn tất', N'Bị từ chối', N'Đã đóng')),
	CONSTRAINT [CK_BaoCao_UuTien] CHECK (MucDoUuTien IN (N'Khẩn cấp', N'Cao', N'Trung bình', N'Thấp')),
	CONSTRAINT [CK_BaoCao_ThoiGian] CHECK (ThoiGianPhatHien <= NgayGui),
	CONSTRAINT [CK_BaoCao_ViDo] CHECK (ViDo IS NULL OR (ViDo BETWEEN -90 AND 90)),
	CONSTRAINT [CK_BaoCao_KinhDo] CHECK (KinhDo IS NULL OR (KinhDo BETWEEN -180 AND 180)),
	UNIQUE ([MaTraCuu]),
	FOREIGN KEY([MaNguoiBaoCao]) REFERENCES [NguoiBaoCao] ([MaNguoiBaoCao]),
	FOREIGN KEY([MaDiaBan]) REFERENCES [DiaBan] ([MaDiaBan]),
	FOREIGN KEY([MaLoai]) REFERENCES [LoaiSuCo] ([MaLoai]),
	FOREIGN KEY([MaCanBoTiepNhan]) REFERENCES [CanBoXuLy] ([MaCanBo])
);
GO
CREATE INDEX [IX_BaoCao_DiaBan_NgayGui] ON [BaoCaoSuCo] ([MaDiaBan], [NgayGui]);
GO
CREATE INDEX [IX_BaoCao_TrangThai_NgayGui] ON [BaoCaoSuCo] ([TrangThai], [NgayGui]);
GO

CREATE TABLE [DonViXuLy] (
	[MaDonVi] INTEGER NOT NULL IDENTITY,
	[MaDiaBan] INTEGER NULL,
	[TenDonVi] NVARCHAR(150) NOT NULL,
	[DiaChi] NVARCHAR(200) NULL,
	[SoDienThoai] VARCHAR(15) NULL,
	[DangSuDung] BIT NOT NULL DEFAULT 1,
	PRIMARY KEY ([MaDonVi]),
	FOREIGN KEY([MaDiaBan]) REFERENCES [DiaBan] ([MaDiaBan])
);
GO

CREATE TABLE [ThamSoHeThong] (
	[MaThamSo] VARCHAR(50) NOT NULL,
	[GiaTri] NVARCHAR(200) NOT NULL,
	[MoTa] NVARCHAR(500) NULL,
	[MaCanBoCapNhat] INTEGER NULL,
	[NgayCapNhat] DATETIME2 NULL,
	PRIMARY KEY ([MaThamSo]),
	FOREIGN KEY([MaCanBoCapNhat]) REFERENCES [CanBoXuLy] ([MaCanBo])
);
GO

CREATE TABLE [TramQuanTrac] (
	[MaTram] INTEGER NOT NULL IDENTITY,
	[MaDiaBan] INTEGER NOT NULL,
	[MaThietBi] VARCHAR(20) NOT NULL,
	[TenTram] NVARCHAR(100) NOT NULL,
	[KhoaBam] VARCHAR(255) NOT NULL,
	[ViDo] NUMERIC(9, 6) NULL,
	[KinhDo] NUMERIC(9, 6) NULL,
	[NguongKhongKhi] NUMERIC(8, 1) NOT NULL DEFAULT 1000,
	[NguongTDS] NUMERIC(8, 1) NOT NULL DEFAULT 1000,
	[LanGuiCuoi] DATETIME2 NULL,
	[DangSuDung] BIT NOT NULL DEFAULT 1,
	PRIMARY KEY ([MaTram]),
	CONSTRAINT [CK_Tram_ViDo] CHECK (ViDo IS NULL OR (ViDo BETWEEN -90 AND 90)),
	CONSTRAINT [CK_Tram_KinhDo] CHECK (KinhDo IS NULL OR (KinhDo BETWEEN -180 AND 180)),
	CONSTRAINT [CK_Tram_Nguong] CHECK (NguongKhongKhi > 0 AND NguongTDS > 0),
	FOREIGN KEY([MaDiaBan]) REFERENCES [DiaBan] ([MaDiaBan]),
	UNIQUE ([MaThietBi])
);
GO

CREATE TABLE [KiemDuyet] (
	[MaKiemDuyet] INTEGER NOT NULL IDENTITY,
	[MaBaoCao] INTEGER NOT NULL,
	[MaCanBo] INTEGER NOT NULL,
	[TieuDeCongKhai] NVARCHAR(200) NOT NULL,
	[NoiDungCongKhai] NVARCHAR(max) NOT NULL,
	[DaKiemTraAnDanh] BIT NOT NULL DEFAULT 0,
	[TrangThai] NVARCHAR(20) NOT NULL,
	[LyDo] NVARCHAR(500) NULL,
	[ThoiGian] DATETIME2 NOT NULL,
	[DangHienThi] BIT NOT NULL DEFAULT 0,
	PRIMARY KEY ([MaKiemDuyet]),
	CONSTRAINT [CK_KiemDuyet_TrangThai] CHECK (TrangThai IN (N'Chờ duyệt', N'Đã duyệt', N'Không duyệt')),
	CONSTRAINT [CK_KiemDuyet_AnDanh] CHECK (DangHienThi = 0 OR DaKiemTraAnDanh = 1),
	FOREIGN KEY([MaBaoCao]) REFERENCES [BaoCaoSuCo] ([MaBaoCao]),
	FOREIGN KEY([MaCanBo]) REFERENCES [CanBoXuLy] ([MaCanBo])
);
GO
CREATE UNIQUE INDEX [UX_KiemDuyet_HienThi] ON [KiemDuyet] ([MaBaoCao]) WHERE DangHienThi = 1;
GO

CREATE TABLE [PhanCongXuLy] (
	[MaPhanCong] INTEGER NOT NULL IDENTITY,
	[MaBaoCao] INTEGER NOT NULL,
	[MaCanBo] INTEGER NOT NULL,
	[MaDonVi] INTEGER NOT NULL,
	[NoiDungNhiemVu] NVARCHAR(1000) NOT NULL,
	[NgayPhanCong] DATETIME2 NOT NULL,
	[NgayTiepNhan] DATETIME2 NULL,
	[TrangThai] NVARCHAR(20) NOT NULL,
	[LyDoTraLai] NVARCHAR(500) NULL,
	[RowVersion] ROWVERSION NULL,
	PRIMARY KEY ([MaPhanCong]),
	CONSTRAINT [CK_PhanCong_TrangThai] CHECK (TrangThai IN (N'Chờ tiếp nhận', N'Đang xử lý', N'Chờ duyệt kết quả', N'Hoàn thành', N'Bị trả lại', N'Đã thay thế')),
	FOREIGN KEY([MaBaoCao]) REFERENCES [BaoCaoSuCo] ([MaBaoCao]),
	FOREIGN KEY([MaCanBo]) REFERENCES [CanBoXuLy] ([MaCanBo]),
	FOREIGN KEY([MaDonVi]) REFERENCES [DonViXuLy] ([MaDonVi])
);
GO
CREATE INDEX [IX_PhanCong_DonVi_TrangThai] ON [PhanCongXuLy] ([MaDonVi], [TrangThai]);
GO
CREATE UNIQUE INDEX [UX_PhanCong_HieuLuc] ON [PhanCongXuLy] ([MaBaoCao]) WHERE TrangThai IN (N'Chờ tiếp nhận', N'Đang xử lý', N'Chờ duyệt kết quả');
GO

CREATE TABLE [SoLieuQuanTrac] (
	[MaSoLieu] BIGINT NOT NULL IDENTITY,
	[MaTram] INTEGER NOT NULL,
	[ThoiGianDo] DATETIME2 NOT NULL,
	[KhongKhiPPM] NUMERIC(8, 1) NOT NULL,
	[TdsPPM] NUMERIC(8, 1) NOT NULL,
	[VuotNguong] BIT NOT NULL DEFAULT 0,
	PRIMARY KEY ([MaSoLieu]),
	CONSTRAINT [CK_SoLieu_KhongKhi] CHECK (KhongKhiPPM BETWEEN 0 AND 5000),
	CONSTRAINT [CK_SoLieu_TDS] CHECK (TdsPPM BETWEEN 0 AND 3000),
	FOREIGN KEY([MaTram]) REFERENCES [TramQuanTrac] ([MaTram])
);
GO
CREATE INDEX [IX_SoLieu_Tram_ThoiGian] ON [SoLieuQuanTrac] ([MaTram], [ThoiGianDo]);
GO

CREATE TABLE [TaiKhoan] (
	[MaTaiKhoan] INTEGER NOT NULL IDENTITY,
	[TenDangNhap] VARCHAR(50) NOT NULL,
	[MatKhauBam] VARCHAR(255) NOT NULL,
	[LoaiTaiKhoan] NVARCHAR(20) NOT NULL,
	[MaCanBo] INTEGER NULL,
	[MaDonVi] INTEGER NULL,
	[TrangThai] NVARCHAR(20) NOT NULL,
	[PhaiDoiMatKhau] BIT NOT NULL DEFAULT 1,
	[LanDangNhapCuoi] DATETIME2 NULL,
	PRIMARY KEY ([MaTaiKhoan]),
	CONSTRAINT [CK_TaiKhoan_Loai] CHECK (LoaiTaiKhoan IN (N'Cán bộ', N'Đơn vị')),
	CONSTRAINT [CK_TaiKhoan_TrangThai] CHECK (TrangThai IN (N'Hoạt động', N'Bị khóa')),
	CONSTRAINT [CK_TaiKhoan_ChuSoHuu] CHECK ((MaCanBo IS NOT NULL AND MaDonVi IS NULL) OR (MaCanBo IS NULL AND MaDonVi IS NOT NULL)),
	UNIQUE ([TenDangNhap]),
	FOREIGN KEY([MaCanBo]) REFERENCES [CanBoXuLy] ([MaCanBo]),
	FOREIGN KEY([MaDonVi]) REFERENCES [DonViXuLy] ([MaDonVi])
);
GO
CREATE UNIQUE INDEX [UX_TaiKhoan_MaCanBo] ON [TaiKhoan] ([MaCanBo]) WHERE MaCanBo IS NOT NULL;
GO

CREATE TABLE [YeuCauBoSung] (
	[MaYeuCau] INTEGER NOT NULL IDENTITY,
	[MaBaoCao] INTEGER NOT NULL,
	[MaCanBo] INTEGER NOT NULL,
	[NoiDungYeuCau] NVARCHAR(1000) NOT NULL,
	[NgayYeuCau] DATETIME2 NOT NULL,
	[HanBoSung] DATETIME2 NOT NULL,
	[NoiDungPhanHoi] NVARCHAR(max) NULL,
	[NgayPhanHoi] DATETIME2 NULL,
	[TrangThai] NVARCHAR(20) NOT NULL,
	PRIMARY KEY ([MaYeuCau]),
	CONSTRAINT [CK_YeuCauBoSung_TrangThai] CHECK (TrangThai IN (N'Chờ phản hồi', N'Đã phản hồi', N'Quá hạn')),
	CONSTRAINT [CK_YeuCauBoSung_Han] CHECK (HanBoSung > NgayYeuCau),
	FOREIGN KEY([MaBaoCao]) REFERENCES [BaoCaoSuCo] ([MaBaoCao]),
	FOREIGN KEY([MaCanBo]) REFERENCES [CanBoXuLy] ([MaCanBo])
);
GO

CREATE TABLE [CapNhatXuLy] (
	[MaCapNhat] INTEGER NOT NULL IDENTITY,
	[MaPhanCong] INTEGER NOT NULL,
	[MaTaiKhoan] INTEGER NOT NULL,
	[LoaiCapNhat] NVARCHAR(30) NOT NULL,
	[ThoiGian] DATETIME2 NOT NULL,
	[PhanTramTienDo] TINYINT NULL,
	[NoiDung] NVARCHAR(max) NOT NULL,
	[ViDo] NUMERIC(9, 6) NULL,
	[KinhDo] NUMERIC(9, 6) NULL,
	PRIMARY KEY ([MaCapNhat]),
	CONSTRAINT [CK_CapNhat_Loai] CHECK (LoaiCapNhat IN (N'Ghi nhận hiện trường', N'Tiến độ', N'Kết quả', N'Không có sự cố')),
	CONSTRAINT [CK_CapNhat_TienDo] CHECK (PhanTramTienDo IS NULL OR (PhanTramTienDo BETWEEN 0 AND 100)),
	FOREIGN KEY([MaPhanCong]) REFERENCES [PhanCongXuLy] ([MaPhanCong]),
	FOREIGN KEY([MaTaiKhoan]) REFERENCES [TaiKhoan] ([MaTaiKhoan])
);
GO

CREATE TABLE [LichSuTrangThai] (
	[MaLichSu] BIGINT NOT NULL IDENTITY,
	[MaBaoCao] INTEGER NOT NULL,
	[TrangThaiCu] NVARCHAR(30) NULL,
	[TrangThaiMoi] NVARCHAR(30) NOT NULL,
	[ThoiGian] DATETIME2 NOT NULL,
	[MaTaiKhoan] INTEGER NULL,
	[GhiChu] NVARCHAR(500) NULL,
	PRIMARY KEY ([MaLichSu]),
	FOREIGN KEY([MaBaoCao]) REFERENCES [BaoCaoSuCo] ([MaBaoCao]),
	FOREIGN KEY([MaTaiKhoan]) REFERENCES [TaiKhoan] ([MaTaiKhoan])
);
GO
CREATE INDEX [IX_LichSu_BaoCao_ThoiGian] ON [LichSuTrangThai] ([MaBaoCao], [ThoiGian]);
GO

CREATE TABLE [MinhChungBaoCao] (
	[MaMinhChung] INTEGER NOT NULL IDENTITY,
	[MaBaoCao] INTEGER NOT NULL,
	[MaYeuCau] INTEGER NULL,
	[TenTep] NVARCHAR(255) NOT NULL,
	[LoaiTep] VARCHAR(10) NOT NULL,
	[KichThuoc] BIGINT NOT NULL,
	[DuongDan] VARCHAR(500) NOT NULL,
	[NgayTaiLen] DATETIME2 NOT NULL,
	[DuocCongKhai] BIT NOT NULL DEFAULT 0,
	PRIMARY KEY ([MaMinhChung]),
	CONSTRAINT [CK_MinhChungBaoCao_LoaiTep] CHECK (LoaiTep IN (N'jpg', N'png', N'mp4')),
	CONSTRAINT [CK_MinhChungBaoCao_KichThuoc] CHECK (KichThuoc > 0),
	FOREIGN KEY([MaBaoCao]) REFERENCES [BaoCaoSuCo] ([MaBaoCao]),
	FOREIGN KEY([MaYeuCau]) REFERENCES [YeuCauBoSung] ([MaYeuCau])
);
GO

CREATE TABLE [NghiemThu] (
	[MaNghiemThu] INTEGER NOT NULL IDENTITY,
	[MaPhanCong] INTEGER NOT NULL,
	[MaCanBo] INTEGER NOT NULL,
	[ThoiGian] DATETIME2 NOT NULL,
	[KetQua] NVARCHAR(30) NOT NULL,
	[NhanXet] NVARCHAR(1000) NULL,
	PRIMARY KEY ([MaNghiemThu]),
	CONSTRAINT [CK_NghiemThu_KetQua] CHECK (KetQua IN (N'Đạt', N'Chưa đạt', N'Không có sự cố')),
	FOREIGN KEY([MaPhanCong]) REFERENCES [PhanCongXuLy] ([MaPhanCong]),
	FOREIGN KEY([MaCanBo]) REFERENCES [CanBoXuLy] ([MaCanBo])
);
GO

CREATE TABLE [MinhChungXuLy] (
	[MaMinhChung] INTEGER NOT NULL IDENTITY,
	[MaCapNhat] INTEGER NOT NULL,
	[GiaiDoan] NVARCHAR(10) NOT NULL,
	[TenTep] NVARCHAR(255) NOT NULL,
	[LoaiTep] VARCHAR(10) NOT NULL,
	[DuongDan] VARCHAR(500) NOT NULL,
	[NgayTaiLen] DATETIME2 NOT NULL,
	[DuocCongKhai] BIT NOT NULL DEFAULT 0,
	PRIMARY KEY ([MaMinhChung]),
	CONSTRAINT [CK_MinhChungXuLy_GiaiDoan] CHECK (GiaiDoan IN (N'Trước', N'Sau')),
	CONSTRAINT [CK_MinhChungXuLy_LoaiTep] CHECK (LoaiTep IN (N'jpg', N'png', N'mp4')),
	FOREIGN KEY([MaCapNhat]) REFERENCES [CapNhatXuLy] ([MaCapNhat])
);
GO
