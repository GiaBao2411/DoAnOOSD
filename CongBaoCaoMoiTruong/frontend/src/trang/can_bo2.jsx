import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { dt, dtGiay, dtInput, dtNgan, giay, so0, so1 } from "../dinh_dang.js";
import { BanDoDiem, BanDoXem, escHtml } from "../thanh_phan/ban_do.jsx";
import { BangLoc, BcInfo, LichSu, Media, Pager, Tag, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai, useUngDung } from "../ung_dung.jsx";

function BieuDo({ rows, nguongKk, nguongTds, w = 900, h = 240 }) {
  if (!rows.length) return null;
  const r = [...rows].sort((a, b) => giay(a.thoi_gian) - giay(b.thoi_gian));
  const t0 = giay(r[0].thoi_gian), t1 = giay(r[r.length - 1].thoi_gian);
  const span = Math.max(t1 - t0, 1);
  const vmax = Math.max(...r.map((x) => x.kk), ...r.map((x) => x.tds), nguongKk, nguongTds) * 1.1;
  const L = 50, R = 10, T = 10, B = 28;
  const W = w - L - R, H = h - T - B;
  const X = (t) => L + (W * (t - t0)) / span;
  const Y = (v) => T + H - (H * v) / vmax;
  const duong = (k) => r.map((x) => X(giay(x.thoi_gian)).toFixed(1) + "," + Y(x[k]).toFixed(1)).join(" ");
  const nhan = (t) => {
    const d = new Date(t * 1000);
    return String(d.getUTCHours()).padStart(2, "0") + ":" + String(d.getUTCMinutes()).padStart(2, "0");
  };
  return (
    <svg viewBox={"0 0 " + w + " " + h} className="chart" xmlns="http://www.w3.org/2000/svg">
      <rect x={L} y={T} width={W} height={H} fill="#fff" stroke="#9fb4b0" />
      {[0, 1, 2, 3, 4].map((k) => {
        const v = (vmax * k) / 4;
        return (
          <g key={"y" + k}>
            <line x1={L} x2={L + W} y1={Y(v)} y2={Y(v)} stroke="#dbe4e2" />
            <text x={L - 4} y={Y(v) + 4} fontSize="10" textAnchor="end" fill="#1d2a2a">{Math.floor(v)}</text>
          </g>
        );
      })}
      {[0, 1, 2, 3, 4].map((k) => {
        const t = t0 + ((t1 - t0) * k) / 4;
        return <text key={"x" + k} x={X(t)} y={h - 8} fontSize="10" textAnchor={k === 0 ? "start" : k === 4 ? "end" : "middle"} fill="#1d2a2a">{nhan(t)}</text>;
      })}
      <line x1={L} x2={L + W} y1={Y(nguongKk)} y2={Y(nguongKk)} stroke="#c0392b" strokeDasharray="6 4" />
      {nguongTds !== nguongKk && <line x1={L} x2={L + W} y1={Y(nguongTds)} y2={Y(nguongTds)} stroke="#e67e22" strokeDasharray="6 4" />}
      <polyline fill="none" stroke="#2e6da4" strokeWidth="2" points={duong("kk")} />
      <polyline fill="none" stroke="#1f6f43" strokeWidth="2" points={duong("tds")} />
      {r.filter((x) => x.vuot).map((x, i) => (
        <circle key={i} cx={X(giay(x.thoi_gian))} cy={Y(x.kk > nguongKk ? x.kk : x.tds)} r="3" fill="#c0392b" />
      ))}
    </svg>
  );
}

export function ThietBiDo() {
  const [q, datQ] = useSearchParams();
  const tudong = q.get("tu_dong") === "1";
  const tham = new URLSearchParams(q);
  tham.delete("tu_dong");
  const t = useTai("/api/can-bo/tram-quan-trac?" + tham.toString());
  const { lamMoiTrang } = useUngDung();
  useEffect(() => {
    if (!tudong) return;
    const h = setInterval(lamMoiTrang, 10000);
    return () => clearInterval(h);
  }, [tudong, lamMoiTrang]);
  const d = t.d;
  if (!d) return t.loi ? <div className="flash err">{t.loi.message}</div> : null;
  const chon = d.chon;
  const diem = d.tq.filter((x) => x.tram.vi_do !== null).map((x) => ({
    lat: x.tram.vi_do, lng: x.tram.kinh_do,
    html: "<b>" + escHtml(x.tram.ma_thiet_bi) + "</b> – " + escHtml(x.tram.ten) + "<br>" + (x.mat_ket_noi ? "Mất kết nối" : "Đang gửi") +
      (x.moi ? "<br>Không khí " + so0(x.moi.kk) + " · TDS " + so0(x.moi.tds) + " ppm" : ""),
  }));
  return (
    <>
      <TieuDe>Thiết bị đo (IoT)</TieuDe>
      <h1>Thiết bị đo môi trường (IoT)</h1>
      <div className="grid" style={{ gridTemplateColumns: "minmax(0,2fr) minmax(0,1fr)", alignItems: "start" }}>
        <div>
          <BangLoc
            rong="Chưa có thiết bị. Thêm thiết bị ở Danh mục → Thiết bị đo."
            dau={<tr><th>Thiết bị</th><th className="num">Không khí (ppm)</th><th className="num">TDS nước (ppm)</th><th className="num">Lần gửi cuối</th><th>Kết nối</th></tr>}
            dong={d.tq.map((x) => {
              const tr = x.tram, m = x.moi;
              return {
                key: tr.ma, sel: chon && chon.ma === tr.ma, chu: [tr.ma_thiet_bi, tr.ten, tr.dia_ban].join(" "),
                el: (
                  <DongTram key={tr.ma} sel={chon && chon.ma === tr.ma} ma={tr.ma}>
                    <td><b>{tr.ma_thiet_bi}</b><span className="cell-sub">{tr.ten}, {tr.dia_ban}</span></td>
                    {m ? (<>
                      <td className={"num " + (m.kk > tr.nguong_kk ? "vuot" : "")}>{so0(m.kk)}</td>
                      <td className={"num " + (m.tds > tr.nguong_tds ? "vuot" : "")}>{so0(m.tds)}</td></>)
                      : (<><td className="num">—</td><td className="num">—</td></>)}
                    <td className="num">{tr.lan_gui_cuoi ? dtNgan(tr.lan_gui_cuoi) : "Chưa gửi"}</td>
                    <td>{x.mat_ket_noi ? <span className="tag s-no">Mất kết nối</span> : <span className="tag s-pc">Đang gửi</span>}</td>
                  </DongTram>
                ),
              };
            })}
          />
        </div>
        <div className="card"><div className="hd">Vị trí các thiết bị</div><div className="bd"><BanDoXem id="maptram" diem={diem} zoom={13} className="map sm" /></div></div>
      </div>

      {chon && (
        <div className="card"><div className="hd">Số liệu theo thời gian — {chon.ma_thiet_bi} · {chon.ten}{" "}
          <span className="small" style={{ fontWeight: 400 }}>Ngưỡng: không khí {so0(chon.nguong_kk)} ppm · TDS {so0(chon.nguong_tds)} ppm</span></div>
          <div className="bd">
            <form className="row" id="floc" key={d.tu + d.den + chon.ma} onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.target);
              const p = { tram: f.get("tram"), tu: f.get("tu"), den: f.get("den") };
              if (f.get("vuot")) p.vuot = "1";
              datQ(p);
            }}>
              <div><label>Thiết bị <span className="req">*</span></label><select name="tram" defaultValue={chon.ma}>
                {d.tq.map((x) => <option key={x.tram.ma} value={x.tram.ma}>{x.tram.ma_thiet_bi} – {x.tram.ten}</option>)}</select></div>
              <div><label>Từ thời điểm <span className="req">*</span></label><input type="datetime-local" name="tu" defaultValue={dtInput(d.tu)} /></div>
              <div><label>Đến thời điểm <span className="req">*</span></label><input type="datetime-local" name="den" defaultValue={dtInput(d.den)} /></div>
              <div style={{ flex: "0 0 auto", minWidth: 0, whiteSpace: "nowrap" }}><label style={{ fontWeight: 400 }}>
                <input type="checkbox" name="vuot" value="1" defaultChecked={!!q.get("vuot")} /> Chỉ xem vượt ngưỡng</label></div>
              <div style={{ flex: "0 0 auto", minWidth: 0 }}><button className="btn">Xem</button></div>
            </form>
            <label style={{ fontWeight: 400, marginTop: 8 }}><input type="checkbox" id="tudong" checked={tudong} onChange={(e) => {
              const p = new URLSearchParams(q);
              p.delete("tu");
              p.delete("den");
              if (e.target.checked) p.set("tu_dong", "1");
              else p.delete("tu_dong");
              datQ(p);
            }} /> Tự làm mới mỗi 10 giây</label>
            {d.loi && <div className="flash err">{d.loi}</div>}
            {d.rows.length > 0 && (
              <>
                <div className="legend small"><span style={{ color: "#2e6da4" }}>━ Không khí (ppm)</span> <span style={{ color: "#1f6f43" }}>━ TDS (ppm)</span>{" "}
                  <span style={{ color: "#c0392b" }}>┅ Ngưỡng</span> <span style={{ color: "#c0392b" }}>● Lần đo vượt ngưỡng</span></div>
                <BieuDo rows={d.rows} nguongKk={chon.nguong_kk} nguongTds={chon.nguong_tds} />
              </>
            )}
            <h3>Bảng số liệu</h3>
            {d.rows.length ? (
              <BangLoc cuon
                dau={<tr><th>Thời gian đo</th><th className="num">Không khí (ppm)</th><th className="num">TDS (ppm)</th><th>Vượt ngưỡng</th></tr>}
                dong={d.rows.slice(0, 200).map((r, i) => ({
                  key: i, chu: [dtGiay(r.thoi_gian), so1(r.kk), so1(r.tds), r.vuot ? "Có" : "Không"].join(" "),
                  el: (<tr key={i} className={r.vuot ? "row-vuot" : ""}><td>{dtGiay(r.thoi_gian)}</td>
                    <td className={"num " + (r.kk > chon.nguong_kk ? "vuot" : "")}>{so1(r.kk)}</td>
                    <td className={"num " + (r.tds > chon.nguong_tds ? "vuot" : "")}>{so1(r.tds)}</td>
                    <td>{r.vuot ? "Có" : "Không"}</td></tr>),
                }))}
              />
            ) : <div className="empty">Thiết bị chưa có số liệu trong khoảng thời gian này. Hãy chạy thiết bị thật hoặc tệp giả lập thiết bị.</div>}
          </div></div>
      )}
    </>
  );
}

function DongTram({ sel, ma, children }) {
  const [q, datQ] = useSearchParams();
  return <tr className={"click " + (sel ? "sel" : "")} onClick={() => {
    const p = new URLSearchParams();
    p.set("tram", ma);
    if (q.get("tu_dong")) p.set("tu_dong", "1");
    datQ(p);
  }}>{children}</tr>;
}

export function TraCuuNoiBo() {
  const [q] = useSearchParams();
  const navigate = useNavigate();
  const { cauHinh } = useUngDung();
  const f = { q: q.get("q") || "", trang_thai: q.get("trang_thai") || "", loai: q.get("loai") || "", dia_ban: q.get("dia_ban") || "",
    tu_ngay: q.get("tu_ngay") || "", den_ngay: q.get("den_ngay") || "" };
  const ma = +(q.get("ma") || 0);
  const trang = q.get("trang") || 1;
  const qs = "?" + new URLSearchParams(f).toString();
  const t = useTai("/api/can-bo/tra-cuu" + qs + "&trang=" + trang);
  const ct = useTai(ma ? "/api/can-bo/bao-cao/" + ma : null);
  const d = t.d;
  const bc = ma ? ct.d : null;
  const loc = (form) => {
    const p = new URLSearchParams();
    new FormData(form).forEach((v, k) => p.set(k, v));
    navigate("/can-bo/tra-cuu?" + p.toString());
  };
  return (
    <>
      <TieuDe>Tra cứu báo cáo (nội bộ)</TieuDe>
      <h1>Tra cứu báo cáo (nội bộ)</h1>
      <form className="bo-loc" key={qs + (d ? 1 : 0)} onSubmit={(e) => { e.preventDefault(); loc(e.target); }}>
        <div className="bo-loc-tim">
          <label htmlFor="q">Mã báo cáo hoặc từ khóa</label>
          <div className="bo-loc-hang">
            <input type="search" id="q" name="q" defaultValue={f.q} placeholder="BC2026-000123" />
            <button className="btn">Tìm kiếm</button>
            <Link className="btn sec" to="/can-bo/tra-cuu">Xóa lọc</Link>
          </div>
        </div>
        <div className="bo-loc-luoi">
          <div><label htmlFor="loc-tt">Trạng thái</label><select id="loc-tt" name="trang_thai" defaultValue={f.trang_thai} onChange={(e) => loc(e.target.form)}>
            <option value="">Tất cả</option>
            <option value={cauHinh ? cauHinh.loc_o_don_vi : "o-don-vi"}>Đang ở đơn vị (đã giao, đang xử lý)</option>
            {cauHinh && cauHinh.trang_thai_bc.map((s) => <option key={s}>{s}</option>)}</select></div>
          <div><label htmlFor="loc-loai">Loại</label><select id="loc-loai" name="loai" defaultValue={f.loai} onChange={(e) => loc(e.target.form)}>
            <option value="">Tất cả</option>{d && d.ds_loai.map((l) => <option key={l.ma} value={l.ma}>{l.ten}</option>)}</select></div>
          <div><label htmlFor="loc-pb">Phường/xã</label><select id="loc-pb" name="dia_ban" defaultValue={f.dia_ban} onChange={(e) => loc(e.target.form)}>
            <option value="">Tất cả</option>{d && d.ds_dia_ban.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}</select></div>
          <div><label htmlFor="loc-tu">Từ ngày</label><input type="date" id="loc-tu" name="tu_ngay" defaultValue={f.tu_ngay} onChange={(e) => loc(e.target.form)} /></div>
          <div><label htmlFor="loc-den">Đến ngày</label><input type="date" id="loc-den" name="den_ngay" defaultValue={f.den_ngay} onChange={(e) => loc(e.target.form)} /></div>
        </div>
      </form>
      {d && d.loi && <div className="flash err">{d.loi}</div>}
      {d && (
        <>
          <table className="t"><tbody>
            <tr><th>Mã</th><th>Tóm tắt</th><th>Phường/xã</th><th>Loại</th><th>Ngày gửi</th><th>Trạng thái</th></tr>
            {d.ds.items.map((b) => (
              <tr key={b.ma} className={"click " + (ma === b.ma ? "sel" : "")} onClick={() => navigate(qs + "&trang=" + d.ds.trang + "&ma=" + b.ma)}>
                <td className="ma-bc">{b.ma_tra_cuu}</td><td>{b.mo_ta.slice(0, 70)}{b.mo_ta.length > 70 ? "…" : ""}</td>
                <td className="nw">{b.dia_ban}</td><td>{b.loai || ""}</td><td>{dt(b.ngay_gui)}</td><td><Tag s={b.trang_thai} /></td>
              </tr>
            ))}
            {d.ds.items.length === 0 && <tr><td colSpan={6} className="empty">Không có kết quả.</td></tr>}
          </tbody></table>
          <Pager ds={d.ds} coSo={qs} />
        </>
      )}
      {bc && (
        <>
          <div className="grid g2" style={{ marginTop: 16 }}>
            <div className="card"><div className="hd">Chi tiết {bc.ma_tra_cuu} <Tag s={bc.trang_thai} /></div><div className="bd">
              <BcInfo bc={bc} lienHe />
              {bc.ly_do_ket_thuc && <p className="small"><b>Lý do kết thúc:</b> {bc.ly_do_ket_thuc}</p>}
              <div style={{ margin: "8px 0" }}><BanDoDiem lat={bc.vi_do} lng={bc.kinh_do} /></div>
              <div className="gallery">{bc.minh_chung.map((m) => <Media key={m.ma} m={m} />)}</div>
              {bc.ban_cong_khai && <div className="flash ok small" style={{ marginTop: 10 }}><b>Bản công khai:</b> {bc.ban_cong_khai}</div>}
            </div></div>
            <div className="card"><div className="hd">Phân công</div><div className="bd">
              {bc.phan_cong.map((p) => (
                <div key={p.ma} style={{ marginBottom: 10 }}><b>PC-{p.ma}</b> · {p.don_vi} · giao {dt(p.ngay)} <Tag s={p.trang_thai} />
                  {p.nghiem_thu.map((n, i) => <div key={i} className="small">Duyệt kết quả {dt(n.thoi_gian)}: {n.ket_qua} {n.nhan_xet || ""}</div>)}</div>
              ))}
              {bc.phan_cong.length === 0 && <div className="small muted">Chưa phân công.</div>}
            </div></div>
          </div>
          <h2>Lịch sử trạng thái</h2><LichSu ds={bc.lich_su} />
        </>
      )}
    </>
  );
}

