import React from 'react';
import { useTranslation } from 'react-i18next';
import { MdLock } from 'react-icons/md';
import InfoScreen from '../InfoScreen';

export interface LockScreenProps {
  title?: string;
  message: string;
}

const LockScreen: React.FC<LockScreenProps> = ({ title, message }) => {
  const { t } = useTranslation();

  return (
    <InfoScreen
      icon={<MdLock size={100} className='text-primary' />}
      title={title ?? t('lockScreen.defaultTitle')}
      description={message}
    />
  );
};

export default LockScreen;
