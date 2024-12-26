import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { ConfigProvider } from './ConfigProvider.tsx';
import { AuthProvider } from './AuthProvider.tsx';
import { BrowserRouter } from 'react-router-dom';
import { CustomColorProvider } from './CustomColorProvider.tsx';
// import { I18nextProvider } from 'react-i18next';
import './i18n';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        {/* <I18nextProvider i18n={i18n}> */}
        <ConfigProvider>
          <CustomColorProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </CustomColorProvider>
        </ConfigProvider>
        {/* </I18nextProvider> */}
        {import.meta.env.VITE_APP_DEV === 'true' && <ReactQueryDevtools initialIsOpen={false} />}
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
