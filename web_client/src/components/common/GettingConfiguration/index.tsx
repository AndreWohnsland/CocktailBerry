import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCog } from 'react-icons/fa';

const GettingConfiguration: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
      <FaCog className='animate-spin text-neutral' size={100} />
      <span className='mt-8 text-2xl text-secondary text-center'>{t('skeletons.gettingConfiguration')}</span>
      <span className='mt-4 text-lg text-center'>{t('skeletons.gettingConfigurationDescription')}</span>
      <span className='mt-4 text-md text-neutral text-center'>{t('skeletons.errorPersistInformation')}</span>
    </div>
  );
};

export default GettingConfiguration;
