// Các thành phần giao diện dùng chung (tương ứng các macro của giao diện cũ).
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { boDau, dt } from "../dinh_dang.js";
import { useUngDung } from "../ung_dung.jsx";

const LOP_TAG = {
  "Mới gửi": "s-moi", "Đang xem xét": "s-xem", "Chờ bổ sung": "s-bs", "Chờ phân công": "s-pc", "Đã phân công": "s-pc",
  "Đang xử lý": "s-xl", "Chờ duyệt kết quả": "s-nt", "Chờ công khai": "s-ck", "Hoàn tất": "s-ok", "Hoàn thành": "s-ok",
  "Bị từ chối": "s-no", "Đã đóng": "s-no", "Bị trả lại": "s-no", "Đã thay thế": "s-no", "Chờ tiếp nhận": "s-moi",
  "Chờ duyệt": "s-bs", "Đã duyệt": "s-ok", "Không duyệt": "s-no", "Đã chấp thuận": "s-ok", "Chờ phản hồi": "s-bs",
  "Đã phản hồi": "s-pc", "Quá hạn": "s-no", "Bị khóa": "s-no", "Hoạt động": "s-pc", "Chờ gửi": "s-bs", "Đã gửi": "s-ok",
  Lỗi: "s-no",
};

export function Tag({ s }) {
  return <span className={"tag " + (LOP_TAG[s] || "")}>{s}</span>;
}

export function Flash() {
  const { flashes } = useUngDung();
  return flashes.map((f) => (
    <div key={f.id} className={"flash " + f.loai}>
      {f.nd}
    </div>
  ));
}

export function TieuDe({ children }) {
  // đặt tiêu đề tab trình duyệt
  if (typeof document !== "undefined") document.title = children;
  return null;
}

export function Media({ m, nhan }) {
  const url = "/tep/" + m.bang + "/" + m.ma;
  return (
    <figure>
      {m.loai === "mp4" ? (
        <video src={url} controls preload="metadata"></video>
      ) : (
        <a href={url} target="_blank" rel="noreferrer">
          <img src={url} alt={m.ten || ""} loading="lazy" />
        </a>
      )}
      <figcaption>{nhan !== undefined ? nhan : m.nhan || m.ten}</figcaption>
    </figure>
  );
}

export function BcInfo({ bc, lienHe = false }) {
  const n = bc.nguoi_bao_cao;
  return (
    <>
      <p className="mo-ta">{bc.mo_ta}</p>
      <dl className="meta">
        <dt>Phát hiện</dt><dd>{dt(bc.thoi_gian_phat_hien)}</dd>
        <dt>Ngày gửi</dt><dd>{dt(bc.ngay_gui)}</dd>
        <dt>Phường/xã</dt><dd>{bc.dia_ban}</dd>
        {bc.dia_chi && (<><dt>Địa chỉ</dt><dd>{bc.dia_chi}</dd></>)}
        {bc.loai && (<><dt>Loại sự cố</dt><dd>{bc.loai}</dd></>)}
        {bc.uu_tien && (<><dt>Ưu tiên</dt><dd>{bc.uu_tien}</dd></>)}
      </dl>
      {lienHe && (
        <dl className="meta noi-bo">
          <dt>Người báo cáo</dt><dd>{n ? n.ho_ten || "(không tên)" : "Ẩn danh"}</dd>
          {n && n.so_dien_thoai && (<><dt>Điện thoại</dt><dd>{n.so_dien_thoai}</dd></>)}
          {n && n.email && (<><dt>Email</dt><dd>{n.email}</dd></>)}
        </dl>
      )}
    </>
  );
}

export function LichSu({ ds }) {
  return (
    <BangLoc
      dau={<tr><th>Thời gian</th><th>Người thực hiện</th><th>Trạng thái cũ → mới</th><th>Ghi chú</th></tr>}
      dong={ds.map((h, i) => ({
        key: i,
        chu: [dt(h.thoi_gian), h.nguoi, h.cu, h.moi, h.ghi_chu].join(" "),
        el: (
          <tr key={i}><td>{dt(h.thoi_gian)}</td><td>{h.nguoi}</td><td>{(h.cu || "—") + " → " + h.moi}</td><td>{h.ghi_chu || ""}</td></tr>
        ),
      }))}
    />
  );
}

// Phân trang phía máy chủ: ds = {trang, so_trang, tong}; coSo = đường dẫn hiện tại không có tham số trang.
export function Pager({ ds, coSo }) {
  const noi = coSo + (coSo.includes("?") ? "&" : "?");
  const so = [];
  for (let i = 1; i <= ds.so_trang; i++) {
    if (i === 1 || i === ds.so_trang || Math.abs(i - ds.trang) <= 2) {
      so.push(i === ds.trang
        ? <span key={i} className="pg on" aria-current="page">{i}</span>
        : <Link key={i} className="pg" to={noi + "trang=" + i}>{i}</Link>);
    } else if (Math.abs(i - ds.trang) === 3) so.push(<span key={i} className="pg ba-cham">…</span>);
  }
  return (
    <nav className="pager" aria-label="Phân trang">
      <span className="pager-tong">{ds.tong} dòng</span>
      {ds.so_trang > 1 && (
        <span className="pager-so">
          {ds.trang > 1 ? <Link className="pg" to={noi + "trang=" + (ds.trang - 1)} aria-label="Trang trước">‹</Link> : <span className="pg tat">‹</span>}
          {so}
          {ds.trang < ds.so_trang ? <Link className="pg" to={noi + "trang=" + (ds.trang + 1)} aria-label="Trang sau">›</Link> : <span className="pg tat">›</span>}
        </span>
      )}
    </nav>
  );
}

// Bảng dài: ô tìm nhanh + phân trang ngay trên trình duyệt (mỗi trang `soDong` dòng). Bảng ít dòng hơn thì để nguyên.
// dong = [{key, chu (chữ để tìm), el (thẻ <tr>), sel}]
export function BangLoc({ dau, dong, soDong = 10, rong, cuon = false, style, className = "t" }) {
  const [tu, datTu] = useState("");
  const chonIdx = dong.findIndex((r) => r.sel);
  const [trangChon, datTrang] = useState(chonIdx >= 0 ? Math.floor(chonIdx / soDong) + 1 : 1);
  const chu = useMemo(() => dong.map((r) => boDau(r.chu)), [dong]);
  const soCot = dau && dau.props && dau.props.children ? [].concat(dau.props.children).length : 1;

  const bang = (rows) => (
    <table className={className} style={style}>
      <tbody>
        {dau}
        {rows}
        {rong && dong.length === 0 && <tr><td colSpan={soCot} className="empty">{rong}</td></tr>}
      </tbody>
    </table>
  );
  const boc = (x, them = "") => (cuon ? <div className={"scroll" + them}>{x}</div> : x);

  if (dong.length <= soDong) return boc(bang(dong.map((r) => r.el)));

  const t = boDau(tu.trim());
  const khop = dong.filter((r, i) => !t || chu[i].includes(t));
  const soTrang = Math.max(1, Math.ceil(khop.length / soDong));
  const trang = Math.min(Math.max(1, trangChon), soTrang);
  const hien = khop.slice((trang - 1) * soDong, trang * soDong);
  const nut = (nhan, so, lop, tat) =>
    tat ? <span key={nhan + lop} className={"pg" + (lop ? " " + lop : "")} aria-current={lop === "on" ? "page" : undefined}>{nhan}</span>
        : <button key={nhan} type="button" className={"pg" + (lop ? " " + lop : "")} onClick={() => datTrang(so)}>{nhan}</button>;
  const cacSo = [];
  for (let i = 1; i <= soTrang; i++) {
    if (i === 1 || i === soTrang || Math.abs(i - trang) <= 2) cacSo.push(nut(String(i), i, i === trang ? "on" : "", i === trang));
    else if (Math.abs(i - trang) === 3) cacSo.push(<span key={"bc" + i} className="pg ba-cham">…</span>);
  }
  return (
    <>
      <div className="loc-bang">
        <input type="search" placeholder="Tìm trong danh sách" aria-label="Tìm trong danh sách" value={tu}
          onChange={(e) => { datTu(e.target.value); datTrang(1); }} />
      </div>
      {boc(
        bang(<>
          {hien.map((r) => r.el)}
          {khop.length === 0 && <tr><td className="empty" colSpan={soCot}>Không có dòng nào khớp.</td></tr>}
        </>),
        " het-cuon"
      )}
      <nav className="pager" aria-label="Phân trang">
        <span className="pager-tong">{khop.length} dòng</span>
        {soTrang > 1 && (
          <span className="pager-so">
            {nut("‹", trang - 1, "", trang === 1)}
            {cacSo}
            {nut("›", trang + 1, "", trang === soTrang)}
          </span>
        )}
      </nav>
    </>
  );
}

// Xem trước các tệp vừa chọn (ảnh/video)
export function ChonTep({ name = "tep", required = false, xem, datXem }) {
  return (
    <>
      <input type="file" name={name} multiple accept=".jpg,.jpeg,.png,.mp4" required={required}
        onChange={(e) => datXem([...e.target.files].map((f) => ({ ten: f.name, co: f.size, video: f.type.startsWith("video"), url: URL.createObjectURL(f) })))} />
      <div className="gallery" style={{ marginTop: 8 }}>
        {xem.map((f, i) => (
          <figure key={i}>
            {f.video ? <video src={f.url} muted></video> : <img src={f.url} alt="" />}
            <figcaption>{f.ten + " (" + (f.co / 1048576).toFixed(1) + " MB)"}</figcaption>
          </figure>
        ))}
      </div>
    </>
  );
}

// Danh sách ghi nhận, tiến độ, kết quả của đơn vị
export function CapNhatList({ ds }) {
  return (
    <div className="timeline">
      {ds.length === 0 && <div className="small muted">Chưa có cập nhật.</div>}
      {ds.map((c) => (
        <div className="it" key={c.ma}>
          <b>{dt(c.thoi_gian)} · {c.loai}</b>
          {c.phan_tram !== null && c.phan_tram !== undefined && " · " + c.phan_tram + "%"}
          {c.vi_do !== null && c.vi_do !== undefined && (
            <span className="small muted"> · vị trí {c.vi_do}, {c.kinh_do}
              {c.khoang_cach !== null && c.khoang_cach !== undefined && " (cách điểm báo " + c.khoang_cach + " m)"}</span>
          )}
          <div>{c.noi_dung}</div>
          {c.minh_chung.length > 0 && (
            <div className="gallery" style={{ marginTop: 6 }}>{c.minh_chung.map((m) => <Media key={m.ma} m={m} />)}</div>
          )}
        </div>
      ))}
    </div>
  );
}

export function DangTai({ t }) {
  if (t.loi) return <div className="flash err">{t.loi.message}</div>;
  return null;
}
