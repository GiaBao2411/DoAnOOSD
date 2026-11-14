// Gọi API JSON của máy chủ FastAPI. Mọi lỗi máy chủ trả về dạng {"loi": "..."}.

export class LoiApi extends Error {
  constructor(thongBao, maHttp) {
    super(thongBao);
    this.maHttp = maHttp;
  }
}

async function docKetQua(r) {
  let d = null;
  try {
    d = await r.json();
  } catch {
    d = null;
  }
  if (!r.ok) throw new LoiApi((d && d.loi) || "Có lỗi xảy ra (mã " + r.status + ").", r.status);
  return d;
}

export async function layDuLieu(url) {
  let r;
  try {
    r = await fetch(url, { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } });
  } catch {
    throw new LoiApi("Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.", 0);
  }
  return docKetQua(r);
}

// Gửi dữ liệu form (kể cả tệp) bằng multipart/form-data, giống form HTML.
export async function guiForm(url, duLieu) {
  let body = duLieu;
  if (!(duLieu instanceof FormData)) {
    body = new FormData();
    Object.entries(duLieu || {}).forEach(([k, v]) => {
      if (Array.isArray(v)) v.forEach((x) => body.append(k, x));
      else if (v !== undefined && v !== null) body.append(k, v);
    });
  }
  let r;
  try {
    r = await fetch(url, { method: "POST", body, credentials: "same-origin", headers: { Accept: "application/json" } });
  } catch {
    throw new LoiApi("Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.", 0);
  }
  return docKetQua(r);
}

// Lấy dữ liệu form kèm giá trị của nút bấm đã gửi form (vd name="hanh_dong" value="duyet").
export function duLieuForm(e) {
  const fd = new FormData(e.target);
  const nut = e.nativeEvent && e.nativeEvent.submitter;
  if (nut && nut.name) fd.append(nut.name, nut.value);
  return fd;
}
