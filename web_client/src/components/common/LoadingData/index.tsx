import type React from 'react';
import { useTranslation } from 'react-i18next';
import { FaSpinner } from 'react-icons/fa';
import InfoScreen from '../InfoScreen';

export interface LoadingDataProps {
  showDescription?: boolean;
}

const LoadingData: React.FC<LoadingDataProps> = ({ showDescription = true }) => {
  const { t } = useTranslation();
  return (
    <InfoScreen
      icon={<FaSpinner className='animate-spin text-neutral' size={100} />}
      title={t('skeletons.loadingData')}
      description={showDescription ? t('skeletons.loadingDataDescription') : undefined}
    />
  );
};

export default LoadingData;
