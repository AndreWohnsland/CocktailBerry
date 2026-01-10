import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { Cocktail, PaymentUserData, PaymentUserUpdate, UserLookupResult } from '../types/models';
import { API_URL } from './common';

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

    // Create WebSocket URL (convert http to ws)
    const wsUrl = API_URL.replace(/^http/, 'ws') + '/cocktails/ws/payment/user';
    const ws = new WebSocket(wsUrl);
    // Track if connection was ever established (to suppress StrictMode double-mount noise)
    let wasConnected = false;

    const showErrorToast = (lookupResult: UserLookupResult) => {
      const randomNumber = Math.floor(100000 + Math.random() * 900000);
      if (lookupResult === 'user_not_found') {
        toast(t('payment.userNotFound'), {
          toastId: `payment-error-${randomNumber}`,
          pauseOnHover: false,
          autoClose: 5000,
        });
      } else if (lookupResult === 'service_unavailable') {
        toast(t('payment.serviceUnavailable'), {
          toastId: `payment-error-${randomNumber}`,
          pauseOnHover: false,
          autoClose: 5000,
        });
      }
    };

    ws.onopen = () => {
      console.log('Payment WebSocket connected');
      wasConnected = true;
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: PaymentUserUpdate = JSON.parse(event.data);
        const lookupResult = data.lookup_result;

        // Handle error states - show toast but don't change user state
        if (lookupResult === 'user_not_found' || lookupResult === 'service_unavailable') {
          showErrorToast(lookupResult);
          return;
        }

        // For user_found or user_removed, update state if user actually changed
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
    };

    return () => {
      ws.close();
    };
  }, [enabled, t]);

  return { user, cocktails, isConnected };
};
