// Định dạng ngày giờ và số. Máy chủ trả thời gian dạng "YYYY-MM-DDTHH:MM:SS" (giờ Việt Nam, không múi giờ).

const NBSP = " ";

export function dt(s) {
  if (!s) return "";
  // khoảng trắng không ngắt dòng để ngày và giờ luôn nằm trên một dòng trong bảng
  return s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4) + NBSP + s.slice(11, 16);
}

export function ngay(s) {
  if (!s) return "";
  return s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4);
}

export function dtGiay(s) {
  if (!s) return "";
  return s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4) + " " + s.slice(11, 19);
}

export function dtNgan(s) {
  // "12/11 21:05:07"
  if (!s) return "";
  return s.slice(8, 10) + "/" + s.slice(5, 7) + " " + s.slice(11, 19);
}

export function dtInput(s) {
  return s ? s.slice(0, 16) : "";
}

export function gio(s) {
  return s ? s.slice(11, 16) : "";
}

export function giay(s) {
  // số giây kể từ mốc, để so sánh hai thời điểm cùng múi giờ
  return s ? Date.parse(s.slice(0, 19) + "Z") / 1000 : 0;
}

export function so0(v) {
  return v === null || v === undefined ? "" : Math.round(v).toString();
}

export function so1(v) {
  return v === null || v === undefined ? "" : Number(v).toFixed(1);
}

export const THU = ["Chủ nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

export function thuNgay(s) {
  if (!s) return "";
  const d = new Date(Date.parse(s.slice(0, 10) + "T00:00:00Z"));
  return THU[d.getUTCDay()] + ", " + ngay(s);
}

export function boDau(s) {
  return (s || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}
