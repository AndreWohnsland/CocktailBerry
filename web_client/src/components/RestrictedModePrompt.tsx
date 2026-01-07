import React from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { useRestrictedMode } from '../providers/RestrictedModeProvider';

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
      className='w-full max-w-md p-6 bg-background border-2 border-primary rounded-lg shadow-lg'
      overlayClassName='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'
      contentLabel={t('restrictedMode.title')}
    >
      <div className='flex flex-col space-y-4'>
        <h2 className='text-2xl font-bold text-primary'>{t('restrictedMode.title')}</h2>
        <p className='text-neutral'>{t('restrictedMode.message')}</p>
        <div className='flex space-x-4 justify-end'>
          <button
            onClick={handleDecline}
            className='px-4 py-2 bg-neutral text-background rounded hover:bg-opacity-80 transition-colors'
          >
            {t('restrictedMode.decline')}
          </button>
          <button
            onClick={handleAccept}
            className='px-4 py-2 bg-primary text-background rounded hover:bg-opacity-80 transition-colors'
          >
            {t('restrictedMode.accept')}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default RestrictedModePrompt;
