import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor: attach JWT bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: standardize error format
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // Server responded with an error status (4xx, 5xx)
      const data = error.response.data;
      const status = error.response.status;

      if (status === 401 && !error.config.url.includes('/auth/login') && !error.config.url.includes('/auth/register')) {
        // Token invalid or expired: clear stale credentials
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }

      const formattedError = {
        status,
        code: data?.error?.code || 'ERROR',
        message: data?.error?.message || data?.message || error.message || 'An unexpected error occurred',
      };
      return Promise.reject(formattedError);
    } else if (error.request) {
      // Backend server unavailable / Network error
      return Promise.reject({
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to Flask API server. Please ensure the backend is running at ' + API_BASE_URL,
      });
    } else {
      return Promise.reject({
        status: -1,
        code: 'CLIENT_ERROR',
        message: error.message,
      });
    }
  }
);

export default api;
