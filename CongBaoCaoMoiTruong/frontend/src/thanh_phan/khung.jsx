import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { guiForm, layDuLieu } from "../api.js";
import { useUngDung } from "../ung_dung.jsx";
import { Flash } from "./chung.jsx";

const LOGO = (
  <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
    <path d="M14 2.5C9.6 8.4 6.5 12.6 6.5 16.6a7.5 7.5 0 0 0 15 0c0-4-3.1-8.2-7.5-14.1Z" fill="#fff" />
    <path d="M8.2 17.8c1.9-1.4 3.8-1.4 5.8 0s3.9 1.4 5.8 0" fill="none" stroke="#0e5e63" strokeWidth="2" strokeLinecap="round" />
    <circle cx="21.5" cy="7" r="3.2" fill="#e8a317" />
  </svg>
);

const TU_LAM_MOI = ["/trang-chinh", "/can-bo/tiep-nhan", "/can-bo/phan-cong", "/can-bo/nghiem-thu", "/can-bo/kiem-duyet", "/don-vi/nhiem-vu"];

const MENU_CAN_BO = [
  ["/trang-chinh", "Trang chính"], ["/can-bo/tiep-nhan", "Tiếp nhận báo cáo", "moi"], ["/can-bo/phan-cong", "Phân công xử lý", "phan_cong"],
  ["/can-bo/nghiem-thu", "Duyệt kết quả", "nghiem_thu"], ["/can-bo/kiem-duyet", "Kiểm duyệt, công khai", "cong_khai"],
  ["/can-bo/tram-quan-trac", "Thiết bị đo (IoT)"], ["/can-bo/tra-cuu", "Tra cứu báo cáo"],
];

function MucMenu({ to, ten, dem }) {
  const { pathname } = useLocation();
  return (
    <Link to={to} className={pathname === to ? "on" : ""}>
      {ten}
      {dem ? <span className="dem">{dem}</span> : null}
    </Link>
  );
}

function useTheoDoiThayDoi(bat) {
  const { lamMoiTrang } = useUngDung();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [dem, datDem] = useState({});
  const [baoMoi, datBaoMoi] = useState(null);
  const st = useRef({ dau: null, nt: null, dangNhap: false, path: pathname });
  st.current.path = pathname;

  useEffect(() => {
    st.current.dangNhap = false;
  }, [pathname]);

  useEffect(() => {
    if (!bat) return;
    const go = (e) => {
      if (e.target.closest && e.target.closest("form")) st.current.dangNhap = true;
    };
    document.addEventListener("input", go);
    document.addEventListener("change", go);
    let hen = null;
    let dung = false;
    async function hoi() {
      try {
        const d = await layDuLieu("/api/trang-thai-moi");
        datDem(d.dem || {});
        const nt = (d.dem || {}).nghiem_thu;
        const s = st.current;
        if (s.dau !== null && d.dau !== s.dau) {
          const coKetQuaMoi = nt !== undefined && nt > s.nt;
          if (TU_LAM_MOI.includes(s.path) && !s.dangNhap) lamMoiTrang();
          else if (coKetQuaMoi)
            datBaoMoi({ nd: "Đơn vị vừa gửi kết quả mới: " + nt + " kết quả đang chờ duyệt.", link: s.path === "/can-bo/nghiem-thu" ? null : "/can-bo/nghiem-thu" });
          else datBaoMoi({ nd: "Có cập nhật mới. Tải lại để xem.", link: null });
        }
        s.dau = d.dau;
        s.nt = nt;
      } catch {
      }
    }
    function lap() {
      clearTimeout(hen);
      hen = setTimeout(async () => {
        if (!document.hidden) await hoi();
        if (!dung) lap();
      }, 8000);
    }
    const hien = () => {
      if (!document.hidden) {
        hoi();
        lap();
      }
    };
    document.addEventListener("visibilitychange", hien);
    hoi();
    lap();
    return () => {
      dung = true;
      clearTimeout(hen);
      document.removeEventListener("input", go);
      document.removeEventListener("change", go);
      document.removeEventListener("visibilitychange", hien);
    };
  }, [bat, lamMoiTrang]);

  const theBaoMoi = baoMoi && (
    <div id="bao-moi" role="status">
      <span>{baoMoi.nd}</span>
      <a className="btn sm" href={baoMoi.link || "#"} onClick={(e) => {
        e.preventDefault();
        datBaoMoi(null);
        if (baoMoi.link) navigate(baoMoi.link);
        else lamMoiTrang();
      }}>{baoMoi.link ? "Mở trang duyệt" : "Tải lại trang"}</a>
      <button type="button" className="btn sec sm" onClick={() => datBaoMoi(null)}>Đóng</button>
    </div>
  );
  return { dem, theBaoMoi };
}

export default function Khung() {
  const { taiKhoan, datTaiKhoan, daTai, xong } = useUngDung();
  const { pathname } = useLocation();
  const noiBo = !!(taiKhoan && !taiKhoan.phai_doi_mat_khau);
  const laCanBo = taiKhoan && taiKhoan.loai === "Cán bộ";
  const { dem, theBaoMoi } = useTheoDoiThayDoi(noiBo);

  useEffect(() => {
    document.body.scrollTop = 0;
  }, [pathname]);

  async function dangXuat() {
    await guiForm("/api/dang-xuat", {}).catch(() => {});
    datTaiKhoan(null);
    xong("Đã đăng xuất.", "/");
  }

  if (daTai && taiKhoan && taiKhoan.phai_doi_mat_khau && pathname !== "/doi-mat-khau") return <Navigate to="/doi-mat-khau" replace />;

  const dauTrang = (
    <header className="top">
      <Link className="brand" to={taiKhoan ? "/trang-chinh" : "/"}>
        {LOGO}
        <span>Cổng báo cáo sự cố môi trường</span>
      </Link>
      <nav>
        {taiKhoan ? (
          <>
            <span className="who">{laCanBo ? "Cán bộ" : "Đơn vị"}: <b>{taiKhoan.ten_hien_thi}</b></span>
            <Link to="/trang-chinh">Trang chính</Link>
            <Link to="/doi-mat-khau">Đổi mật khẩu</Link>
            <form className="inline" onSubmit={(e) => { e.preventDefault(); dangXuat(); }}><button>Đăng xuất</button></form>
          </>
        ) : (
          <>
            {[["/", "Trang chủ"], ["/gui-bao-cao", "Gửi báo cáo"], ["/tra-cuu", "Tra cứu"], ["/bo-sung", "Bổ sung thông tin"]].map(([u, t]) => (
              <NavLink key={u} to={u} end className={({ isActive }) => (isActive ? "on" : "")}>{t}</NavLink>
            ))}
            <Link to="/dang-nhap" className="dn">Đăng nhập cán bộ</Link>
          </>
        )}
      </nav>
    </header>
  );

  const chanTrang = (
    <footer className="chan">
      <div className="chan-trong">
        <div className="chan-tg">
          <svg width="30" height="30" viewBox="0 0 28 28" aria-hidden="true">
            <path d="M14 2.5C9.6 8.4 6.5 12.6 6.5 16.6a7.5 7.5 0 0 0 15 0c0-4-3.1-8.2-7.5-14.1Z" fill="#fff" />
            <path d="M8.2 17.8c1.9-1.4 3.8-1.4 5.8 0s3.9 1.4 5.8 0" fill="none" stroke="#1f5753" strokeWidth="2" strokeLinecap="round" />
            <circle cx="21.5" cy="7" r="3.2" fill="#e9b949" />
          </svg>
          <div><b>Đồ án môn học</b><span>Huỳnh Gia Bảo · MSSV 1250080014 · Lớp 12_CNPM1</span></div>
        </div>
      </div>
      <div className="chan-duoi">
        <span>Trường Đại học Tài nguyên và Môi trường TP.HCM · {new Date().getFullYear()}</span>
      </div>
    </footer>
  );

  if (!noiBo) {
    return (
      <>
        {dauTrang}
        <main className="wide"><Flash /><Outlet /></main>
        {chanTrang}
      </>
    );
  }
  return (
    <>
      {dauTrang}
      <div className="layout">
        <aside className="menu">
          {laCanBo ? (
            <>
              <h4>Xử lý báo cáo</h4>
              {MENU_CAN_BO.map(([u, t, k]) => <MucMenu key={u} to={u} ten={t} dem={k ? dem[k] : 0} />)}
              <h4>Quản lý hệ thống</h4>
              <MucMenu to="/can-bo/danh-muc" ten="Danh mục" />
              <MucMenu to="/can-bo/tai-khoan" ten="Tài khoản đơn vị" />
            </>
          ) : (
            <>
              <h4>Đơn vị xử lý</h4>
              <MucMenu to="/trang-chinh" ten="Trang chính" />
              <MucMenu to="/don-vi/nhiem-vu" ten="Nhiệm vụ được giao" dem={dem.cho_nhan} />
              <MucMenu to="/don-vi/cap-nhat" ten="Cập nhật tiến độ" />
            </>
          )}
          <h4>Công khai</h4>
          <a href="/" target="_blank" rel="noreferrer">Xem trang người dân</a>
        </aside>
        <main><Flash /><Outlet /></main>
      </div>
      {chanTrang}
      {theBaoMoi}
    </>
  );
}

export function YeuCau({ vaiTro, children }) {
  const { taiKhoan, daTai } = useUngDung();
  const { pathname, search } = useLocation();
  if (!daTai) return null;
  if (!taiKhoan) return <Navigate to={"/dang-nhap?tiep=" + encodeURIComponent(pathname + search)} replace />;
  if (vaiTro && taiKhoan.loai !== vaiTro) return <TrangLoi tieuDe="Không đủ quyền" noiDung="Tài khoản của bạn không được phép dùng chức năng này." />;
  return children;
}

export function TrangLoi({ tieuDe = "Không tìm thấy trang", noiDung = "Địa chỉ bạn mở không tồn tại." }) {
  document.title = tieuDe;
  return (
    <div className="card" style={{ maxWidth: 560, margin: "40px auto" }}>
      <div className="hd">{tieuDe}</div>
      <div className="bd">
        <p>{noiDung}</p>
        <div className="actions"><Link className="btn" to="/">Về trang chủ</Link><Link className="btn sec" to="/trang-chinh">Trang chính</Link></div>
      </div>
    </div>
  );
}
