import axios from "axios";
import { useInactivityLock } from "../composables/useInactivityLock";

const rawBaseURL = (import.meta as any).env?.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/";
const normalizedBaseURL = rawBaseURL.endsWith("/") ? rawBaseURL : `${rawBaseURL}/`;

const api = axios.create({
  baseURL: normalizedBaseURL,
  withCredentials: true, // Required: sends HttpOnly refresh cookie automatically
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Do not attempt token refresh for login/auth endpoints
    if (originalRequest.url?.includes('auth/login') || originalRequest.url?.includes('auth/token/refresh')) {
      return Promise.reject(error);
    }

    // Check if error is 401 Unauthorized and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Refresh token is sent automatically via HttpOnly cookie (withCredentials)
        const refreshUrl = `${normalizedBaseURL}auth/token/refresh/`;
        const res = await axios.post(refreshUrl, {}, { withCredentials: true });

        const newAccess = res.data.access;
        localStorage.setItem("access", newAccess);

        api.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;

        processQueue(null, newAccess);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;

        const { checkInactivityExpired, lockSession } = useInactivityLock();
        const userExists = Boolean(localStorage.getItem("user"));

        if (userExists && checkInactivityExpired()) {
          // If inactivity limit (15 mins) has passed, trigger lock screen instead of hard logout
          lockSession();
        } else if (userExists) {
          // If user exists and is active but refresh failed, trigger lock session to re-authenticate cleanly
          lockSession();
        } else {
          // No user session stored, redirect to login
          localStorage.removeItem("access");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;