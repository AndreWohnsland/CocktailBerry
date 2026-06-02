import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { cancelPayment, getCocktailStatus, stopCocktail } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import type { HandAddMeasure as HandAddItem } from '../../types/models';
import { errorToast } from '../../utils';
import PreparationFinalize from '../cocktail/PreparationFinalize';
import PaymentWaiting from './PaymentWaiting';
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
        if (cocktailStatus.status === 'IN_PROGRESS' || cocktailStatus.status === 'WAITING_FOR_PAYMENT') {
          return;
        }
        // terminal status: the cocktail is finalized. If it carries hand-adds, show the (non-blocking)
        // scale guidance window instead of closing; otherwise show the message or just close.
        cancelInterval();
        const adds = cocktailStatus.hand_adds ?? [];
        const msg = cocktailStatus.message ? cocktailStatus.message.replaceAll('\n', '<br />') : null;
        if (adds.length > 0) {
          // the guidance window carries the message (e.g. payment balance) so it still shows
          setHandAdds(adds);
          setMessage(msg);
        } else if (msg) {
          setMessage(msg);
        } else {
          closeWindow(cocktailStatus.status);
        }
      }, 250);
    }

    return () => {
      cancelInterval();
    };
  }, [isOpen, closeWindow]);

  // the completion view (hand-adds and/or message) owns its own auto-close linger + walk-away timeout
  const showCompletion = handAdds.length > 0 || message !== null;

  const chooseButton = (status: string) => {
    if (status === 'WAITING_FOR_PAYMENT') {
      return (
        <button type='button' className='px-4 py-2 button-primary w-1/2' onClick={handleCancelPayment}>
          {t('cancel')}
        </button>
      );
    } else if (showCompletion) {
      return (
        <button type='button' className='px-4 py-2 button-primary w-1/2' onClick={() => closeWindow('FINISHED')}>
          {t('cocktails.handAdd.finish')}
        </button>
      );
    } else if (status === 'IN_PROGRESS') {
      return (
        <button type='button' className='px-4 py-2 button-primary w-1/2' onClick={stopCocktail}>
          {t('cancel')}
        </button>
      );
    } else {
      return (
        <button type='button' className='px-4 py-2 button-primary w-1/2' onClick={() => closeWindow(currentStatus)}>
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
        <TextHeader text={displayName} huge space={4} />
        {currentStatus === 'WAITING_FOR_PAYMENT' ? (
          <PaymentWaiting />
        ) : showCompletion ? (
          // post-preparation completion: interactive hand-adds (if any) then the optional message.
          // The cocktail is already finalized, so Finish just closes.
          <PreparationFinalize
            handAdds={handAdds}
            message={message}
            expFactor={config.EXP_MAKER_FACTOR}
            expUnit={config.EXP_MAKER_UNIT}
            onFinish={() => closeWindow('FINISHED')}
          />
        ) : (
          <ProgressBar className='w-full min-h-20' fillPercent={currentProgress} />
        )}
        <div className='text-center mt-4'>{chooseButton(currentStatus)}</div>
      </div>
    </Modal>
  );
};

export default ProgressModal;
