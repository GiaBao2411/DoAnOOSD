import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { guiForm } from "../api.js";
import { dt, so0 } from "../dinh_dang.js";
import { BangLoc, Tag, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai, useUngDung } from "../ung_dung.jsx";

const TAB = [["loai", "Loại sự cố"], ["dia-ban", "Địa bàn"], ["don-vi", "Đơn vị xử lý"], ["tram", "Thiết bị đo"], ["tham-so", "Tham số hệ thống"]];

function useLuu() {
  const { xong, baoTaiCho } = useUngDung();
  return async (url, duLieu, urlXong, kem) => {
    try {
      const d = await guiForm(url, duLieu);
      xong(d.thong_bao, urlXong, "ok", kem ? kem(d) : undefined);
      return d;
    } catch (e) {
      baoTaiCho(e.message);
      return null;
    }
  };
}

export function DanhMuc() {
  const [q] = useSearchParams();
  const tab = q.get("tab") || "loai";
  const sua = q.get("sua") || "";
  const { state } = useLocation();
  const luu = useLuu();
  const t = useTai("/api/can-bo/danh-muc?tab=" + tab);
  const d = t.d && t.d.tab === tab ? t.d : null;
  const ds = d ? d.ds : [];
  const o = sua ? ds.find((x) => String(x.ma) === sua) : null;
  const uTab = "/can-bo/danh-muc?tab=" + tab;
  const dangDung = (x) => (x.dang_dung ? "Đang dùng" : "Ngừng dùng");
  const gui = (url, kem) => (e) => {
    e.preventDefault();
    luu(url, new FormData(e.target), uTab, kem);
  };
  const khoaKem = (r) => (r.khoa ? { khoa: r.khoa } : null);

  let bang = null;
  let form = null;
  if (d && tab === "loai") {
    bang = <BangLoc dau={<tr><th>Mã</th><th>Tên loại sự cố</th><th>Mô tả</th><th>Trạng thái</th><th></th></tr>}
      dong={ds.map((x) => ({ key: x.ma, sel: o && o.ma === x.ma, chu: [x.ma, x.ten, x.mo_ta, dangDung(x)].join(" "),
        el: <tr key={x.ma} className={o && o.ma === x.ma ? "sel" : ""}><td>{x.ma}</td><td>{x.ten}</td><td>{x.mo_ta || ""}</td>
          <td className="nw">{dangDung(x)}</td><td><Link to={"?tab=loai&sua=" + x.ma}>Sửa</Link></td></tr> }))} />;
    form = (
      <form key={sua} onSubmit={gui("/api/can-bo/danh-muc/loai")}><input type="hidden" name="ma" value={o ? o.ma : ""} />
        <label>Tên loại sự cố <span className="req">*</span></label><input type="text" name="ten" defaultValue={o ? o.ten : ""} required />
        <label>Mô tả</label><textarea name="mo_ta" defaultValue={o && o.mo_ta ? o.mo_ta : ""}></textarea>
        <label style={{ fontWeight: 400 }}><input type="checkbox" name="dang_dung" value="1" defaultChecked={!o || o.dang_dung} /> Đang sử dụng</label>
        <div className="actions"><button className="btn">Lưu</button><Link className="btn sec" to="?tab=loai">Thêm mới</Link></div></form>
    );
  } else if (d && tab === "dia-ban") {
    bang = <BangLoc dau={<tr><th>Mã</th><th>Phường/xã</th><th>Tỉnh/thành</th><th>Trạng thái</th><th></th></tr>}
      dong={ds.map((x) => ({ key: x.ma, sel: o && o.ma === x.ma, chu: [x.ma, x.ten, x.tinh, dangDung(x)].join(" "),
        el: <tr key={x.ma} className={o && o.ma === x.ma ? "sel" : ""}><td>{x.ma}</td><td>{x.ten}</td><td>{x.tinh}</td>
          <td className="nw">{dangDung(x)}</td><td><Link to={"?tab=dia-ban&sua=" + x.ma}>Sửa</Link></td></tr> }))} />;
    form = (
      <form key={sua} onSubmit={gui("/api/can-bo/danh-muc/dia-ban")}><input type="hidden" name="ma" value={o ? o.ma : ""} />
        <label>Tên phường/xã <span className="req">*</span></label><input type="text" name="ten" defaultValue={o ? o.ten : ""} required />
        <label>Tỉnh/thành phố <span className="req">*</span></label><input type="text" name="tinh" defaultValue={o ? o.tinh : "TP. Hồ Chí Minh"} required />
        <label style={{ fontWeight: 400 }}><input type="checkbox" name="dang_dung" value="1" defaultChecked={!o || o.dang_dung} /> Đang sử dụng</label>
        <div className="actions"><button className="btn">Lưu</button><Link className="btn sec" to="?tab=dia-ban">Thêm mới</Link></div></form>
    );
  } else if (d && tab === "don-vi") {
    bang = <BangLoc dau={<tr><th>Mã</th><th>Đơn vị</th><th>Địa bàn phụ trách</th><th>Điện thoại</th><th>Trạng thái</th><th></th></tr>}
      dong={ds.map((x) => ({ key: x.ma, sel: o && o.ma === x.ma, chu: [x.ma, x.ten, x.dia_ban, x.sdt, dangDung(x)].join(" "),
        el: <tr key={x.ma} className={o && o.ma === x.ma ? "sel" : ""}><td>{x.ma}</td><td>{x.ten}</td><td>{x.dia_ban}</td>
          <td className="nw">{x.sdt || "—"}</td><td className="nw">{dangDung(x)}</td><td><Link to={"?tab=don-vi&sua=" + x.ma}>Sửa</Link></td></tr> }))} />;
    form = (
      <form key={sua} onSubmit={gui("/api/can-bo/danh-muc/don-vi")}><input type="hidden" name="ma" value={o ? o.ma : ""} />
        <label>Tên đơn vị <span className="req">*</span></label><input type="text" name="ten" defaultValue={o ? o.ten : ""} required />
        <label>Địa bàn phụ trách chính (dùng để gợi ý khi giao việc)</label><select name="ma_dia_ban" defaultValue={o && o.ma_dia_ban ? o.ma_dia_ban : ""}>
          <option value="">— Không —</option>{d.ds_dia_ban.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}</select>
        <label>Địa chỉ</label><input type="text" name="dia_chi" defaultValue={o && o.dia_chi ? o.dia_chi : ""} />
        <label>Số điện thoại</label><input type="text" name="sdt" defaultValue={o && o.sdt ? o.sdt : ""} />
        <label style={{ fontWeight: 400 }}><input type="checkbox" name="dang_dung" value="1" defaultChecked={!o || o.dang_dung} /> Đang sử dụng</label>
        <div className="actions"><button className="btn">Lưu</button><Link className="btn sec" to="?tab=don-vi">Thêm mới</Link></div></form>
    );
  } else if (d && tab === "tram") {
    bang = (
      <>
        {state && state.khoa && (
          <div className="flash warn">Khóa của thiết bị <b>{state.khoa[0]}</b>: <code style={{ fontSize: 15 }}>{state.khoa[1]}</code><br />
            Chỉ hiển thị một lần. Chép vào dòng <code>KHOA_TRAM = "..."</code> trong main.py của mạch Pico (hoặc tệp giả lập thiết bị).</div>
        )}
        <BangLoc dau={<tr><th>Thiết bị</th><th className="num">Ngưỡng KK / TDS</th><th className="num">Lần gửi cuối</th><th>Trạng thái</th><th></th></tr>}
          dong={ds.map((x) => ({ key: x.ma, sel: o && o.ma === x.ma, chu: [x.ma_thiet_bi, x.ten, x.dia_ban, dangDung(x)].join(" "),
            el: <tr key={x.ma} className={o && o.ma === x.ma ? "sel" : ""}><td><b>{x.ma_thiet_bi}</b><span className="cell-sub">{x.ten}, {x.dia_ban}</span></td>
              <td className="num">{so0(x.nguong_kk)} / {so0(x.nguong_tds)}</td><td className="num">{dt(x.lan_gui_cuoi)}</td>
              <td className="nw">{dangDung(x)}</td><td><Link to={"?tab=tram&sua=" + x.ma}>Sửa</Link></td></tr> }))} />
      </>
    );
    form = (
      <>
        <form key={sua} onSubmit={gui("/api/can-bo/danh-muc/tram", khoaKem)}><input type="hidden" name="ma" value={o ? o.ma : ""} />
          <div className="row"><div><label>Mã thiết bị <span className="req">*</span></label><input type="text" name="ma_thiet_bi" defaultValue={o ? o.ma_thiet_bi : ""} required /></div>
            <div><label>Tên thiết bị <span className="req">*</span></label><input type="text" name="ten" defaultValue={o ? o.ten : ""} required /></div></div>
          <label>Phường/xã đặt thiết bị <span className="req">*</span></label><select name="ma_dia_ban" required defaultValue={o ? o.ma_dia_ban : undefined}>
            {d.ds_dia_ban.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}</select>
          <div className="row"><div><label>Vĩ độ</label><input type="text" name="vi_do" defaultValue={o && o.vi_do !== null ? o.vi_do : ""} /></div>
            <div><label>Kinh độ</label><input type="text" name="kinh_do" defaultValue={o && o.kinh_do !== null ? o.kinh_do : ""} /></div></div>
          <div className="row"><div><label>Ngưỡng không khí (ppm) <span className="req">*</span></label><input type="number" step="0.1" name="nguong_kk" defaultValue={o ? o.nguong_kk : d.nguong_mac_dinh} required /></div>
            <div><label>Ngưỡng TDS (ppm) <span className="req">*</span></label><input type="number" step="0.1" name="nguong_tds" defaultValue={o ? o.nguong_tds : d.nguong_mac_dinh} required /></div></div>
          <label style={{ fontWeight: 400 }}><input type="checkbox" name="dang_dung" value="1" defaultChecked={!o || o.dang_dung} /> Đang sử dụng (bỏ chọn thì thiết bị bị từ chối khi gửi)</label>
          <div className="actions"><button className="btn">Lưu</button><Link className="btn sec" to="?tab=tram">Thêm mới</Link></div></form>
        {o && (
          <form style={{ marginTop: 10 }} onSubmit={(e) => {
            e.preventDefault();
            if (window.confirm("Cấp khóa mới? Mạch đang dùng khóa cũ sẽ bị từ chối cho tới khi nạp khóa mới."))
              luu("/api/can-bo/danh-muc/tram/" + o.ma + "/cap-khoa", {}, "/can-bo/danh-muc?tab=tram&sua=" + o.ma, khoaKem);
          }}><button className="btn orange">Cấp khóa mới cho thiết bị</button></form>
        )}
      </>
    );
  } else if (d) {
    bang = <BangLoc dau={<tr><th>Mã tham số</th><th>Giá trị</th><th>Ý nghĩa</th><th>Cập nhật lần cuối</th><th></th></tr>}
      dong={ds.map((x) => ({ key: x.ma, sel: o && o.ma === x.ma, chu: [x.ma, x.gia_tri, x.mo_ta].join(" "),
        el: <tr key={x.ma} className={o && o.ma === x.ma ? "sel" : ""}><td>{x.ma}</td><td><b>{x.gia_tri}</b></td><td>{x.mo_ta}</td>
          <td className="small">{dt(x.ngay)}{x.can_bo ? " · " + x.can_bo : ""}</td><td><Link to={"?tab=tham-so&sua=" + x.ma}>Sửa</Link></td></tr> }))} />;
    form = o ? (
      <form key={sua} onSubmit={gui("/api/can-bo/danh-muc/tham-so")}><input type="hidden" name="ma" value={o.ma} />
        <p><b>{o.ma}</b><br /><span className="small muted">{o.mo_ta}</span></p>
        <label>Giá trị (số nguyên dương) <span className="req">*</span></label><input type="number" min="1" name="gia_tri" defaultValue={o.gia_tri} required />
        <div className="actions"><button className="btn">Lưu</button></div></form>
    ) : null;
  }

  return (
    <>
      <TieuDe>Quản lý danh mục</TieuDe>
      <h1>Quản lý danh mục</h1>
      <div className="tabs">{TAB.map(([k, v]) => <Link key={k} to={"?tab=" + k} className={tab === k ? "on" : ""}>{v}</Link>)}</div>
      <div className="grid" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        <div>{bang}</div>
        <div className="card"><div className="hd">{o ? "Sửa" : "Thêm mới"}</div><div className="bd">{form}</div></div>
      </div>
    </>
  );
}

export function TaiKhoan() {
  const [q, datQ] = useSearchParams();
  const tim = q.get("q") || "";
  const sua = +(q.get("sua") || 0);
  const { state } = useLocation();
  const navigate = useNavigate();
  const luu = useLuu();
  const t = useTai("/api/can-bo/tai-khoan?q=" + encodeURIComponent(tim));
  const d = t.d;
  const o = d && sua ? d.ds.find((x) => x.ma === sua) : null;
  const mkKem = (r) => (r.mat_khau_tam ? { mat_khau_tam: r.mat_khau_tam } : null);
  return (
    <>
      <TieuDe>Tài khoản đơn vị xử lý</TieuDe>
      <h1>Tài khoản đơn vị xử lý</h1>
      {state && state.mat_khau_tam && (
        <div className="flash warn">Mật khẩu tạm của <b>{state.mat_khau_tam[0]}</b>: <span className="big-code" style={{ fontSize: 15 }}>{state.mat_khau_tam[1]}</span>
          {" "}— chỉ hiển thị một lần; đơn vị phải đổi ở lần đăng nhập đầu.</div>
      )}
      <div className="grid" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
        <div>
          <form className="row" key={tim} onSubmit={(e) => { e.preventDefault(); datQ({ q: new FormData(e.target).get("q") }); }}>
            <div><label>Tìm theo tên đăng nhập</label><input type="text" name="q" defaultValue={tim} /></div>
            <div style={{ flex: 0 }}><button className="btn">Lọc</button></div></form>
          {d && (
            <BangLoc style={{ marginTop: 10 }} rong="Chưa có tài khoản đơn vị."
              dau={<tr><th>Tên đăng nhập</th><th>Đơn vị xử lý</th><th>Trạng thái</th><th>Đăng nhập cuối</th></tr>}
              dong={d.ds.map((x) => ({
                key: x.ma, sel: sua === x.ma, chu: [x.ten_dang_nhap, x.don_vi, x.trang_thai].join(" "),
                el: (<tr key={x.ma} className={"click " + (sua === x.ma ? "sel" : "")} onClick={() => navigate("?sua=" + x.ma)}>
                  <td>{x.ten_dang_nhap}</td><td>{x.don_vi}</td><td><Tag s={x.trang_thai} /></td><td className="small">{dt(x.lan_dang_nhap_cuoi)}</td></tr>),
              }))}
            />
          )}
        </div>
        <div>
          {o ? (
            <div className="card"><div className="hd">Tài khoản {o.ten_dang_nhap} <Tag s={o.trang_thai} /></div><div className="bd">
              <p>Tài khoản của đơn vị <b>{o.don_vi}</b>.</p>
              <div className="actions">
                <form onSubmit={(e) => { e.preventDefault(); luu("/api/can-bo/tai-khoan/" + o.ma + "/khoa", {}, "/can-bo/tai-khoan?sua=" + o.ma); }}>
                  <button className="btn red">{o.trang_thai === "Hoạt động" ? "Khóa" : "Mở khóa"}</button></form>
                <form onSubmit={(e) => { e.preventDefault(); luu("/api/can-bo/tai-khoan/" + o.ma + "/dat-lai", {}, "/can-bo/tai-khoan?sua=" + o.ma, mkKem); }}>
                  <button className="btn orange">Đặt lại mật khẩu</button></form>
                <Link className="btn sec" to="/can-bo/tai-khoan">Thêm tài khoản mới</Link>
              </div>
            </div></div>
          ) : (
            <div className="card"><div className="hd">Cấp tài khoản cho đơn vị</div><div className="bd">
              <form onSubmit={(e) => { e.preventDefault(); luu("/api/can-bo/tai-khoan/them", new FormData(e.target), "/can-bo/tai-khoan", mkKem); }}>
                <label>Đơn vị xử lý <span className="req">*</span></label><select name="ma_don_vi" required defaultValue="">
                  <option value="">— Chọn —</option>{d && d.ds_don_vi.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}</select>
                <label>Tên đăng nhập <span className="req">*</span></label><input type="text" name="ten" required />
                <div className="actions"><button className="btn">Cấp tài khoản</button></div>
              </form>
            </div></div>
          )}
        </div>
      </div>
    </>
  );
}
