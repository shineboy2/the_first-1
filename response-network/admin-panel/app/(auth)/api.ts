// api.ts
import axios from "axios";

// Get API URL from environment or use default
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Accept": "application/json",
  },
  // Add timeout
  timeout: 10000,
  // Ensure we have proper CORS behavior
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

// Add request interceptor to attach token and logging
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage (Zustand persist storage)
    if (typeof window !== "undefined") {
      try {
        const authStorage = localStorage.getItem("auth-storage");
        if (authStorage) {
          const parsed = JSON.parse(authStorage);
          const token = parsed.state?.token;

          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
      } catch (error) {
        console.error("Error reading token from storage:", error);
      }
    }

    // Development logging
    if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
      console.log("API Request:", {
        url: config.url,
        baseURL: config.baseURL,
        method: config.method,
        headers: config.headers,
        withCredentials: config.withCredentials,
        timeout: config.timeout,
        data: config.data,
      });
    }

    return config;
  }
);

api.interceptors.response.use(
  (response) => {
    if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
      console.log("Response:", {
        status: response.status,
        data: response.data,
        headers: response.headers,
      });
    }
    return response;
  },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (error: any) => {
    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        // Clear auth storage
        localStorage.removeItem("auth-storage");

        // Clear auth-token cookie
        document.cookie = "auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

        // Redirect to login if not already there
        const currentPath = window.location.pathname;
        if (!currentPath.includes("/login")) {
          window.location.href = "/login";
        }
      }
    }

    // Pass through the error
    return Promise.reject(error);
  }
);

export default api;