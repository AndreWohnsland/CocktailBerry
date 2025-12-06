import { useEffect, useState } from 'react';
import { Cocktail, PaymentUserData, PaymentUserUpdate } from '../types/models';
import { API_URL } from './common';

export const usePaymentWebSocket = (enabled: boolean) => {
  const [user, setUser] = useState<PaymentUserData | null>(null);
  const [cocktails, setCocktails] = useState<Cocktail[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setUser(null);
      setCocktails([]);
      setIsConnected(false);
      return;
    }

    // Create WebSocket URL (convert http to ws)
    const wsUrl = API_URL.replace(/^http/, 'ws') + '/cocktails/ws/payment/user';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Payment WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: PaymentUserUpdate = JSON.parse(event.data);
        setUser(data.user);
        setCocktails(data.cocktails);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Payment WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Payment WebSocket closed');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [enabled]);

  return { user, cocktails, isConnected };
};
