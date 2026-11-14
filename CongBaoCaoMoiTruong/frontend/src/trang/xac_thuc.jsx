// FormDangNhap, đổi mật khẩu, FormMain (trang chính theo vai trò)
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { guiForm } from "../api.js";
import { dt, so0, thuNgay } from "../dinh_dang.js";
import { BangLoc, Tag, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai, useUngDung } from "../ung_dung.jsx";

export function DangNhap() {
  const { taiKhoan, datTaiKhoan, daTai, xong } = useUngDung();
  const [q] = useSearchParams();
  const navigate = useNavigate();
  const [loi, datLoi] = useState(null);
  const tiep = q.get("tiep") || "";
  if (daTai && taiKhoan && !taiKhoan.phai_doi_mat_khau) return <Navigate to="/trang-chinh" replace />;
  async function gui(e) {
    e.preventDefault();
    try {
      const d = await guiForm("/api/dang-nhap", new FormData(e.target));
      datTaiKhoan(d.tai_khoan);
      if (d.tai_khoan.phai_doi_mat_khau) {
        xong("Đây là lần đăng nhập đầu hoặc mật khẩu vừa được đặt lại. Vui lòng đổi mật khẩu.", "/doi-mat-khau", "warn");
        return;
      }
      navigate(tiep.startsWith("/") && !tiep.startsWith("//") ? tiep : "/trang-chinh", { replace: true });
    } catch (x) {
      datLoi(x.message);
    }
  }
  return (
    <>
      <TieuDe>Đăng nhập nội bộ</TieuDe>
      {loi && <div className="flash err">{loi}</div>}
      <div className="card" style={{ maxWidth: 420, margin: "30px auto" }}><div className="hd">Đăng nhập nội bộ (cán bộ, đơn vị xử lý)</div><div className="bd">
        <form onSubmit={gui}>
          <label>Tên đăng nhập <span className="req">*</span></label><input type="text" name="ten" required autoFocus />
          <label>Mật khẩu <span className="req">*</span></label><input type="password" name="mat_khau" required />
          <div className="actions"><button className="btn" style={{ width: "100%" }}>Đăng nhập</button></div>
        </form>
      </div></div>
    </>
  );
}

export function DoiMatKhau() {
  const { taiKhoan, datTaiKhoan, xong, baoTaiCho } = useUngDung();
  async function gui(e) {
    e.preventDefault();
    try {
      const d = await guiForm("/api/doi-mat-khau", new FormData(e.target));
      datTaiKhoan(d.tai_khoan);
      xong(d.thong_bao, "/trang-chinh");
    } catch (x) {
      baoTaiCho(x.message);
      e.target.reset();
    }
  }
  return (
    <>
      <TieuDe>Đổi mật khẩu</TieuDe>
      <div className="card" style={{ maxWidth: 420, margin: "30px auto" }}><div className="hd">Đổi mật khẩu — {taiKhoan.ten_dang_nhap}</div><div className="bd">
        <form onSubmit={gui}>
          <label>Mật khẩu hiện tại <span className="req">*</span></label><input type="password" name="cu" required />
          <label>Mật khẩu mới <span className="req">*</span></label><input type="password" name="moi" required minLength={8} />
          <label>Nhập lại mật khẩu mới <span className="req">*</span></label><input type="password" name="nhap_lai" required />
          <div className="actions"><button className="btn">Đổi mật khẩu</button></div>
        </form>
      </div></div>
    </>
  );
}

export function TrangChinh() {
  const t = useTai("/api/trang-chinh");
  if (!t.d) return t.loi ? <div className="flash err">{t.loi.message}</div> : null;
  return t.d.vai_tro === "don_vi" ? <TrangChinhDonVi d={t.d} /> : <TrangChinhCanBo d={t.d} />;
}

function DongChay({ ds, lop = "" }) {
  return (
    <ol className={"dong-chay " + lop}>
      {ds.map(([buoc, n, moTa, url, cuaToi], i) => (
        <li key={buoc} className={cuaToi && n ? "can-lam" : ""}><Link to={url}>
          <span className="buoc">{i + 1}. {buoc}</span>
          <span className="so">{n}</span>
          <span className="mt">{moTa}</span></Link></li>
      ))}
    </ol>
  );
}

function TrangChinhCanBo({ d }) {
  const { cauHinh } = useUngDung();
  const so = d.so;
  const chuY = [
    [so.nghiem_thu, "kết quả đơn vị đã gửi, chờ cán bộ duyệt", "/can-bo/nghiem-thu", "lam"],
    [so.qua_han_bs, "báo cáo quá hạn bổ sung thông tin", "/can-bo/tiep-nhan?tab=qua-han", "cam"],
    [so.bo_sung, "báo cáo người dân vừa bổ sung", "/can-bo/tiep-nhan?tab=da-bo-sung", "lam"],
    [so.tram_vuot, "thiết bị đo đang vượt ngưỡng", "/can-bo/tram-quan-trac", "do"],
    [so.tram_mat, "thiết bị đo mất kết nối", "/can-bo/tram-quan-trac", "cam"],
  ].filter((x) => x[0]);
  return (
    <>
      <TieuDe>Trang chính — Cán bộ</TieuDe>
      <div className="db-dau">
        <h1>Tổng quan công việc</h1>
        <p className="db-ngay">{thuNgay(d.bay_gio)}</p>
      </div>
      {/* Dải 5 bước: báo cáo đi qua đúng các bước này. Bước cán bộ phải làm mà đang có việc thì tô màu. */}
      <h2 className="db-h">Báo cáo đang ở bước nào</h2>
      <DongChay ds={[
        ["Tiếp nhận", so.moi, "báo cáo mới gửi", "/can-bo/tiep-nhan", true],
        ["Phân công", so.phan_cong, "chờ giao đơn vị", "/can-bo/phan-cong", true],
        ["Đơn vị xử lý", so.dang_xl, "đang ở hiện trường", "/can-bo/tra-cuu?trang_thai=" + (cauHinh ? cauHinh.loc_o_don_vi : "o-don-vi"), false],
        ["Duyệt kết quả", so.nghiem_thu, "chờ cán bộ duyệt kết quả", "/can-bo/nghiem-thu", true],
        ["Công khai", so.cong_khai, "chờ kiểm duyệt", "/can-bo/kiem-duyet", true],
      ]} />

      <h2 className="db-h">Cần chú ý</h2>
      <ul className="chu-y">
        {chuY.map(([n, nd, url, mau]) => (
          <li key={nd} className={"m-" + mau}><Link to={url}><b>{n}</b><span>{nd}</span><span className="xem">Xem</span></Link></li>
        ))}
        {chuY.length === 0 && <li className="m-ok"><span>Không có cảnh báo nào. Các thiết bị đo hoạt động bình thường.</span></li>}
      </ul>

      <div className="grid db-hai">
        <section>
          <h2 className="db-h">Việc cần làm</h2>
          {d.viec.length ? (
            <BangLoc
              dau={<tr><th>Mã báo cáo</th><th>Việc</th><th>Phường/xã / Đơn vị</th><th className="num">Thời điểm</th></tr>}
              dong={d.viec.map((v, i) => ({
                key: i, chu: [v.ma_tra_cuu, v.viec, v.noi, dt(v.luc)].join(" "),
                el: (<tr key={i}><td><Link to={v.url}><b>{v.ma_tra_cuu}</b></Link></td>
                  <td className="nw">{v.viec}</td><td>{v.noi}</td><td className="num">{dt(v.luc)}</td></tr>),
              }))}
            />
          ) : <div className="card empty">Không có việc nào đang chờ.</div>}
        </section>
        <section>
          <h2 className="db-h">Thiết bị đo</h2>
          <div className="tram-ds">
            {d.tram.map((x) => (
              <Link key={x.tram.ma} className="tram-dong" to={"/can-bo/tram-quan-trac?tram=" + x.tram.ma}>
                <span className="tram-ten"><b>{x.tram.ma_thiet_bi}</b> {x.tram.ten}</span>
                {x.mat_ket_noi ? <span className="tag s-bs">Mất kết nối</span>
                  : x.moi && x.moi.vuot ? <span className="tag s-no">Vượt ngưỡng</span>
                  : <span className="tag s-ok">Đang gửi</span>}
                <span className="tram-so">{x.moi ? "Không khí " + so0(x.moi.kk) + " ppm, nước " + so0(x.moi.tds) + " ppm" : "Chưa có số liệu"}</span>
              </Link>
            ))}
            {d.tram.length === 0 && <div className="empty">Chưa có thiết bị nào đang dùng.</div>}
          </div>
        </section>
      </div>
    </>
  );
}

function TrangChinhDonVi({ d }) {
  const dem = d.dem;
  return (
    <>
      <TieuDe>Trang chính — Đơn vị</TieuDe>
      <div className="db-dau">
        <h1>Tổng quan nhiệm vụ của đơn vị</h1>
        <p className="db-ngay">{thuNgay(d.bay_gio)}</p>
      </div>
      <h2 className="db-h">Nhiệm vụ đang ở bước nào</h2>
      <DongChay lop="b3" ds={[
        ["Chờ tiếp nhận", dem.cho_tiep_nhan, "cần nhận hoặc trả lại", "/don-vi/nhiem-vu", true],
        ["Đang xử lý", dem.dang_xu_ly, "cập nhật tiến độ, gửi kết quả", "/don-vi/nhiem-vu", true],
        ["Chờ duyệt kết quả", dem.cho_duyet, "cán bộ đang xem kết quả", "/don-vi/nhiem-vu", false],
      ]} />
      <h2 className="db-h">Cần chú ý</h2>
      <ul className="chu-y">
        {dem.cho_tiep_nhan ? (
          <li className="m-lam"><Link to="/don-vi/nhiem-vu"><b>{dem.cho_tiep_nhan}</b><span>nhiệm vụ mới được giao, cần tiếp nhận</span><span className="xem">Xem</span></Link></li>
        ) : <li className="m-ok"><span>Không có nhiệm vụ mới cần tiếp nhận.</span></li>}
      </ul>
      <h2 className="db-h">Nhiệm vụ đang thực hiện</h2>
      {d.ds.length ? (
        <BangLoc
          dau={<tr><th>Mã PC</th><th>Báo cáo</th><th>Phường/xã</th><th>Ưu tiên</th><th>Giao lúc</th><th>Trạng thái</th></tr>}
          dong={d.ds.map((p) => ({
            key: p.ma, chu: ["PC-" + p.ma, p.ma_tra_cuu, p.dia_ban, p.uu_tien, dt(p.ngay), p.trang_thai].join(" "),
            el: (<tr key={p.ma}><td><Link to={"/don-vi/nhiem-vu?pc=" + p.ma}><b>PC-{p.ma}</b></Link></td><td>{p.ma_tra_cuu}</td>
              <td>{p.dia_ban}</td><td>{p.uu_tien}</td><td>{dt(p.ngay)}</td><td><Tag s={p.trang_thai} /></td></tr>),
          }))}
        />
      ) : <div className="card empty">Đơn vị chưa có nhiệm vụ nào.</div>}
    </>
  );
}
