import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { Cocktail, PaymentUserData, PaymentUserUpdate } from '../types/models';
import { errorToast } from '../utils';
import { useReconnectingWebSocket } from './useReconnectingWebSocket';

export const usePaymentWebSocket = (enabled: boolean) => {
  const [user, setUser] = useState<PaymentUserData | null>(null);
  const [cocktails, setCocktails] = useState<Cocktail[]>([]);
  const { t } = useTranslation();

  // Track previous user UID to detect changes
  const prevUserRef = useRef<string | null>(null);

  const { isConnected } = useReconnectingWebSocket<PaymentUserUpdate>({
    enabled,
    path: '/cocktails/ws/payment/user',
    label: 'Payment',
    onMessage: (data) => {
      const lookupResult = data.changeReason;
      if (lookupResult === 'USER_NOT_FOUND') {
        errorToast(t('payment.userNotFound'));
        return;
      }
      if (lookupResult === 'SERVICE_UNAVAILABLE') {
        errorToast(t('payment.serviceUnavailable'));
        return;
      }

      // the reader re-sends the same card every second, only react to a change
      const currentUser = JSON.stringify(data.user);
      if (currentUser !== prevUserRef.current) {
        prevUserRef.current = currentUser;
        setUser(data.user);
        setCocktails(data.cocktails);
      }
    },
    onReset: () => {
      setUser(null);
      setCocktails([]);
      prevUserRef.current = null;
    },
  });

  return { user, cocktails, isConnected };
};
