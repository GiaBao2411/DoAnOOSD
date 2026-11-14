import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { layDuLieu } from "./api.js";

const UngDung = createContext(null);
export const useUngDung = () => useContext(UngDung);

let soFlash = 0;

export function NenUngDung({ children }) {
  const [taiKhoan, datTaiKhoan] = useState(null);
  const [daTai, datDaTai] = useState(false);
  const [cauHinh, datCauHinh] = useState(null);
  const [flashes, datFlashes] = useState([]);
  const [lamMoi, datLamMoi] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();
  const viTri = useRef(location.key);

  useEffect(() => {
    layDuLieu("/api/toi")
      .then((d) => datTaiKhoan(d.tai_khoan))
      .catch(() => datTaiKhoan(null))
      .finally(() => datDaTai(true));
    layDuLieu("/api/cau-hinh").then(datCauHinh).catch(() => {});
  }, []);

  useEffect(() => {
    viTri.current = location.key;
    datFlashes((fs) => fs.filter((f) => f.loc === null || f.loc === location.key).map((f) => ({ ...f, loc: location.key })));
  }, [location.key]);

  const baoTaiCho = useCallback((noiDung, loai = "err") => {
    soFlash += 1;
    datFlashes([{ id: soFlash, loai, nd: noiDung, loc: viTri.current }]);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const xong = useCallback(
    (noiDung, url, loai = "ok", trangThai) => {
      soFlash += 1;
      datFlashes((fs) => [...fs, { id: soFlash, loai, nd: noiDung, loc: null }]);
      const hienTai = location.pathname + location.search;
      navigate(url || hienTai, { replace: !url || url === hienTai, state: trangThai });
      window.scrollTo({ top: 0 });
    },
    [location.pathname, location.search, navigate]
  );

  const lamMoiTrang = useCallback(() => datLamMoi((x) => x + 1), []);
  const giaTri = { taiKhoan, datTaiKhoan, daTai, cauHinh, flashes, baoTaiCho, xong, lamMoi, lamMoiTrang };
  return <UngDung.Provider value={giaTri}>{children}</UngDung.Provider>;
}

export function useTai(url) {
  const { lamMoi, datTaiKhoan } = useUngDung();
  const location = useLocation();
  const [trangThai, datTrangThai] = useState({ d: null, loi: null, dangTai: true, url: null });
  const [lan, datLan] = useState(0);
  useEffect(() => {
    if (!url) {
      datTrangThai({ d: null, loi: null, dangTai: false, url });
      return;
    }
    let huy = false;
    datTrangThai((t) => ({ ...t, dangTai: true }));
    layDuLieu(url)
      .then((d) => !huy && datTrangThai({ d, loi: null, dangTai: false, url }))
      .catch((e) => {
        if (huy) return;
        if (e.maHttp === 401) datTaiKhoan(null);
        datTrangThai({ d: null, loi: e, dangTai: false, url });
      });
    return () => {
      huy = true;
    };
  }, [url, location.key, lamMoi, lan, datTaiKhoan]);
  return { ...trangThai, taiLai: () => datLan((x) => x + 1) };
}
