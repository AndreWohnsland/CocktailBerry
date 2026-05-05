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
  const prevUserUidRef = useRef<string | null>(null);

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

      const currentUid = data.user?.nfc_id ?? null;
      if (currentUid !== prevUserUidRef.current) {
        prevUserUidRef.current = currentUid;
        setUser(data.user);
        setCocktails(data.cocktails);
      }
    },
    onReset: () => {
      setUser(null);
      setCocktails([]);
      prevUserUidRef.current = null;
    },
  });

  return { user, cocktails, isConnected };
};
