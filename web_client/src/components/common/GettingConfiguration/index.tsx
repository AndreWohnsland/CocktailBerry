import type React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCog } from 'react-icons/fa';
import InfoScreen from '../InfoScreen';

const GettingConfiguration: React.FC = () => {
  const { t } = useTranslation();
  return (
    <InfoScreen
      icon={<FaCog className='animate-spin text-neutral' size={100} />}
      title={t('skeletons.gettingConfiguration')}
      description={t('skeletons.gettingConfigurationDescription')}
      hint={t('skeletons.errorPersistInformation')}
    />
  );
};

export default GettingConfiguration;
