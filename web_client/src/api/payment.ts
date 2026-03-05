import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Cocktail, PaymentUserData, PaymentUserUpdate } from '../types/models';
import { errorToast } from '../utils';
import { API_URL } from './common';

const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 16_000;

export const usePaymentWebSocket = (enabled: boolean) => {
  const [user, setUser] = useState<PaymentUserData | null>(null);
  const [cocktails, setCocktails] = useState<Cocktail[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const { t } = useTranslation();

  // Track previous user UID to detect changes
  const prevUserUidRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      // Reset state when disabled - this runs as a side effect, not during render
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUser(null);
      setCocktails([]);
      setIsConnected(false);
      prevUserUidRef.current = null;
      return undefined;
    }

    let disposed = false;
    let reconnectAttempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let ws: WebSocket | null = null;

    const connect = () => {
      if (disposed) return;
      const wsUrl = `${API_URL.replace(/^http/, 'ws')}/cocktails/ws/payment/user`;
      ws = new WebSocket(wsUrl);
      // Track if connection was ever established (to suppress StrictMode double-mount noise)
      let wasConnected = false;

      ws.onopen = () => {
        console.log('Payment WebSocket connected');
        wasConnected = true;
        reconnectAttempt = 0;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: PaymentUserUpdate = JSON.parse(event.data);

          // Handle error states - show toast but don't change user state
          const lookupResult = data.changeReason;
          if (lookupResult === 'USER_NOT_FOUND') {
            errorToast(t('payment.userNotFound'));
            return;
          }
          if (lookupResult === 'SERVICE_UNAVAILABLE') {
            errorToast(t('payment.serviceUnavailable'));
            return;
          }

          // Only update if user actually changed
          const currentUid = data.user?.nfc_id ?? null;
          if (currentUid !== prevUserUidRef.current) {
            prevUserUidRef.current = currentUid;
            setUser(data.user);
            setCocktails(data.cocktails);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        // Only log errors if connection was established (avoid React StrictMode noise)
        if (wasConnected) {
          console.error('Payment WebSocket error:', error);
        }
      };

      ws.onclose = () => {
        // Only log if connection was established (avoid React StrictMode noise)
        if (wasConnected) {
          console.log('Payment WebSocket closed');
        }
        setIsConnected(false);
        // Schedule reconnection with exponential backoff
        if (!disposed) {
          const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempt, RECONNECT_MAX_DELAY_MS);
          reconnectAttempt += 1;
          console.log(`Payment WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttempt})`);
          reconnectTimer = setTimeout(connect, delay);
        }
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      ws?.close();
    };
  }, [enabled, t]);

  return { user, cocktails, isConnected };
};
