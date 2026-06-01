import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCreditCard } from 'react-icons/fa';
import Modal from 'react-modal';
import { cancelPayment, finishHandAdd, getCocktailStatus, stopCocktail } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import type { HandAddMeasure as HandAddItem } from '../../types/models';
import { errorToast } from '../../utils';
import HandAddMeasure from '../cocktail/HandAddMeasure';
import ProgressBar from './ProgressBar';
import TextHeader from './TextHeader';

interface ProgressModalProps {
  isOpen: boolean;
  onRequestClose: () => void;
  progress: number;
  displayName: string;
  triggerOnClose?: (status: string) => void;
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
  const [currentStatus, setCurrentStatus] = useState<string>(
    config.PAYMENT_TYPE !== 'Disabled' ? 'WAITING_FOR_PAYMENT' : 'IN_PROGRESS',
  );
  const [message, setMessage] = useState<string | null>(null);
  const [handAdds, setHandAdds] = useState<HandAddItem[]>([]);
  const { t } = useTranslation();

  const closeWindow = React.useCallback(
    (finalStatus?: string) => {
      setCurrentProgress(0);
      setMessage(null);
      setHandAdds([]);
      onRequestClose();
      if (triggerOnClose) {
        triggerOnClose(finalStatus ?? 'CANCELED');
      }
    },
    [onRequestClose, triggerOnClose],
  );

  const handleCancelPayment = async () => {
    try {
      await cancelPayment();
      closeWindow('CANCELED');
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
        if (cocktailStatus.status === 'WAITING_FOR_HAND_ADD') {
          // capture the list once; keep polling so the FINISHED transition closes the modal
          setHandAdds((prev) => (prev.length ? prev : (cocktailStatus.hand_adds ?? [])));
          return;
        }
        if (cocktailStatus.status === 'IN_PROGRESS' || cocktailStatus.status === 'WAITING_FOR_PAYMENT') {
          return;
        }
        cancelInterval();
        if (cocktailStatus.message) {
          const formattedMessage = cocktailStatus.message.replaceAll('\n', '<br />');
          setMessage(formattedMessage);
        } else {
          closeWindow(cocktailStatus.status);
        }
      }, 250);
    }

    return () => {
      cancelInterval();
    };
  }, [isOpen, closeWindow]);

  const chooseButton = (status: string) => {
    if (status === 'WAITING_FOR_PAYMENT') {
      return (
        <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={handleCancelPayment}>
          {t('cancel')}
        </button>
      );
    } else if (status === 'WAITING_FOR_HAND_ADD') {
      return (
        <button
          type='button'
          className='mt-4 px-4 py-2 button-primary w-1/2'
          onClick={() => finishHandAdd().catch(errorToast)}
        >
          {t('cocktails.handAdd.finish')}
        </button>
      );
    } else if (status === 'IN_PROGRESS') {
      return (
        <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={stopCocktail}>
          {t('cancel')}
        </button>
      );
    } else {
      return (
        <button
          type='button'
          className='mt-4 px-4 py-2 button-primary w-1/2'
          onClick={() => closeWindow(currentStatus)}
        >
          {t('close')}
        </button>
      );
    }
  };

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
        {currentStatus === 'WAITING_FOR_PAYMENT' ? (
          <div className='flex flex-col items-center justify-center grow gap-8'>
            <FaCreditCard className='text-primary animate-pulse' size={120} />
            <div className='text-center'>
              <p className='text-2xl text-neutral font-bold mb-4'>{t('payment.scanNFC')}</p>
              <p className='text-lg text-text'>{t('payment.holdCard')}</p>
            </div>
          </div>
        ) : currentStatus === 'WAITING_FOR_HAND_ADD' ? (
          <HandAddMeasure
            handAdds={handAdds}
            onFinish={() => {
              finishHandAdd().catch(errorToast);
            }}
          />
        ) : message ? (
          // biome-ignore lint/security/noDangerouslySetInnerHtml: it is from our backend, so its okay for now
          <div className='text-neutral text-center' dangerouslySetInnerHTML={{ __html: message }} />
        ) : (
          <ProgressBar className='w-full min-h-20' fillPercent={currentProgress} />
        )}
        <div className='text-center mt-8'>{chooseButton(currentStatus)}</div>
      </div>
    </Modal>
  );
};

export default ProgressModal;
