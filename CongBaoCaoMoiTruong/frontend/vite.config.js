import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Khi phát triển (npm run dev, cổng 5173): chuyển các yêu cầu /api và /tep sang máy chủ FastAPI ở cổng 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": "http://localhost:8000",
      "/tep": "http://localhost:8000",
    },
  },
  build: { outDir: "dist", chunkSizeWarningLimit: 900 },
});
