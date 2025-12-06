import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaCreditCard } from 'react-icons/fa';
import Modal from 'react-modal';
import { cancelPayment } from '../../api/cocktails';
import { errorToast } from '../../utils';
import TextHeader from '../common/TextHeader';

interface NFCPaymentPromptProps {
  isOpen: boolean;
  onRequestClose: () => void;
  displayName: string;
  triggerOnClose?: () => void;
}

const NFCPaymentPrompt: React.FC<NFCPaymentPromptProps> = ({ isOpen, onRequestClose, displayName, triggerOnClose }) => {
  const { t } = useTranslation();

  const handleCancel = async () => {
    try {
      await cancelPayment();
      if (triggerOnClose) {
        triggerOnClose();
      }
      onRequestClose();
    } catch (error) {
      errorToast(error);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel='NFC Payment Modal'
      className='modal'
      overlayClassName='overlay z-30'
      shouldCloseOnOverlayClick={false}
      preventScroll={true}
    >
      <div className='h-full flex flex-col justify-between items-center py-8'>
        <TextHeader text={displayName} huge />
        <div className='flex flex-col items-center justify-center flex-grow gap-8'>
          <FaCreditCard className='text-primary animate-pulse' size={120} />
          <div className='text-center'>
            <p className='text-2xl text-neutral font-bold mb-4'>{t('payment.scanNFC')}</p>
            <p className='text-lg text-text'>{t('payment.holdCard')}</p>
          </div>
        </div>
        <div className='text-center mt-8'>
          <button type='button' className='mt-4 px-4 py-2 button-primary w-64' onClick={handleCancel}>
            {t('cancel')}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default NFCPaymentPrompt;
