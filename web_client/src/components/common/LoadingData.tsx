import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaSpinner } from 'react-icons/fa';

const LoadingData: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
      <FaSpinner className='animate-spin text-neutral' size={100} />
      <span className='mt-8 text-2xl text-secondary text-center'>{t('skeletons.loadingData')}</span>
      <span className='mt-4 text-lg text-center'>{t('skeletons.loadingDataDescription')}</span>
    </div>
  );
};

export default LoadingData;
