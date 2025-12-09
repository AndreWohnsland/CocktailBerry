import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaExclamationTriangle } from 'react-icons/fa';
import InfoScreen from '../InfoScreen';

export interface ErrorComponentProps {
  text?: string;
}

const ErrorComponent: React.FC<ErrorComponentProps> = ({ text }) => {
  const { t } = useTranslation();
  return (
    <InfoScreen
      icon={<FaExclamationTriangle className='text-danger' size={100} />}
      title='Error'
      description={text ?? t('skeletons.couldNotLoadData')}
      hint={t('skeletons.errorPersistInformation')}
    />
  );
};

export default ErrorComponent;
