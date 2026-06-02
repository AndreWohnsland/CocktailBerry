import type React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCreditCard } from 'react-icons/fa';

/** WAITING_FOR_PAYMENT view shown in ProgressModal while the user holds their NFC card to the reader. */
const PaymentWaiting: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className='flex flex-col items-center justify-center grow gap-8'>
      <FaCreditCard className='text-primary animate-pulse' size={120} />
      <div className='text-center'>
        <p className='text-2xl text-neutral font-bold mb-4'>{t('payment.scanNFC')}</p>
        <p className='text-lg text-text'>{t('payment.holdCard')}</p>
      </div>
    </div>
  );
};

export default PaymentWaiting;
