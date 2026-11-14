// Trang của đơn vị xử lý hiện trường: FormNhiemVuHienTruong (UC11), FormCapNhatXuLy (UC12)
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { duLieuForm } from "../api.js";
import { dt } from "../dinh_dang.js";
import { BanDoDiem, layViTri } from "../thanh_phan/ban_do.jsx";
import { BcInfo, CapNhatList, ChonTep, Media, Pager, Tag, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai } from "../ung_dung.jsx";
import { useThaoTac } from "./can_bo.jsx";

export function NhiemVu() {
  const [q] = useSearchParams();
  const navigate = useNavigate();
  const tatCa = +(q.get("tat_ca") || 0);
  const trang = q.get("trang") || 1;
  const pcChon = +(q.get("pc") || 0);
  const thaoTac = useThaoTac();
  const [xem, datXem] = useState([]);
  const [viTri, datViTri] = useState({ lat: "", lng: "", gc: "" });
  const t = useTai("/api/don-vi/nhiem-vu?tat_ca=" + tatCa + "&trang=" + trang);
  const d = t.d;
  const maChon = pcChon || (d && d.ds.items.length ? d.ds.items[0].ma : 0);
  const ct = useTai(maChon ? "/api/don-vi/nhiem-vu/" + maChon : null);
  if (pcChon && ct.loi && ct.loi.maHttp === 400) return <BaoLoiChuyen loi={ct.loi.message} />;
  const pc = ct.d && ct.d.ma === maChon ? ct.d : null;
  const bc = pc && pc.bao_cao;
  const uPc = (ma) => "/don-vi/nhiem-vu?pc=" + ma;
  return (
    <>
      <TieuDe>Nhiệm vụ được giao</TieuDe>
      <h1>Nhiệm vụ được giao cho đơn vị</h1>
      <div className="tabs"><Link to="?" className={!tatCa ? "on" : ""}>Đang thực hiện</Link><Link to="?tat_ca=1" className={tatCa ? "on" : ""}>Tất cả</Link></div>
      {d && (d.ds.items.length ? (
        <>
          <table className="t"><tbody>
            <tr><th>Mã PC</th><th>Báo cáo</th><th>Phường/xã</th><th>Ưu tiên</th><th>Giao lúc</th><th>Trạng thái</th></tr>
            {d.ds.items.map((p) => (
              <tr key={p.ma} className={"click " + (pc && pc.ma === p.ma ? "sel" : "")} onClick={() => navigate("?pc=" + p.ma + "&tat_ca=" + tatCa)}>
                <td>PC-{p.ma}</td><td>{p.ma_tra_cuu}</td><td>{p.dia_ban}</td><td>{p.uu_tien}</td><td>{dt(p.ngay)}</td><td><Tag s={p.trang_thai} /></td>
              </tr>
            ))}
          </tbody></table>
          <Pager ds={d.ds} coSo={"?tat_ca=" + tatCa} />
        </>
      ) : <div className="card empty">Không có nhiệm vụ.</div>)}

      {pc && (
        <>
          <div className="grid g2" style={{ marginTop: 16 }}>
            <div className="card"><div className="hd">Chi tiết nhiệm vụ PC-{pc.ma} <Tag s={pc.trang_thai} /></div><div className="bd">
              <p><b>Nhiệm vụ:</b> {pc.noi_dung}<br /><span className="small">Giao lúc {dt(pc.ngay)}</span></p>
              <BcInfo bc={bc} />
              <div className="gallery" style={{ marginTop: 8 }}>{bc.minh_chung.map((m) => <Media key={m.ma} m={m} nhan="Người dân gửi" />)}</div>
            </div></div>
            <div className="card"><div className="hd">Vị trí sự cố{" "}
              {bc.vi_do !== null && <a className="btn sec sm" target="_blank" rel="noreferrer" href={"https://www.google.com/maps/dir/?api=1&destination=" + bc.vi_do + "," + bc.kinh_do}>Chỉ đường</a>}</div>
              <div className="bd"><BanDoDiem lat={bc.vi_do} lng={bc.kinh_do} className="map" /></div></div>
          </div>

          {pc.trang_thai === "Chờ tiếp nhận" && (
            <div className="card"><div className="hd">Nhận hoặc trả lại nhiệm vụ</div><div className="bd">
              <div className="row">
                <form style={{ flex: 0 }} onSubmit={(e) => { e.preventDefault(); thaoTac("/api/don-vi/nhiem-vu/" + pc.ma + "/nhan", {}, uPc(pc.ma)); }}>
                  <button className="btn">Nhận nhiệm vụ</button></form>
                <form className="row" style={{ flex: 3 }} onSubmit={(e) => { e.preventDefault(); thaoTac("/api/don-vi/nhiem-vu/" + pc.ma + "/tra-lai", new FormData(e.target), "/don-vi/nhiem-vu"); }}>
                  <div><label htmlFor="ly_do">Lý do trả lại (bắt buộc khi trả lại)</label><input type="text" id="ly_do" name="ly_do" /></div>
                  <div style={{ flex: 0 }}><button className="btn red">Trả lại</button></div></form>
              </div>
            </div></div>
          )}
          {pc.trang_thai === "Đang xử lý" && (
            <div className="card"><div className="hd">Ghi nhận tại hiện trường <Link className="btn sec sm" to={"/don-vi/cap-nhat?pc=" + pc.ma}>Mở cập nhật tiến độ / gửi kết quả</Link></div><div className="bd">
              <form key={pc.ma + "-" + pc.cap_nhat.length} onSubmit={async (e) => {
                e.preventDefault();
                if (await thaoTac("/api/don-vi/nhiem-vu/" + pc.ma + "/ghi-nhan", duLieuForm(e), uPc(pc.ma))) {
                  datXem([]);
                  datViTri({ lat: "", lng: "", gc: "" });
                }
              }}>
                <div className="row">
                  <div><label>Vĩ độ</label><input type="text" id="gn_lat" name="vi_do" value={viTri.lat} readOnly /></div>
                  <div><label>Kinh độ</label><input type="text" id="gn_lng" name="kinh_do" value={viTri.lng} readOnly /></div>
                  <div style={{ flex: 0 }}><button type="button" className="btn sec" onClick={() => layViTri(
                    (lat, lng) => datViTri({ lat: lat.toFixed(6), lng: lng.toFixed(6), gc: "Đã lấy vị trí: " + lat.toFixed(6) + ", " + lng.toFixed(6) }),
                    (loi) => datViTri((v) => ({ ...v, gc: loi })))}>Lấy vị trí thiết bị</button></div>
                </div>
                <div className="small muted" id="gps">{viTri.gc}</div>
                <label>Nhận xét hiện trường <span className="req">*</span></label><textarea name="nhan_xet" required></textarea>
                <label>Ảnh trước xử lý</label>
                <ChonTep xem={xem} datXem={datXem} />
                <div className="actions"><button className="btn" name="hanh_dong" value="ghi-nhan">Lưu ghi nhận</button>
                  <button className="btn orange" name="hanh_dong" value="khong-su-co">Báo không có sự cố</button></div>
              </form>
            </div></div>
          )}
          <div className="card"><div className="hd">Lịch sử cập nhật</div><div className="bd">
            <CapNhatList ds={pc.cap_nhat} />
            {pc.nghiem_thu.map((n, i) => (
              <div key={i} className={"flash " + (n.ket_qua === "Đạt" ? "ok" : "warn") + " small"}>Cán bộ duyệt kết quả {dt(n.thoi_gian)}: <b>{n.ket_qua}</b> — {n.nhan_xet || ""}</div>
            ))}
          </div></div>
        </>
      )}
    </>
  );
}

// Mở nhiệm vụ không thuộc đơn vị (BR09): báo lỗi rồi về danh sách nhiệm vụ
function BaoLoiChuyen({ loi }) {
  return (
    <>
      <div className="flash err">{loi}</div>
      <p><Link className="btn sec" to="/don-vi/nhiem-vu">Về danh sách nhiệm vụ</Link></p>
    </>
  );
}

export function CapNhat() {
  const [q] = useSearchParams();
  const pcMa = +(q.get("pc") || 0);
  const thaoTac = useThaoTac();
  const [xem, datXem] = useState([]);
  const ds = useTai(pcMa ? null : "/api/don-vi/cap-nhat");
  const ct = useTai(pcMa ? "/api/don-vi/nhiem-vu/" + pcMa : null);
  const navigate = useNavigate();

  if (!pcMa) {
    if (!ds.d) return null;
    // Mở từ menu: chỉ có 1 nhiệm vụ đang xử lý thì mở luôn, nhiều thì cho chọn
    if (ds.d.ds.length === 1) return <Navigate to={"/don-vi/cap-nhat?pc=" + ds.d.ds[0].ma} replace />;
    return (
      <>
        <TieuDe>Cập nhật tiến độ và kết quả</TieuDe>
        <h1>Cập nhật tiến độ và kết quả</h1>
        {ds.d.ds.length ? (
          <table className="t"><tbody>
            <tr><th>Mã PC</th><th>Báo cáo</th><th>Phường/xã</th><th>Ưu tiên</th><th className="num">Giao lúc</th></tr>
            {ds.d.ds.map((p) => (
              <tr key={p.ma} className="click" onClick={() => navigate("/don-vi/cap-nhat?pc=" + p.ma)}>
                <td className="ma-bc"><Link to={"/don-vi/cap-nhat?pc=" + p.ma}>PC-{p.ma}</Link></td><td>{p.ma_tra_cuu}</td>
                <td className="nw">{p.dia_ban}</td><td>{p.uu_tien}</td><td className="num">{dt(p.ngay)}</td>
              </tr>
            ))}
          </tbody></table>
        ) : (
          <div className="card empty">Không có nhiệm vụ nào đang xử lý.
            <div className="actions" style={{ justifyContent: "center" }}><Link className="btn" to="/don-vi/nhiem-vu">Xem nhiệm vụ được giao</Link></div></div>
        )}
      </>
    );
  }
  if (ct.loi) return <BaoLoiChuyen loi={ct.loi.message} />;
  const pc = ct.d && ct.d.ma === pcMa ? ct.d : null;
  if (!pc) return null;
  const uC = "/don-vi/cap-nhat?pc=" + pc.ma;
  return (
    <>
      <TieuDe>Cập nhật tiến độ và kết quả</TieuDe>
      <h1>Cập nhật tiến độ và kết quả</h1>
      <p><b>PC-{pc.ma}</b> · {pc.ma_tra_cuu} · {pc.loai_bc || ""} · <Tag s={pc.trang_thai} /> · <Link to={"/don-vi/nhiem-vu?pc=" + pc.ma}>Về chi tiết nhiệm vụ</Link></p>
      {pc.trang_thai === "Đang xử lý" ? (
        <>
          <div className="card"><div className="hd">Tiến độ</div><div className="bd">
            <form key={"td" + pc.cap_nhat.length} onSubmit={(e) => { e.preventDefault(); thaoTac("/api/don-vi/cap-nhat/" + pc.ma + "/tien-do", new FormData(e.target), uC); }}>
              <label>Phần trăm hoàn thành <span className="req">*</span></label><input type="number" name="phan_tram" min="0" max="100" defaultValue="50" required />
              <label>Công việc đã làm <span className="req">*</span></label><textarea name="noi_dung" required></textarea>
              <div className="actions"><button className="btn sec">Lưu tiến độ</button></div>
            </form>
          </div></div>
          <div className="card"><div className="hd">Gửi kết quả xử lý</div><div className="bd">
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (await thaoTac("/api/don-vi/cap-nhat/" + pc.ma + "/ket-qua", new FormData(e.target), uC)) datXem([]);
            }}>
              <label>Kết quả <span className="req">*</span></label><textarea name="ket_qua" required></textarea>
              <label>Ảnh sau xử lý <span className="req">*</span></label>
              <ChonTep required xem={xem} datXem={datXem} />
              <div className="actions"><button className="btn">Gửi kết quả</button></div>
            </form>
          </div></div>
        </>
      ) : <div className="flash info">Nhiệm vụ đang ở trạng thái “{pc.trang_thai}”, không cập nhật được.</div>}
      <div className="card"><div className="hd">Lịch sử cập nhật</div><div className="bd"><CapNhatList ds={pc.cap_nhat} /></div></div>
    </>
  );
}
