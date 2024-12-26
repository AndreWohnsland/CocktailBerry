import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaExclamationTriangle } from 'react-icons/fa';

const ErrorComponent: React.FC<{ text?: string }> = ({ text }) => {
  const { t } = useTranslation();
  return (
    <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
      <FaExclamationTriangle className='text-danger' size={100} />
      <span className='mt-8 text-2xl text-secondary text-center'>Error</span>
      <span className='mt-4 text-lg text-center'>{text || t('skeletons.couldNotLoadData')}</span>
      <span className='mt-4 text-md text-neutral text-center'>{t('skeletons.errorPersistInformation')}</span>
    </div>
  );
};

export default ErrorComponent;
