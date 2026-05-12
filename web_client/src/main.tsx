import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { BrowserRouter } from 'react-router';
import App from './App.tsx';
import './i18n';
import './index.css';
import { AuthProvider } from './providers/AuthProvider.tsx';
import { ConfigProvider } from './providers/ConfigProvider.tsx';
import { CustomColorProvider } from './providers/CustomColorProvider.tsx';
import { RestrictedModeProvider } from './providers/RestrictedModeProvider.tsx';
import { WaiterProvider } from './providers/WaiterProvider.tsx';

const queryClient = new QueryClient();

const root = document.getElementById('root');

if (!root) {
  throw new Error('Failed to find the root element');
}

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider>
          <CustomColorProvider>
            <RestrictedModeProvider>
              <WaiterProvider>
                <AuthProvider>
                  <App />
                </AuthProvider>
              </WaiterProvider>
            </RestrictedModeProvider>
          </CustomColorProvider>
        </ConfigProvider>
        {import.meta.env.VITE_APP_DEV === 'true' && <ReactQueryDevtools initialIsOpen={false} />}
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
