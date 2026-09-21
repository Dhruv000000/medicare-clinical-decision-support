import axios from "axios";

export const ACCESS_TOKEN_KEY = "medicare_access_token";
export const REFRESH_TOKEN_KEY = "medicare_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access, refresh) {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  }
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem("medicare-demo-user");
  localStorage.removeItem("manus-runtime-user-info");
}

const baseURL =
  import.meta.env.VITE_API_URL ||
  "https://medicare-clinical-decision-support.onrender.com/api/v1/";

const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

// Request interceptor to attach JWT access token
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with queued refresh token handling
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
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

    // Avoid infinite retry loops on auth endpoints
    const isAuthUrl =
      originalRequest?.url?.includes("/auth/login/") ||
      originalRequest?.url?.includes("/auth/token/refresh/") ||
      originalRequest?.url?.includes("/auth/register/");

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthUrl) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        isRefreshing = false;
        clearTokens();
        window.dispatchEvent(new CustomEvent("medicare-auth-expired"));
        return Promise.reject(error);
      }

      try {
        // Direct axios call without interceptor to prevent recursion
        const refreshUrl = baseURL.endsWith("/")
          ? `${baseURL}auth/token/refresh/`
          : `${baseURL}/auth/token/refresh/`;

        const { data } = await axios.post(refreshUrl, { refresh: refreshToken });
        const newAccessToken = data.access;
        const newRefreshToken = data.refresh;

        setTokens(newAccessToken, newRefreshToken);
        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.dispatchEvent(new CustomEvent("medicare-auth-expired"));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
