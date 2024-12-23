import axios from 'axios';

export const API_URL = `${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000'}`;

const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

// Add a response interceptor to process errors globally
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.data && error.response.data.detail) {
      // Reformat the error message to include response data
      return Promise.reject(new Error(error.response.data.detail));
    }
    return Promise.reject(error);
  },
);

export { axiosInstance };
