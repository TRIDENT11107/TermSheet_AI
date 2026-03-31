import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/predict": "http://127.0.0.1:5000",
      "/health": "http://127.0.0.1:5000",
      "/model": "http://127.0.0.1:5000",
      "/supported-types": "http://127.0.0.1:5000",
    },
  },
});
