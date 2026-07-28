import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      // Lets you write: import X from "@/lib/axios"
      // Instead of:     import X from "../../lib/axios"
      "@": path.resolve(__dirname, "./src"),
    },
  },

  server: {
    port: 5173,
    // Forward /api requests to the backend during development.
    // This avoids CORS issues when calling the API from the browser.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
