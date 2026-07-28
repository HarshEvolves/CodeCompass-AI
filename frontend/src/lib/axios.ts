/**
 * CodeCompass — Axios API Client
 *
 * A pre-configured Axios instance for all API calls.
 * - Sets the base URL so you write api.get("/health") instead of the full URL
 * - Will auto-attach JWT tokens in Phase 2 (auth)
 * - Handles 401 errors globally
 *
 * Usage:
 *   import api from "@/lib/axios";
 *   const res = await api.get("/health");
 *   console.log(res.data);  // { status: "healthy", ... }
 */

import axios from "axios";

const api = axios.create({
  // Vite's dev proxy forwards "/api" → "http://localhost:8000/api"
  // so we only need the path prefix here.
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 10000,
});

// ─── Request Interceptor ──────────────────────────────────────
// Runs BEFORE every request. Attaches JWT token if logged in.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ─────────────────────────────────────
// Runs AFTER every response. Handles auth errors globally.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
