import { useEffect, useRef, useState } from 'react';
import { Cocktail, PaymentUserData, PaymentUserUpdate } from '../types/models';
import { API_URL } from './common';

export const usePaymentWebSocket = (enabled: boolean) => {
  const [user, setUser] = useState<PaymentUserData | null>(null);
  const [cocktails, setCocktails] = useState<Cocktail[]>([]);
  const [isConnected, setIsConnected] = useState(false);

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

    ws.onopen = () => {
      console.log('Payment WebSocket connected');
      wasConnected = true;
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: PaymentUserUpdate = JSON.parse(event.data);

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
    };

    return () => {
      ws.close();
    };
  }, [enabled]);

  return { user, cocktails, isConnected };
};
