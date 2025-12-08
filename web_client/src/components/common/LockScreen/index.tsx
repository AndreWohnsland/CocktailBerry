import React from 'react';
import { useTranslation } from 'react-i18next';
import { MdLock } from 'react-icons/md';

export interface LockScreenProps {
  title?: string;
  message: string;
}

const LockScreen: React.FC<LockScreenProps> = ({ title, message }) => {
  const { t } = useTranslation();

  return (
    <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
      <MdLock size={100} className='text-primary' />
      <span className='mt-8 text-2xl text-secondary text-center'>{title ?? t('lockScreen.defaultTitle')}</span>
      <span className='mt-4 text-lg text-center'>{message}</span>
    </div>
  );
};

export default LockScreen;
