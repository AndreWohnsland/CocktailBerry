import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCreditCard } from 'react-icons/fa';
import Modal from 'react-modal';
import { cancelPayment, getCocktailStatus, stopCocktail } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import { errorToast } from '../../utils';
import ProgressBar from '../common/ProgressBar';
import TextHeader from '../common/TextHeader';

interface ProgressModalProps {
  isOpen: boolean;
  onRequestClose: () => void;
  progress: number;
  displayName: string;
  triggerOnClose?: () => void;
}

const ProgressModal: React.FC<ProgressModalProps> = ({
  isOpen,
  onRequestClose,
  progress,
  displayName,
  triggerOnClose,
}) => {
  const { config } = useConfig();
  const [currentProgress, setCurrentProgress] = useState(progress);
  const [currentStatus, setCurrentStatus] = useState<string>(config.PAYMENT_ACTIVE ? 'WAITING_FOR_NFC' : 'IN_PROGRESS');
  const [message, setMessage] = useState<string | null>(null);
  const { t } = useTranslation();

  const closeWindow = React.useCallback(() => {
    setCurrentProgress(0);
    setMessage(null);
    onRequestClose();
    if (triggerOnClose) {
      triggerOnClose();
    }
  }, [onRequestClose, triggerOnClose]);

  const handleCancelPayment = async () => {
    try {
      await cancelPayment();
      closeWindow();
    } catch (error) {
      errorToast(error);
    }
  };

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const cancelInterval = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    if (isOpen && !intervalId) {
      intervalId = setInterval(async () => {
        const cocktailStatus = await getCocktailStatus();
        setCurrentStatus(cocktailStatus.status);
        setCurrentProgress(cocktailStatus.progress);
        if (cocktailStatus.status === 'IN_PROGRESS' || cocktailStatus.status === 'WAITING_FOR_NFC') {
          return;
        }
        cancelInterval();
        if (cocktailStatus.message) {
          const formattedMessage = cocktailStatus.message.replaceAll('\n', '<br />');
          setMessage(formattedMessage);
        } else {
          closeWindow();
        }
      }, 250);
    }

    return () => {
      cancelInterval();
    };
  }, [isOpen, closeWindow]);

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel='Progress Modal'
      className='modal'
      overlayClassName='overlay z-30'
      shouldCloseOnOverlayClick={false}
      preventScroll={true}
    >
      <div className='progress-modal h-full flex flex-col justify-between'>
        <TextHeader text={displayName} huge />
        {currentStatus === 'WAITING_FOR_NFC' ? (
          <div className='flex flex-col items-center justify-center flex-grow gap-8'>
            <FaCreditCard className='text-primary animate-pulse' size={120} />
            <div className='text-center'>
              <p className='text-2xl text-neutral font-bold mb-4'>{t('payment.scanNFC')}</p>
              <p className='text-lg text-text'>{t('payment.holdCard')}</p>
            </div>
          </div>
        ) : message ? (
          // biome-ignore lint/security/noDangerouslySetInnerHtml: it is from our backend, so its okay for now
          <div className='text-neutral text-center' dangerouslySetInnerHTML={{ __html: message }} />
        ) : (
          <ProgressBar className='w-full min-h-20' fillPercent={currentProgress} />
        )}
        <div className='text-center mt-8'>
          {currentStatus === 'WAITING_FOR_NFC' ? (
            <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={handleCancelPayment}>
              {t('cancel')}
            </button>
          ) : currentStatus === 'IN_PROGRESS' ? (
            <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={stopCocktail}>
              {t('cancel')}
            </button>
          ) : (
            <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={closeWindow}>
              {t('close')}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default ProgressModal;
