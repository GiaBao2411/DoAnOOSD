// Bảng định tuyến: mỗi đường dẫn ứng với một màn hình (Form) của hệ thống
import { Route, Routes } from "react-router-dom";
import Khung, { TrangLoi, YeuCau } from "./thanh_phan/khung.jsx";
import { BoSung, GuiBaoCao, QuenMa, TraCuu, TrangChu } from "./trang/cong_khai.jsx";
import { DangNhap, DoiMatKhau, TrangChinh } from "./trang/xac_thuc.jsx";
import { KiemDuyet, NghiemThu, PhanCong, TiepNhan } from "./trang/can_bo.jsx";
import { ThietBiDo, TraCuuNoiBo } from "./trang/can_bo2.jsx";
import { DanhMuc, TaiKhoan } from "./trang/quan_ly.jsx";
import { CapNhat, NhiemVu } from "./trang/don_vi.jsx";

const CB = "Cán bộ";
const DV = "Đơn vị";

export default function App() {
  return (
    <Routes>
      <Route element={<Khung />}>
        {/* Người dân (không đăng nhập) */}
        <Route path="/" element={<TrangChu />} />
        <Route path="/gui-bao-cao" element={<GuiBaoCao />} />
        <Route path="/tra-cuu" element={<TraCuu />} />
        <Route path="/quen-ma" element={<QuenMa />} />
        <Route path="/bo-sung" element={<BoSung />} />
        {/* Đăng nhập, trang chính */}
        <Route path="/dang-nhap" element={<DangNhap />} />
        <Route path="/doi-mat-khau" element={<YeuCau><DoiMatKhau /></YeuCau>} />
        <Route path="/trang-chinh" element={<YeuCau><TrangChinh /></YeuCau>} />
        {/* Cán bộ xử lý */}
        <Route path="/can-bo/tiep-nhan" element={<YeuCau vaiTro={CB}><TiepNhan /></YeuCau>} />
        <Route path="/can-bo/phan-cong" element={<YeuCau vaiTro={CB}><PhanCong /></YeuCau>} />
        <Route path="/can-bo/nghiem-thu" element={<YeuCau vaiTro={CB}><NghiemThu /></YeuCau>} />
        <Route path="/can-bo/kiem-duyet" element={<YeuCau vaiTro={CB}><KiemDuyet /></YeuCau>} />
        <Route path="/can-bo/tram-quan-trac" element={<YeuCau vaiTro={CB}><ThietBiDo /></YeuCau>} />
        <Route path="/can-bo/tra-cuu" element={<YeuCau vaiTro={CB}><TraCuuNoiBo /></YeuCau>} />
        <Route path="/can-bo/danh-muc" element={<YeuCau vaiTro={CB}><DanhMuc /></YeuCau>} />
        <Route path="/can-bo/tai-khoan" element={<YeuCau vaiTro={CB}><TaiKhoan /></YeuCau>} />
        {/* Đơn vị xử lý hiện trường */}
        <Route path="/don-vi/nhiem-vu" element={<YeuCau vaiTro={DV}><NhiemVu /></YeuCau>} />
        <Route path="/don-vi/cap-nhat" element={<YeuCau vaiTro={DV}><CapNhat /></YeuCau>} />
        <Route path="*" element={<TrangLoi />} />
      </Route>
    </Routes>
  );
}
