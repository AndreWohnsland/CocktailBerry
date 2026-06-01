import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCreditCard } from 'react-icons/fa';
import Modal from 'react-modal';
import { cancelPayment, getCocktailStatus, stopCocktail } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import type { HandAddMeasure as HandAddItem } from '../../types/models';
import { errorToast } from '../../utils';
import HandAddMeasure from '../cocktail/HandAddMeasure';
import ProgressBar from './ProgressBar';
import TextHeader from './TextHeader';

// the cocktail is already finalized when guidance shows, so auto-close it if the user walks away;
// allow more time when the scale is involved (measuring takes longer than checking off manual adds)
const HAND_ADD_MANUAL_TIMEOUT_MS = 60_000;
const HAND_ADD_MEASURE_TIMEOUT_MS = 120_000;

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
        if (adds.length > 0) {
          setHandAdds(adds);
        } else if (cocktailStatus.message) {
          setMessage(cocktailStatus.message.replaceAll('\n', '<br />'));
        } else {
          closeWindow(cocktailStatus.status);
        }
      }, 250);
    }

    return () => {
      cancelInterval();
    };
  }, [isOpen, closeWindow]);

  // safety auto-close: guidance is purely informational (cocktail already saved)
  useEffect(() => {
    if (handAdds.length === 0) return;
    const timeoutMs = handAdds.some((h) => h.measurable) ? HAND_ADD_MEASURE_TIMEOUT_MS : HAND_ADD_MANUAL_TIMEOUT_MS;
    const id = setTimeout(() => closeWindow('FINISHED'), timeoutMs);
    return () => clearTimeout(id);
  }, [handAdds, closeWindow]);

  const chooseButton = (status: string) => {
    if (status === 'WAITING_FOR_PAYMENT') {
      return (
        <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={handleCancelPayment}>
          {t('cancel')}
        </button>
      );
    } else if (handAdds.length > 0) {
      return (
        <button type='button' className='mt-4 px-4 py-2 button-primary w-1/2' onClick={() => closeWindow('FINISHED')}>
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
        ) : handAdds.length > 0 ? (
          // scale-assisted hand-add guidance; the cocktail is already finalized, Finish just closes
          <HandAddMeasure handAdds={handAdds} onFinish={() => closeWindow('FINISHED')} />
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
