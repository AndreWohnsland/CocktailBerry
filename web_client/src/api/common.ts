import axios from 'axios';

export const API_URL = `${import.meta.env.VITE_APP_API_URL ?? 'http://localhost:8000/api'}`;

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
    // Only unwrap structured API errors. A gateway that cannot reach the backend answers
    // with an HTML page, which must not end up in a toast as the error message.
    if (typeof error?.response?.data === 'object' && error.response.data !== null) {
      return Promise.reject(error.response.data);
    }
    return Promise.reject(error);
  },
);

export { axiosInstance };
