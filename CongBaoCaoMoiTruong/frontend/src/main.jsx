import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { NenUngDung } from "./ung_dung.jsx";
import "./style.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <NenUngDung>
        <App />
      </NenUngDung>
    </BrowserRouter>
  </StrictMode>
);
