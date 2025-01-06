import axios from 'axios';

export const API_URL = `${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000/api'}`;

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
    if (error?.response?.data !== undefined) {
      // Reformat the error message to include response data
      return Promise.reject(error.response.data);
    }
    return Promise.reject(error);
  },
);

export { axiosInstance };
