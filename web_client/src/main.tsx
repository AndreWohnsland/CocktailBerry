import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import { AuthProvider } from './AuthProvider.tsx';
import { ConfigProvider } from './ConfigProvider.tsx';
import { CustomColorProvider } from './CustomColorProvider.tsx';
import './i18n';
import './index.css';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <ConfigProvider>
          <CustomColorProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </CustomColorProvider>
        </ConfigProvider>
        {import.meta.env.VITE_APP_DEV === 'true' && <ReactQueryDevtools initialIsOpen={false} />}
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
