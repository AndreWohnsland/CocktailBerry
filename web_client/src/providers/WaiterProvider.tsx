import type React from 'react';
import { createContext, useContext, useEffect, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useCurrentWaiter, useWaiterWebSocket } from '../api/waiters';
import type { CurrentWaiterState } from '../types/models';
import { errorToast } from '../utils';
import { useConfig } from './ConfigProvider';

interface WaiterContextType {
  /** Merged WebSocket + HTTP waiter state, always the freshest available */
  waiterState: CurrentWaiterState | null;
  /** Whether the WebSocket connection is currently open */
  isConnected: boolean;
  /** Whether the initial HTTP fetch is still loading */
  isLoading: boolean;
}

const WaiterContext = createContext<WaiterContextType | undefined>(undefined);

export const WaiterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { config } = useConfig();
  const { t } = useTranslation();
  const enabled = Boolean(config.WAITER_MODE);

  // Single WebSocket connection for the entire app
  const { waiter: wsState, isConnected } = useWaiterWebSocket(enabled);
  // HTTP fallback for initial load / when WS hasn't connected yet
  const { data: httpWaiter, isLoading } = useCurrentWaiter(enabled);

  // Show a toast when a new NFC scan arrives but the tag is not registered
  const prevNfcIdRef = useRef<string | null | undefined>(undefined);
  useEffect(() => {
    if (wsState === null) {
      prevNfcIdRef.current = null;
      return;
    }
    if (wsState.nfc_id !== prevNfcIdRef.current && wsState.nfc_id !== null && wsState.waiter === null) {
      errorToast(t('waiter.nfcNotRegistered'));
    }
    prevNfcIdRef.current = wsState.nfc_id;
  }, [wsState, t]);

  // WebSocket takes priority, HTTP is fallback
  const waiterState: CurrentWaiterState | null = useMemo(() => {
    if (wsState) return wsState;
    if (httpWaiter) return { nfc_id: httpWaiter.nfc_id, waiter: httpWaiter };
    return null;
  }, [wsState, httpWaiter]);

  const contextValue = useMemo(() => ({ waiterState, isConnected, isLoading }), [waiterState, isConnected, isLoading]);

  return <WaiterContext.Provider value={contextValue}>{children}</WaiterContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useWaiter = () => {
  const context = useContext(WaiterContext);
  if (!context) {
    throw new Error('useWaiter must be used within a WaiterProvider');
  }
  return context;
};
