import { useEffect } from 'react';
import { axiosInstance } from '../api/common';
import { useAuth } from '../AuthProvider';

const useAxiosInterceptors = () => {
  const { makerPassword, masterPassword } = useAuth();

  useEffect(() => {
    const requestInterceptor = axiosInstance.interceptors.request.use(
      (config) => {
        if (makerPassword) {
          config.headers['x-maker-key'] = makerPassword;
        }

        if (masterPassword) {
          config.headers['x-master-key'] = masterPassword;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      },
    );

    return () => {
      axiosInstance.interceptors.request.eject(requestInterceptor);
    };
  }, [makerPassword, masterPassword]);
};

export default useAxiosInterceptors;
