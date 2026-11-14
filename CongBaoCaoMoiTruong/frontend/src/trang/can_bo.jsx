import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { duLieuForm, guiForm } from "../api.js";
import { dt, dtInput, giay } from "../dinh_dang.js";
import { BanDoDiem } from "../thanh_phan/ban_do.jsx";
import { BangLoc, BcInfo, CapNhatList, LichSu, Media, Pager, Tag, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai, useUngDung } from "../ung_dung.jsx";

export function useThaoTac() {
  const { xong, baoTaiCho } = useUngDung();
  return async (url, duLieu, urlXong) => {
    try {
      const d = await guiForm(url, duLieu);
      xong(d.thong_bao || "Đã lưu.", d.chuyen_den || urlXong);
      return d;
    } catch (e) {
      baoTaiCho(e.message);
      return null;
    }
  };
}

function DongClick({ sel, to, children }) {
  const navigate = useNavigate();
  return <tr className={"click " + (sel ? "sel" : "")} onClick={() => navigate(to)}>{children}</tr>;
}

export function TiepNhan() {
  const [q] = useSearchParams();
  const tab = q.get("tab") || "moi";
  const ma = +(q.get("ma") || 0);
  const trang = q.get("trang") || 1;
  const thaoTac = useThaoTac();
  const ds = useTai("/api/can-bo/tiep-nhan?tab=" + tab + "&trang=" + trang);
  const ct = useTai(ma ? "/api/can-bo/bao-cao/" + ma : null);
  const d = ds.d;
  const bc = ma ? ct.d : null;
  const uTab = "/can-bo/tiep-nhan?tab=" + tab;
  return (
    <>
      <TieuDe>Tiếp nhận và kiểm tra báo cáo</TieuDe>
      <h1>Tiếp nhận và kiểm tra báo cáo</h1>
      {d && (
        <div className="tabs">
          <Link to="?tab=moi" className={tab === "moi" ? "on" : ""}>Mới gửi / đang xem xét ({d.dem["moi"]})</Link>
          <Link to="?tab=da-bo-sung" className={tab === "da-bo-sung" ? "on" : ""}>Đã bổ sung ({d.dem["da-bo-sung"]})</Link>
          <Link to="?tab=qua-han" className={tab === "qua-han" ? "on" : ""}>Quá hạn bổ sung ({d.dem["qua-han"]})</Link>
        </div>
      )}
      <div className="grid g-side">
        <div>
          {d && (d.ds.items.length ? (
            <>
              <table className="t"><tbody>
                <tr><th>Báo cáo</th><th className="num">Ngày gửi</th><th>Trạng thái</th></tr>
                {d.ds.items.map((b) => (
                  <DongClick key={b.ma} sel={ma === b.ma} to={"?tab=" + tab + "&ma=" + b.ma}>
                    <td><Link to={"?tab=" + tab + "&ma=" + b.ma}>{b.ma_tra_cuu}</Link><span className="cell-sub">{b.dia_ban}</span></td>
                    <td className="num">{dt(b.ngay_gui)}</td><td><Tag s={b.trang_thai} /></td>
                  </DongClick>
                ))}
              </tbody></table>
              <Pager ds={d.ds} coSo={"?tab=" + tab} />
            </>
          ) : <div className="card empty">Hàng đợi trống.</div>)}
        </div>
        <div>
          {bc ? (
            <>
              <div className="card"><div className="hd">Chi tiết {bc.ma_tra_cuu} <Tag s={bc.trang_thai} /></div><div className="bd">
                <BcInfo bc={bc} lienHe />
                <div className="grid g2" style={{ marginTop: 10 }}>
                  <div><BanDoDiem lat={bc.vi_do} lng={bc.kinh_do} /></div>
                  <div className="gallery">{bc.minh_chung.map((m) => <Media key={m.ma} m={m} nhan={(m.bo_sung ? "Bổ sung · " : "") + m.ten} />)}</div>
                </div>
                {bc.yeu_cau_bo_sung.map((y) => (
                  <div key={y.ma} className={"flash " + (y.trang_thai === "Đã phản hồi" ? "ok" : "warn") + " small"} style={{ marginTop: 10 }}>
                    <b>Yêu cầu bổ sung ({dt(y.ngay)}, hạn {dt(y.han)}):</b> {y.noi_dung} — <Tag s={y.trang_thai} />
                    {y.phan_hoi && <><br /><b>Phản hồi ({dt(y.ngay_phan_hoi)}):</b> {y.phan_hoi}</>}
                  </div>
                ))}
              </div></div>

              {bc.trang_thai === "Mới gửi" && (
                <form onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/tiep-nhan/" + bc.ma + "/nhan", {}); }}>
                  <button className="btn">Tiếp nhận và bắt đầu kiểm tra</button></form>
              )}
              {bc.trang_thai === "Đang xem xét" && (
                <div className="card"><div className="hd">Kết quả kiểm tra</div><div className="bd">
                  <form onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/tiep-nhan/" + bc.ma + "/hop-le", new FormData(e.target), uTab); }}>
                    <input type="hidden" name="rv" value={bc.rv} />
                    <div className="row">
                      <div><label>Loại sự cố <span className="req">*</span></label><select name="ma_loai" defaultValue="">
                        <option value="">— Chọn —</option>
                        {d && d.ds_loai.map((l) => <option key={l.ma} value={l.ma}>{l.ten}</option>)}</select></div>
                      <div><label>Mức độ ưu tiên <span className="req">*</span></label><select name="uu_tien" defaultValue="">
                        <option value="">— Chọn —</option>
                        {["Khẩn cấp", "Cao", "Trung bình", "Thấp"].map((u) => <option key={u}>{u}</option>)}</select></div>
                      <div style={{ flex: 0 }}><button className="btn">Xác nhận hợp lệ</button></div>
                    </div>
                  </form>
                  <hr className="sep" />
                  <form id="f2" onSubmit={(e) => {
                    e.preventDefault();
                    const nut = e.nativeEvent.submitter;
                    thaoTac("/api/can-bo/tiep-nhan/" + bc.ma + "/" + (nut ? nut.dataset.hanhDong : "bo-sung"), new FormData(e.target), uTab);
                  }}>
                    <input type="hidden" name="rv" value={bc.rv} />
                    <label>Nội dung yêu cầu bổ sung / lý do từ chối</label><textarea name="noi_dung"></textarea>
                    <div className="row">
                      <div><label>Hạn bổ sung (khi yêu cầu bổ sung)</label><input type="datetime-local" name="han" defaultValue={dtInput(bc.han_mac_dinh)} /></div>
                      <div style={{ flex: 0 }}><button className="btn orange" data-hanh-dong="bo-sung">Yêu cầu bổ sung</button></div>
                      <div style={{ flex: 0 }}><button className="btn red" data-hanh-dong="tu-choi">Từ chối</button></div>
                    </div>
                  </form>
                </div></div>
              )}
              {bc.trang_thai === "Chờ bổ sung" && (
                <div className="flash warn">Đang chờ người dân bổ sung.{" "}
                  {bc.yc_qua_han && <>Yêu cầu đã quá hạn.{" "}
                    <form className="inline" onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/tiep-nhan/" + bc.ma + "/dong", {}, uTab); }}>
                      <button className="btn sec sm">Đóng hồ sơ quá hạn</button></form></>}
                </div>
              )}
              <h2>Lịch sử</h2><LichSu ds={bc.lich_su} />
            </>
          ) : ma && ct.loi ? <div className="flash err">{ct.loi.message}</div>
            : <div className="card empty">Chọn một báo cáo trong danh sách để kiểm tra.</div>}
        </div>
      </div>
    </>
  );
}

export function PhanCong() {
  const [q] = useSearchParams();
  const ma = +(q.get("ma") || 0);
  const trang = q.get("trang") || 1;
  const thaoTac = useThaoTac();
  const t = useTai("/api/can-bo/phan-cong?ma=" + ma + "&trang=" + trang);
  const d = t.d;
  const c = d && d.chon && d.chon.bao_cao.ma === ma ? d.chon : null;
  const bc = c && c.bao_cao;
  const hl = c && c.pc_hieu_luc;
  return (
    <>
      <TieuDe>Phân công xử lý</TieuDe>
      <h1>Phân công xử lý</h1>
      <div className="grid g-side">
        <div>
          <h2 style={{ marginTop: 0 }}>Báo cáo chờ phân công</h2>
          {d && (d.ds.items.length ? (
            <>
              <table className="t"><tbody>
                <tr><th>Báo cáo</th><th>Loại sự cố</th><th>Ưu tiên</th></tr>
                {d.ds.items.map((b) => (
                  <DongClick key={b.ma} sel={ma === b.ma} to={"?ma=" + b.ma}>
                    <td><Link to={"?ma=" + b.ma}>{b.ma_tra_cuu}</Link><span className="cell-sub">{b.dia_ban}</span></td>
                    <td>{b.loai || ""}</td><td>{b.uu_tien}</td>
                  </DongClick>
                ))}
              </tbody></table>
              <Pager ds={d.ds} coSo="?" />
            </>
          ) : <div className="card empty">Không có báo cáo chờ phân công.</div>)}
        </div>
        <div>
          {bc ? (
            <>
              <div className="card"><div className="hd">{hl ? "Giao lại" : "Giao nhiệm vụ cho"} {bc.ma_tra_cuu} <Tag s={bc.trang_thai} /></div><div className="bd">
                <BcInfo bc={bc} />
                <div style={{ marginTop: 8 }}><BanDoDiem lat={bc.vi_do} lng={bc.kinh_do} /></div>
                {hl && <div className="flash warn small" style={{ marginTop: 10 }}>Đang có phân công hiệu lực PC-{hl.ma} ({hl.don_vi}, {hl.trang_thai}). Giao lại sẽ chuyển phân công này sang “Đã thay thế”.</div>}
                {c.giao_duoc && (
                  <form onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/phan-cong/" + bc.ma + "/giao", new FormData(e.target)); }}>
                    <input type="hidden" name="rv" value={bc.rv} />
                    <div className="row">
                      <div><label>Đơn vị xử lý <span className="req">*</span></label><select name="ma_don_vi" required>
                        {c.don_vi.map((x) => <option key={x.ma} value={x.ma} disabled={hl && hl.ma_don_vi === x.ma}>{x.ten}{x.goi_y ? " (gợi ý, phụ trách địa bàn)" : ""}</option>)}
                      </select></div>
                    </div>
                    <label>Nội dung nhiệm vụ, chỉ dẫn <span className="req">*</span></label>
                    <textarea name="noi_dung" required></textarea>
                    <div className="actions"><button className="btn">{hl ? "Giao lại" : "Giao nhiệm vụ"}</button></div>
                  </form>
                )}
              </div></div>
              <h2>Các lần phân công của báo cáo</h2>
              {bc.phan_cong.length ? (
                <BangLoc
                  dau={<tr><th>Mã PC</th><th>Đơn vị</th><th>Giao lúc</th><th>Trạng thái</th><th>Ghi chú</th></tr>}
                  dong={bc.phan_cong.map((p) => ({
                    key: p.ma, chu: ["PC-" + p.ma, p.don_vi, dt(p.ngay), p.trang_thai, p.ly_do_tra_lai].join(" "),
                    el: <tr key={p.ma}><td>PC-{p.ma}</td><td>{p.don_vi}</td><td>{dt(p.ngay)}</td><td><Tag s={p.trang_thai} /></td><td>{p.ly_do_tra_lai || ""}</td></tr>,
                  }))}
                />
              ) : <div className="small muted">Chưa có.</div>}
            </>
          ) : <div className="card empty">Chọn một báo cáo để giao nhiệm vụ.</div>}
        </div>
      </div>
    </>
  );
}

export function NghiemThu() {
  const [q] = useSearchParams();
  const pcChon = +(q.get("pc") || 0);
  const trang = q.get("trang") || 1;
  const thaoTac = useThaoTac();
  const t = useTai("/api/can-bo/nghiem-thu?pc=" + pcChon + "&trang=" + trang);
  const d = t.d;
  const pc = d && d.chon && (!pcChon || d.chon.ma === pcChon) ? d.chon : null;
  return (
    <>
      <TieuDe>Duyệt kết quả</TieuDe>
      <h1>Duyệt kết quả xử lý</h1>
      {d && (d.ds.items.length ? (
        <>
          <table className="t"><tbody>
            <tr><th>Mã PC</th><th>Báo cáo</th><th>Đơn vị</th><th>Đơn vị báo</th><th className="num">Gửi kết quả lúc</th></tr>
            {d.ds.items.map((p) => (
              <DongClick key={p.ma} sel={pc && pc.ma === p.ma} to={"?trang=" + d.ds.trang + "&pc=" + p.ma}>
                <td>PC-{p.ma}</td><td>{p.ma_tra_cuu}</td><td>{p.don_vi}</td><td>{p.ket_qua_loai || ""}</td>
                <td className="num">{dt(p.ket_qua_luc)}{p.ket_qua_luc && giay(d.bay_gio) - giay(p.ket_qua_luc) < 900 && <span className="tag moi-gui">Mới</span>}</td>
              </DongClick>
            ))}
          </tbody></table>
          <Pager ds={d.ds} coSo="?" />
        </>
      ) : <div className="card empty">Không có nhiệm vụ chờ duyệt kết quả.</div>)}
      {pc && (
        <>
          <div className="grid g2" style={{ marginTop: 16 }}>
            <div className="card"><div className="hd">Báo cáo {pc.ma_tra_cuu} — PC-{pc.ma} <Tag s={pc.trang_thai} /></div><div className="bd">
              <BcInfo bc={pc.bao_cao} />
              <p className="small"><b>Nhiệm vụ:</b> {pc.noi_dung}<br /><b>Đơn vị:</b> {pc.don_vi}</p>
              <div className="gallery">{pc.bao_cao.minh_chung.map((m) => <Media key={m.ma} m={m} nhan="Người dân gửi" />)}</div>
              {pc.nghiem_thu.map((n, i) => (
                <div key={i} className={"flash " + (n.ket_qua === "Đạt" ? "ok" : "warn") + " small"}>Duyệt kết quả {dt(n.thoi_gian)}: <b>{n.ket_qua}</b> — {n.nhan_xet || ""}</div>
              ))}
            </div></div>
            <div className="card"><div className="hd">Ghi nhận, tiến độ và kết quả của đơn vị</div><div className="bd"><CapNhatList ds={pc.cap_nhat} /></div></div>
          </div>
          {pc.trang_thai === "Chờ duyệt kết quả" && (
            <div className="card"><div className="hd">Quyết định duyệt kết quả</div><div className="bd">
              <form key={pc.ma} onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/nghiem-thu/" + pc.ma, new FormData(e.target)); }}>
                <div className="radios">
                  <label><input type="radio" name="ket_qua" value="Đạt" disabled={pc.khong_su_co} defaultChecked={!pc.khong_su_co} /> Đạt</label>
                  <label><input type="radio" name="ket_qua" value="Chưa đạt" /> Chưa đạt — yêu cầu xử lý thêm</label>
                  <label><input type="radio" name="ket_qua" value="Không có sự cố" defaultChecked={pc.khong_su_co} disabled={!pc.khong_su_co} /> Xác nhận không có sự cố</label>
                </div>
                <label>Nhận xét / yêu cầu xử lý thêm</label><textarea name="nhan_xet"></textarea>
                <div className="actions"><button className="btn">Lưu kết quả duyệt</button></div>
              </form>
            </div></div>
          )}
        </>
      )}
    </>
  );
}

export function KiemDuyet() {
  const [q] = useSearchParams();
  const ma = +(q.get("ma") || 0);
  const trang = q.get("trang") || 1;
  const thaoTac = useThaoTac();
  const t = useTai("/api/can-bo/kiem-duyet?ma=" + ma + "&trang=" + trang);
  const d = t.d;
  const c = d && d.chon && (!ma || d.chon.bao_cao.ma === ma) ? d.chon : null;
  const bc = c && c.bao_cao;
  return (
    <>
      <TieuDe>Kiểm duyệt và công khai</TieuDe>
      <h1>Kiểm duyệt và công khai</h1>
      {d && (d.ds.items.length ? (
        <>
          <table className="t"><tbody>
            <tr><th>Mã báo cáo</th><th>Loại</th><th>Phường/xã</th><th>Đơn vị xử lý</th></tr>
            {d.ds.items.map((b) => (
              <DongClick key={b.ma} sel={bc && bc.ma === b.ma} to={"?trang=" + d.ds.trang + "&ma=" + b.ma}>
                <td>{b.ma_tra_cuu}</td><td>{b.loai || ""}</td><td>{b.dia_ban}</td><td>{b.don_vi_xu_ly}</td>
              </DongClick>
            ))}
          </tbody></table>
          <Pager ds={d.ds} coSo="?" />
        </>
      ) : <div className="card empty">Không có báo cáo chờ công khai.</div>)}
      {bc && (
        <>
          <form key={bc.ma + (c.ban_nhap ? c.ban_nhap.thoi_gian : "")} onSubmit={(e) => { e.preventDefault(); thaoTac("/api/can-bo/kiem-duyet/" + bc.ma, duLieuForm(e)); }}>
            <div className="grid g2" style={{ marginTop: 16 }}>
              <div className="card"><div className="hd">Dữ liệu gốc (nội bộ) — {bc.ma_tra_cuu} <Tag s={bc.trang_thai} /></div><div className="bd">
                <BcInfo bc={bc} lienHe />
                <h2>Chọn ảnh/video được công khai</h2>
                <div className="gallery">
                  {c.anh.map((m) => {
                    const url = "/tep/" + m.bang + "/" + m.ma;
                    return (
                      <figure key={m.bang + m.ma}>
                        {m.loai === "mp4" ? <video src={url} controls preload="metadata"></video>
                          : <a href={url} target="_blank" rel="noreferrer"><img src={url} alt="" /></a>}
                        <figcaption><label style={{ fontWeight: 400, margin: 0 }}>
                          <input type="checkbox" name="anh" value={m.bang + "-" + m.ma} defaultChecked={m.cong_khai} /> {m.nhan}</label></figcaption>
                      </figure>
                    );
                  })}
                </div>
              </div></div>
              <div className="card"><div className="hd">Bản công khai {c.ban_nhap && <span className="small">bản nháp đã lưu {dt(c.ban_nhap.thoi_gian)}</span>}</div><div className="bd">
                <label>Tiêu đề <span className="req">*</span></label><input type="text" name="tieu_de" defaultValue={c.tieu_de} maxLength={200} required />
                <label>Nội dung và kết quả công khai <span className="req">*</span></label><textarea name="noi_dung" rows={7} defaultValue={c.noi_dung} required></textarea>
                <label style={{ fontWeight: 400 }}><input type="checkbox" name="da_kiem_tra" value="1" defaultChecked={c.ban_nhap && c.ban_nhap.da_kiem_tra} />{" "}
                  Đã kiểm tra: không có họ tên, liên hệ, mặt người, biển số xe</label>
                <label>Lý do không duyệt / nội dung cần sửa</label><textarea name="ly_do"></textarea>
                <div className="actions">
                  <button className="btn" name="hanh_dong" value="duyet">Duyệt và công khai</button>
                  <button className="btn sec" name="hanh_dong" value="luu">Lưu bản nháp</button>
                  <button className="btn red" name="hanh_dong" value="khong-duyet">Không duyệt</button>
                </div>
              </div></div>
            </div>
          </form>
          <h2>Lịch sử kiểm duyệt</h2>
          {c.lich_su_kd.length ? (
            <BangLoc
              dau={<tr><th>Lần</th><th>Cán bộ</th><th>Thời gian</th><th>Kết quả</th><th>Đang hiển thị</th><th>Lý do</th></tr>}
              dong={c.lich_su_kd.map((k) => ({
                key: k.ma, chu: ["KD-" + k.ma, k.can_bo, dt(k.thoi_gian), k.trang_thai, k.ly_do].join(" "),
                el: <tr key={k.ma}><td>KD-{k.ma}</td><td>{k.can_bo}</td><td>{dt(k.thoi_gian)}</td><td><Tag s={k.trang_thai} /></td>
                  <td>{k.dang_hien_thi ? "Có" : "Không"}</td><td>{k.ly_do || ""}</td></tr>,
              }))}
            />
          ) : <div className="small muted">Chưa có lần kiểm duyệt nào.</div>}
        </>
      )}
    </>
  );
}
