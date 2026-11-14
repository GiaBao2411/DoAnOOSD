import { useEffect, useImperativeHandle, useRef, forwardRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl });

function nen(map) {
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }).addTo(map);
}

export function BanDoXem({ diem, zoom = 12, className = "map", id }) {
  const ref = useRef(null);
  const khoa = JSON.stringify(diem);
  useEffect(() => {
    const pts = JSON.parse(khoa);
    const map = L.map(ref.current).setView(pts.length ? [pts[0].lat, pts[0].lng] : [10.75, 106.65], zoom);
    nen(map);
    const b = [];
    pts.forEach((p) => {
      const m = L.marker([p.lat, p.lng]).addTo(map);
      if (p.html) m.bindPopup(p.html);
      b.push([p.lat, p.lng]);
    });
    if (b.length > 1) map.fitBounds(b, { padding: [30, 30] });
    return () => map.remove();
  }, [khoa, zoom]);
  return <div ref={ref} id={id} className={className}></div>;
}

export function BanDoDiem({ lat, lng, className = "map sm" }) {
  if (lat === null || lat === undefined || lng === null || lng === undefined) return null;
  return <BanDoXem diem={[{ lat, lng }]} zoom={15} className={className} />;
}

export function escHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export const BanDoChon = forwardRef(function BanDoChon({ lat0, lng0, onChon, className = "map sm" }, ref) {
  const el = useRef(null);
  const st = useRef({ map: null, mk: null });
  const goi = useRef(onChon);
  goi.current = onChon;

  useEffect(() => {
    const map = L.map(el.current).setView([lat0, lng0], 12);
    nen(map);
    st.current.map = map;
    map.on("click", (e) => {
      dat(e.latlng.lat, e.latlng.lng);
      goi.current && goi.current(e.latlng.lat, e.latlng.lng, true);
    });
    return () => {
      map.remove();
      st.current = { map: null, mk: null };
    };
  }, []);

  function dat(lat, lng) {
    const s = st.current;
    if (!s.map) return;
    lat = +lat;
    lng = +lng;
    if (s.mk) s.mk.setLatLng([lat, lng]);
    else {
      s.mk = L.marker([lat, lng], { draggable: true }).addTo(s.map);
      s.mk.on("dragend", () => {
        const p = s.mk.getLatLng();
        goi.current && goi.current(p.lat, p.lng, true);
      });
    }
  }

  useImperativeHandle(ref, () => ({
    dat,
    toi: (lat, lng, z = 17) => st.current.map && st.current.map.setView([+lat, +lng], z),
    tam: () => (st.current.map ? st.current.map.getCenter() : { lat: lat0, lng: lng0 }),
  }));

  return <div ref={el} className={className}></div>;
});

export function layViTri(xong, loi) {
  if (!navigator.geolocation) {
    loi("Trình duyệt không hỗ trợ định vị.");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (p) => xong(p.coords.latitude, p.coords.longitude),
    () => loi("Không lấy được vị trí (chưa cho phép hoặc không có GPS).")
  );
}

export async function timToaDo(q, tam) {
  const url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=vn&accept-language=vi" +
    "&viewbox=" + [tam.lng - 0.4, tam.lat + 0.4, tam.lng + 0.4, tam.lat - 0.4].join(",") + "&q=" + encodeURIComponent(q);
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const ds = await r.json();
  return ds.length ? ds[0] : null;
}

export async function timDiaChi(lat, lng) {
  const r = await fetch("https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=18&accept-language=vi&lat=" + lat + "&lon=" + lng,
    { headers: { Accept: "application/json" } });
  const kq = r.ok ? await r.json() : null;
  return kq && !kq.error ? kq : null;
}

export function rutGon(kq) {
  const ds = (kq.display_name || "").split(",").map((s) => s.trim()).filter((s) => s && s !== "Việt Nam" && !/^\d{5,6}$/.test(s));
  for (let i = 0; i < ds.length - 1; i++) {
    if (/^\d+[\w/-]*$/.test(ds[i])) {
      ds[i + 1] = ds[i] + " " + ds[i + 1];
      ds.splice(i, 1);
    }
  }
  return ds.join(", ");
}
