import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { cancelPayment, getCocktailStatus, stopCocktail } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import type { HandAddMeasure as HandAddItem, PrepareResult } from '../../types/models';
import { errorToast } from '../../utils';
import PreparationFinalize from '../cocktail/PreparationFinalize';
import PaymentWaiting from './PaymentWaiting';
import ProgressBar from './ProgressBar';
import TextHeader from './TextHeader';

// what the modal is currently doing; the body content and its footer button are picked from this
type ModalPhase = 'payment' | 'completion' | 'inProgress' | 'closing';

// single source of truth for what the modal is doing; both the body and the footer button derive from it
function getPhase(status: PrepareResult, handAdds: HandAddItem[], message: string | null): ModalPhase {
  if (status === 'WAITING_FOR_PAYMENT') return 'payment';
  if (status === 'IN_PROGRESS') return 'inProgress';
  if (handAdds.length > 0 || message !== null) return 'completion';
  return 'closing';
}

// shared footer button; only the action and label differ between phases
const FooterButton: React.FC<{ onClick: () => void; label: string; filled?: boolean }> = ({
  onClick,
  label,
  filled = false,
}) => (
  <div className='text-center mt-4'>
    <button
      type='button'
      className={`px-4 py-2 button-primary${filled ? '-filled' : ''} w-full max-w-md mx-auto`}
      onClick={onClick}
    >
      {label}
    </button>
  </div>
);

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
  const [currentStatus, setCurrentStatus] = useState<PrepareResult>(
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

    if (isOpen) {
      intervalId = setInterval(async () => {
        const cocktailStatus = await getCocktailStatus();
        setCurrentStatus(cocktailStatus.status);
        setCurrentProgress(cocktailStatus.progress);
        if (cocktailStatus.status === 'IN_PROGRESS' || cocktailStatus.status === 'WAITING_FOR_PAYMENT') {
          return;
        }
        // terminal: show hand-adds and/or message in PreparationFinalize, else close
        cancelInterval();
        const adds = cocktailStatus.hand_adds ?? [];
        const msg = cocktailStatus.message ? cocktailStatus.message.replaceAll('\n', '<br />') : null;
        if (adds.length > 0) {
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

  const phase = getPhase(currentStatus, handAdds, message);

  // one switch over the phase renders the body and its footer button together
  const renderPhase = () => {
    switch (phase) {
      case 'payment':
        return (
          <>
            <PaymentWaiting />
            <FooterButton onClick={handleCancelPayment} label={t('cancel')} />
          </>
        );
      case 'completion':
        // cocktail already finalized; Finish just closes
        return (
          <>
            <PreparationFinalize
              handAdds={handAdds}
              message={message}
              expFactor={config.EXP_MAKER_FACTOR}
              expUnit={config.EXP_MAKER_UNIT}
              onFinish={() => closeWindow('FINISHED')}
            />
            <FooterButton onClick={() => closeWindow('FINISHED')} label={t('cocktails.handAdd.finish')} filled />
          </>
        );
      case 'inProgress':
        return (
          <>
            <ProgressBar className='w-full min-h-20' fillPercent={currentProgress} />
            <FooterButton onClick={stopCocktail} label={t('cancel')} />
          </>
        );
      default:
        return (
          <>
            <ProgressBar className='w-full min-h-20' fillPercent={currentProgress} />
            <FooterButton onClick={() => closeWindow(currentStatus)} label={t('close')} filled />
          </>
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
        {renderPhase()}
      </div>
    </Modal>
  );
};

export default ProgressModal;
