import axios from 'axios';

const axiosInstance = axios.create();

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
export const API_URL = `${import.meta.env.VITE_APP_API_URL || 'http://localhost:8000'}`;
