import axios from "axios";

let configuredBaseURL = import.meta.env.VITE_API_BASE_URL || "";
if (configuredBaseURL.endsWith("/")) {
  configuredBaseURL = configuredBaseURL.slice(0, -1);
}
// Automatically guarantee `/api/v1` is appended to the base URL in production if not present
if (!configuredBaseURL.endsWith("/api/v1")) {
  configuredBaseURL = configuredBaseURL ? `${configuredBaseURL}/api/v1` : "/api/v1";
}

const api = axios.create({
  baseURL: configuredBaseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 300000,
});

// Request Interceptor: Attach JWT Token automatically if exists
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

// Response Interceptor: Catch expired or unauthorized sessions and redirect
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Prevent infinite redirect loops if already on login page
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
