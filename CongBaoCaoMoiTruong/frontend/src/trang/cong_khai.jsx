import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { duLieuForm, guiForm } from "../api.js";
import { dt, dtInput, ngay } from "../dinh_dang.js";
import { BanDoChon, BanDoXem, escHtml, layViTri, rutGon, timDiaChi, timToaDo } from "../thanh_phan/ban_do.jsx";
import { BangLoc, ChonTep, Media, TieuDe } from "../thanh_phan/chung.jsx";
import { useTai, useUngDung } from "../ung_dung.jsx";

export function TrangChu() {
  const [q, datQ] = useSearchParams();
  const loai = q.get("loai") || "";
  const diaBan = q.get("dia_ban") || "";
  const t = useTai("/api/trang-chu?loai=" + encodeURIComponent(loai) + "&dia_ban=" + encodeURIComponent(diaBan));
  const d = t.d;
  const diem = d ? d.ds.filter((p) => p.lat !== null).map((p) => ({
    lat: p.lat, lng: p.lng,
    html: "<b>" + escHtml(p.tieu_de) + '</b><br><a href="/tra-cuu?ma=' + encodeURIComponent(p.ma_tra_cuu) + '">Xem ' + escHtml(p.ma_tra_cuu) + "</a>",
  })) : [];
  return (
    <>
      <TieuDe>Trang chủ — Cổng báo cáo sự cố môi trường</TieuDe>
      <section className="hero">
        <div>
          <h1>Thấy rác ùn ứ, khói đen hay nước thải đổ ra kênh? Báo cho phường xử lý.</h1>
          <div className="actions">
            <Link className="btn lg" to="/gui-bao-cao">Gửi báo cáo sự cố</Link>
            <Link className="btn sec lg" to="/tra-cuu">Tra cứu báo cáo</Link>
          </div>
        </div>
        <ol className="quy-trinh">
          <li><b>Bạn gửi báo cáo</b></li>
          <li><b>Cán bộ phường kiểm tra</b></li>
          <li><b>Đội xử lý đến hiện trường</b></li>
          <li><b>Kết quả được công khai</b></li>
        </ol>
      </section>

      <div className="ban-do-hd">
        <div><h2>Bản đồ sự cố đã xử lý</h2></div>
        <form className="row" onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.target);
          datQ({ loai: f.get("loai"), dia_ban: f.get("dia_ban") });
        }}>
          <div><label htmlFor="loc-loai">Loại sự cố</label>
            <select id="loc-loai" name="loai" defaultValue={loai} key={"l" + loai + (d ? 1 : 0)}>
              <option value="">Tất cả</option>
              {d && d.ds_loai.map((l) => <option key={l.ma} value={l.ma}>{l.ten}</option>)}
            </select></div>
          <div><label htmlFor="loc-pb">Phường/xã</label>
            <select id="loc-pb" name="dia_ban" defaultValue={diaBan} key={"d" + diaBan + (d ? 1 : 0)}>
              <option value="">Tất cả</option>
              {d && d.ds_dia_ban.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}
            </select></div>
          <div className="fit"><button className="btn">Lọc</button></div>
        </form>
      </div>
      {d && <BanDoXem id="map" diem={diem} zoom={12} />}
      {!d && <div className="map"></div>}

      <h2>Kết quả xử lý gần đây</h2>
      {d && (d.ds.length ? (
        <BangLoc
          dau={<tr><th>Mã báo cáo</th><th>Kết quả</th><th>Loại sự cố</th><th>Phường/xã</th><th className="num">Ngày công khai</th></tr>}
          dong={d.ds.map((b) => ({
            key: b.ma_tra_cuu, chu: [b.ma_tra_cuu, b.tieu_de, b.loai, b.dia_ban, ngay(b.ngay)].join(" "),
            el: (<tr key={b.ma_tra_cuu}><td><Link to={"/tra-cuu?ma=" + b.ma_tra_cuu}>{b.ma_tra_cuu}</Link></td><td>{b.tieu_de}</td>
              <td>{b.loai}</td><td>{b.dia_ban}</td><td className="num">{ngay(b.ngay)}</td></tr>),
          }))}
        />
      ) : <div className="empty card">Chưa có sự cố nào được công khai.</div>)}
    </>
  );
}

export function GuiBaoCao() {
  const { cauHinh, baoTaiCho } = useUngDung();
  const [ketQua, datKetQua] = useState(null);
  const [xem, datXem] = useState([]);
  const [viDo, datViDo] = useState("");
  const [kinhDo, datKinhDo] = useState("");
  const [ghiChu, datGhiChu] = useState("");
  const [lan, datLan] = useState(0);
  const [dangGui, datDangGui] = useState(false);
  const banDo = useRef(null);
  const diaChi = useRef(null);
  const phuong = useRef(null);
  const tim = useRef({ hen: null, daTim: "", luot: 0, tuDien: "", henNguoc: null });

  if (ketQua) return <GuiThanhCong kq={ketQua} />;
  if (!cauHinh) return null;

  const bao = (s) => datGhiChu(s);
  function tenPhuong() {
    const w = phuong.current;
    return w && w.value ? w.options[w.selectedIndex].text.trim() : "";
  }
  function chonPhuong(kq) {
    const w = phuong.current;
    if (!w || w.value) return;
    const ten = (kq.display_name || "").split(",").map((s) => s.trim().toLowerCase());
    const opt = [...w.options].find((o) => o.value && ten.includes(o.text.trim().toLowerCase()));
    if (opt) w.value = opt.value;
  }
  function datDiem(lat, lng) {
    datViDo((+lat).toFixed(6));
    datKinhDo((+lng).toFixed(6));
  }
  function khiChon(lat, lng) {
    datDiem(lat, lng);
    const s = tim.current;
    s.luot++;
    clearTimeout(s.hen);
    clearTimeout(s.henNguoc);
    bao("");
    const toi = s.luot;
    s.henNguoc = setTimeout(async () => {
      try {
        const kq = await timDiaChi(lat, lng);
        if (toi !== s.luot || !kq) return;
        const dc = rutGon(kq);
        const dangGo = diaChi.current.value.trim();
        chonPhuong(kq);
        if (!dangGo || dangGo === s.tuDien) {
          diaChi.current.value = dc;
          s.tuDien = dc;
          s.daTim = dc + "|" + tenPhuong();
        }
      } catch {  }
    }, 500);
  }
  async function timTheoDiaChi() {
    const s = tim.current;
    const dc = diaChi.current.value.trim();
    if (dc.length < 4 || !banDo.current) return;
    const tp = tenPhuong();
    const khoa = dc + "|" + tp;
    if (khoa === s.daTim) return;
    s.daTim = khoa;
    const toi = ++s.luot;
    bao("");
    const cach = [];
    if (tp) cach.push(dc + ", " + tp + ", Thành phố Hồ Chí Minh");
    cach.push(dc + ", Thành phố Hồ Chí Minh", dc);
    try {
      for (let i = 0; i < cach.length; i++) {
        if (i) await new Promise((r) => setTimeout(r, 1100));
        if (toi !== s.luot) return;
        const kq = await timToaDo(cach[i], banDo.current.tam());
        if (toi !== s.luot) return;
        if (kq) {
          banDo.current.dat(kq.lat, kq.lon);
          datDiem(kq.lat, kq.lon);
          chonPhuong(kq);
          banDo.current.toi(kq.lat, kq.lon);
          return;
        }
      }
      bao("Không tìm thấy địa chỉ này trên bản đồ. Hãy bấm lên bản đồ để đặt ghim.");
    } catch {
      if (toi === s.luot) bao("Không tìm được địa chỉ (kiểm tra Internet). Hãy bấm lên bản đồ để đặt ghim.");
    }
  }
  function henTim(ngay_) {
    clearTimeout(tim.current.hen);
    tim.current.hen = setTimeout(timTheoDiaChi, ngay_ ? 0 : 1000);
  }

  async function gui(e) {
    e.preventDefault();
    datDangGui(true);
    try {
      datKetQua(await guiForm("/api/bao-cao", duLieuForm(e)));
      window.scrollTo({ top: 0 });
    } catch (loi) {
      baoTaiCho(loi.message);
    } finally {
      datDangGui(false);
    }
  }

  return (
    <>
      <TieuDe>Gửi báo cáo sự cố</TieuDe>
      <h1>Gửi báo cáo sự cố môi trường</h1>
      <form onSubmit={gui} key={lan}>
        <div className="grid g2">
          <div className="card"><div className="hd">1. Nội dung sự cố</div><div className="bd">
            <label>Mô tả sự cố <span className="req">*</span></label>
            <textarea name="mo_ta" required></textarea>
            <div className="row">
              <div><label>Thời gian phát hiện <span className="req">*</span></label>
                <input type="datetime-local" name="thoi_gian_phat_hien" required defaultValue={dtInput(cauHinh.bay_gio)} /></div>
              <div><label>Phường/xã <span className="req">*</span></label>
                <select name="ma_dia_ban" required ref={phuong} defaultValue=""
                  onChange={() => { if (diaChi.current.value.trim()) { tim.current.daTim = ""; henTim(true); } }}>
                  <option value="">— Chọn —</option>
                  {cauHinh.ds_dia_ban.map((x) => <option key={x.ma} value={x.ma}>{x.ten}</option>)}
                </select></div>
            </div>
            <label>Địa chỉ / mô tả vị trí</label>
            <input type="text" id="dia_chi" name="dia_chi" autoComplete="off" ref={diaChi}
              onInput={() => henTim(false)} onBlur={() => henTim(true)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); henTim(true); } }} />
          </div></div>
          <div className="card"><div className="hd">2. Vị trí trên bản đồ</div><div className="bd">
            <BanDoChon ref={banDo} lat0={cauHinh.map_lat} lng0={cauHinh.map_lng} onChon={khiChon} />
            <div className="row small" style={{ marginTop: 6 }}>
              <div><label>Vĩ độ</label><input type="text" id="vi_do" name="vi_do" value={viDo} readOnly /></div>
              <div><label>Kinh độ</label><input type="text" id="kinh_do" name="kinh_do" value={kinhDo} readOnly /></div>
              <div style={{ flex: 0 }}><button type="button" className="btn sec" onClick={() => layViTri((lat, lng) => {
                banDo.current.dat(lat, lng);
                banDo.current.toi(lat, lng);
                khiChon(lat, lng);
              }, bao)}>Lấy vị trí hiện tại</button></div>
            </div>
            <div className="small muted" id="gps">{ghiChu}</div>
          </div></div>
        </div>
        <div className="card"><div className="hd">3. Bằng chứng</div><div className="bd">
          <ChonTep xem={xem} datXem={datXem} />
        </div></div>
        <div className="card"><div className="hd">4. Thông tin liên hệ</div><div className="bd">
          <div className="row">
            <div><label>Họ tên</label><input type="text" name="ho_ten" /></div>
            <div><label>Số điện thoại</label><input type="text" name="so_dien_thoai" /></div>
          </div>
          <label htmlFor="email">Email nhận mã báo cáo</label>
          <input type="email" id="email" name="email" autoComplete="email" inputMode="email" />
        </div></div>
        <div className="actions">
          <button className="btn" disabled={dangGui}>{dangGui ? "Đang gửi…" : "Gửi báo cáo"}</button>
          <button type="button" className="btn sec" onClick={() => { datLan(lan + 1); datXem([]); datViDo(""); datKinhDo(""); datGhiChu(""); }}>Làm mới</button>
        </div>
      </form>
    </>
  );
}

function GuiThanhCong({ kq }) {
  return (
    <>
      <TieuDe>Đã gửi báo cáo</TieuDe>
      <h1>Gửi báo cáo thành công</h1>
      <div className="card"><div className="bd">
        <div className="row" style={{ maxWidth: 640 }}>
          <div><div className="muted small">Mã báo cáo</div><div className="big-code" id="ma">{kq.ma_tra_cuu}</div></div>
        </div>
        {kq.email && kq.mail_bat && (
          <div className="flash ok" style={{ marginTop: 14 }} id="da-gui-mail">Mã báo cáo đang được gửi tới <b>{kq.email}</b>. Thư có thể đến sau 1–2 phút; nếu không thấy, hãy xem thêm mục Thư rác (Spam).</div>
        )}
        {kq.email && !kq.mail_bat && (
          <div className="flash err" style={{ marginTop: 14 }}>Hệ thống chưa bật gửi email nên chưa gửi được mã tới <b>{kq.email}</b>. Hãy ghi lại mã ở trên.</div>
        )}
        <div className="actions"><Link className="btn" to={"/tra-cuu?ma=" + kq.ma_tra_cuu}>Tra cứu báo cáo này</Link><Link className="btn sec" to="/">Về trang chủ</Link></div>
      </div></div>
    </>
  );
}

export function QuenMa() {
  const [daGui, datDaGui] = useState(null);
  const [loi, datLoi] = useState(null);
  const [lan, datLan] = useState(0);
  async function gui(e) {
    e.preventDefault();
    try {
      const d = await guiForm("/api/quen-ma", new FormData(e.target));
      datDaGui(d.email);
      datLoi(null);
    } catch (x) {
      datLoi(x.message);
    }
  }
  return (
    <>
      <TieuDe>Lấy lại mã báo cáo</TieuDe>
      <h1>Lấy lại mã báo cáo</h1>
      <div className="card" style={{ maxWidth: 640 }}><div className="bd">
        {daGui ? (
          <>
            <div className="flash ok" id="da-gui">Nếu <b>{daGui}</b> đã được dùng khi gửi báo cáo, danh sách mã báo cáo sẽ được gửi vào hộp thư này trong vài phút. Hãy xem cả mục Thư rác (Spam).</div>
            <div className="actions"><Link className="btn" to="/tra-cuu">Đến trang tra cứu</Link>
              <button type="button" className="btn sec" onClick={() => { datDaGui(null); datLan(lan + 1); }}>Nhập email khác</button></div>
          </>
        ) : (
          <>
            {loi && <div className="flash err">{loi}</div>}
            <form onSubmit={gui} key={lan}>
              <label htmlFor="email">Email đã dùng khi gửi báo cáo <span className="req">*</span></label>
              <input type="email" id="email" name="email" required autoComplete="email" inputMode="email" />
              <div className="actions"><button className="btn">Gửi lại mã vào email</button></div>
            </form>
          </>
        )}
      </div></div>
    </>
  );
}

export function TraCuu() {
  const [q] = useSearchParams();
  const navigate = useNavigate();
  const ma = q.get("ma") || "";
  const t = useTai(ma ? "/api/tra-cuu?ma=" + encodeURIComponent(ma) : null);
  const kq = t.d && t.url && t.url.endsWith(encodeURIComponent(ma)) ? t.d : null;
  return (
    <>
      <TieuDe>Tra cứu báo cáo</TieuDe>
      <h1>Tra cứu báo cáo</h1>
      <form className="row" style={{ maxWidth: 640 }} onSubmit={(e) => {
        e.preventDefault();
        navigate("/tra-cuu?ma=" + encodeURIComponent(new FormData(e.target).get("ma").trim()));
      }}>
        <div><label htmlFor="ma">Mã báo cáo <span className="req">*</span></label>
          <input type="text" id="ma" name="ma" defaultValue={ma} key={ma} required /></div>
        <div className="fit"><button className="btn">Tra cứu</button></div>
      </form>
      <p style={{ marginTop: 8 }}><Link to="/quen-ma">Quên mã báo cáo? Gửi lại vào email</Link></p>
      {ma && t.loi && <div className="flash err">{t.loi.message}</div>}
      {kq && (
        <>
          <div className="card" style={{ marginTop: 18 }}>
            <div className="hd">Báo cáo {kq.ma_tra_cuu} <span className="small muted">Cập nhật lần cuối {dt(kq.cap_nhat_cuoi)}</span></div>
            <div className="bd">
              {kq.ket_thuc ? (
                <div className="flash err"><b>{kq.trang_thai}.</b> {kq.ly_do_ket_thuc || ""}</div>
              ) : (
                <div className="steps">
                  {kq.buoc.map((s, i) => (
                    <div key={s} className={"st " + (i <= kq.buoc_hien_tai ? "done " : "") + (i === kq.buoc_hien_tai ? "cur" : "")}><i></i>{s}</div>
                  ))}
                </div>
              )}
              <dl className="meta"><dt>Trạng thái</dt><dd><b>{kq.ket_thuc ? kq.trang_thai : kq.trang_thai_hien_thi}</b></dd>
                <dt>Ngày gửi</dt><dd>{dt(kq.ngay_gui)}</dd><dt>Phường/xã</dt><dd>{kq.dia_ban}</dd></dl>
            </div>
          </div>
          {kq.cong_khai && (
            <div className="card"><div className="hd">Kết quả xử lý đã công khai</div><div className="bd">
              <h2 style={{ marginTop: 0 }}>{kq.cong_khai.tieu_de}</h2>
              <div style={{ whiteSpace: "pre-line" }}>{kq.cong_khai.noi_dung}</div>
              <p className="small muted" style={{ margin: "8px 0 14px" }}>{kq.loai}, công khai ngày {ngay(kq.cong_khai.ngay)}</p>
              <div className="gallery">{kq.anh.map((a) => <Media key={a.bang + a.ma} m={{ bang: a.bang, ma: a.ma, loai: a.loai, ten: "" }} nhan={a.nhan} />)}</div>
            </div></div>
          )}
          {kq.cho_bo_sung && (
            <div className="flash warn">Cán bộ đang chờ người gửi bổ sung thông tin. Nếu bạn là người gửi, vào <Link to="/bo-sung">Bổ sung thông tin</Link> và nhập mã báo cáo.</div>
          )}
        </>
      )}
    </>
  );
}

export function BoSung() {
  const { xong, baoTaiCho } = useUngDung();
  const t = useTai("/api/bo-sung");
  const [xem, datXem] = useState([]);
  useEffect(() => datXem([]), [t.d]);
  if (!t.d) return null;
  const { bc, yc } = t.d;
  async function goi(url, du) {
    try {
      const d = await guiForm(url, du);
      xong(d.thong_bao || "", "/bo-sung");
    } catch (e) {
      baoTaiCho(e.message);
    }
  }
  return (
    <>
      <TieuDe>Bổ sung thông tin</TieuDe>
      <h1>Bổ sung thông tin cho báo cáo</h1>
      {!bc ? (
        <div className="card" style={{ maxWidth: 640 }}><div className="hd">Bước 1. Nhập mã báo cáo</div><div className="bd">
          <form onSubmit={(e) => { e.preventDefault(); goi("/api/bo-sung/xac-minh", new FormData(e.target)); }}>
            <label htmlFor="ma">Mã báo cáo <span className="req">*</span></label><input type="text" id="ma" name="ma" required />
            <div className="actions"><button className="btn">Tìm báo cáo</button><Link className="btn sec" to="/quen-ma">Quên mã báo cáo?</Link></div>
          </form>
        </div></div>
      ) : (
        <>
          <div className="flash ok">Đang bổ sung cho báo cáo <b>{bc.ma_tra_cuu}</b> — trạng thái: <b>{bc.trang_thai}</b>.{" "}
            <form className="inline" onSubmit={(e) => { e.preventDefault(); goi("/api/bo-sung/thoat", {}); }}><button className="btn sec sm">Thoát</button></form></div>
          {yc ? (
            <>
              <div className="card"><div className="hd">Bước 2. Nội dung cán bộ yêu cầu</div><div className="bd">
                <p style={{ fontStyle: "italic" }}>“{yc.noi_dung}”</p>
                <p className="small">Yêu cầu lúc {dt(yc.ngay)} · <b className="c-danger">Hạn bổ sung: {dt(yc.han)}</b></p>
              </div></div>
              {yc.con_han ? (
                <div className="card"><div className="hd">Bước 3. Gửi bổ sung</div><div className="bd">
                  <form onSubmit={(e) => { e.preventDefault(); goi("/api/bo-sung/gui", new FormData(e.target)); }}>
                    <label>Nội dung bổ sung <span className="req">*</span></label><textarea name="noi_dung" required></textarea>
                    <label>Tệp bổ sung (không bắt buộc)</label>
                    <ChonTep xem={xem} datXem={datXem} />
                    <div className="actions"><button className="btn">Gửi bổ sung</button></div>
                  </form>
                </div></div>
              ) : (
                <div className="flash err">Yêu cầu bổ sung đã quá hạn. Bạn có thể <Link to="/gui-bao-cao">gửi báo cáo mới</Link>.</div>
              )}
            </>
          ) : (
            <div className="flash info">Báo cáo này hiện không có yêu cầu bổ sung nào đang chờ. Xem tiến độ tại <Link to={"/tra-cuu?ma=" + bc.ma_tra_cuu}>Tra cứu</Link>.</div>
          )}
        </>
      )}
    </>
  );
}
