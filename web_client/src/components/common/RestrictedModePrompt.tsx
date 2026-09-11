import type React from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { useRestrictedMode } from '../../providers/RestrictedModeProvider';
import Button from './Button';
import TextHeader from './TextHeader';

const RestrictedModePrompt: React.FC = () => {
  const { t } = useTranslation();
  const { hasPrompted, setRestrictedMode } = useRestrictedMode();

  const handleAccept = () => {
    setRestrictedMode(true);
  };

  const handleDecline = () => {
    setRestrictedMode(false);
  };

  return (
    <Modal
      isOpen={!hasPrompted}
      className='modal slim h-fit'
      overlayClassName='overlay z-50'
      contentLabel={t('restrictedMode.title')}
    >
      <div className='flex flex-col justify-center h-full p-4'>
        <TextHeader text={t('restrictedMode.title')} />
        <p className='mb-8 text-center'>{t('restrictedMode.message')}</p>
        <div className='flex gap-4 justify-between'>
          <Button style='neutral' label={t('restrictedMode.decline')} className='min-w-36' onClick={handleDecline} />
          <Button filled label={t('restrictedMode.accept')} className='min-w-36' onClick={handleAccept} />
        </div>
      </div>
    </Modal>
  );
};

export default RestrictedModePrompt;
