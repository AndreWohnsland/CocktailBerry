import React from 'react';
import { useTranslation } from 'react-i18next';
import { MdLock } from 'react-icons/md';

const PaymentLockScreen: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className='flex flex-col items-center justify-center min-h-screen px-4'>
      <div className='flex flex-col items-center gap-6 max-w-md text-center'>
        <MdLock size={120} className='text-primary' />
        <h1 className='text-4xl font-bold text-primary'>{t('payment.lockScreen.title')}</h1>
        <p className='text-xl text-neutral'>{t('payment.lockScreen.message')}</p>
      </div>
    </div>
  );
};

export default PaymentLockScreen;
