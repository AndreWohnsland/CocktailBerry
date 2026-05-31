import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import { readScale, tareScale } from '../../api/scale';
import type { HandAddAssistItem } from '../../types/models';
import { errorToast } from '../../utils';
import ProgressBar from '../common/ProgressBar';
import TextHeader from '../common/TextHeader';

interface HandAddMeasureModalProps {
  isOpen: boolean;
  item: HandAddAssistItem | null;
  onClose: () => void;
  onComplete: (itemId: string) => void;
}

const HandAddMeasureModal = ({ isOpen, item, onClose, onComplete }: HandAddMeasureModalProps) => {
  const { t } = useTranslation();
  const [currentWeight, setCurrentWeight] = useState(0);

  useEffect(() => {
    if (!isOpen || !item?.target_weight_grams) {
      setCurrentWeight(0);
      return;
    }
    const targetWeight = item.target_weight_grams;

    let canceled = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const cancelInterval = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    const startMeasurement = async () => {
      try {
        await tareScale();
        intervalId = setInterval(async () => {
          try {
            const reading = await readScale();
            if (canceled) {
              return;
            }
            const weight = Math.max(0, reading.data);
            setCurrentWeight(weight);
            if (weight >= targetWeight) {
              cancelInterval();
              onComplete(item.item_id);
            }
          } catch (error) {
            cancelInterval();
            errorToast(error);
            onClose();
          }
        }, 250);
      } catch (error) {
        errorToast(error);
        onClose();
      }
    };

    startMeasurement();

    return () => {
      canceled = true;
      cancelInterval();
      setCurrentWeight(0);
    };
  }, [isOpen, item, onClose, onComplete]);

  if (!item?.target_weight_grams) {
    return null;
  }

  const targetWeight = item.target_weight_grams;
  const progress = Math.min(100, Math.round((currentWeight / targetWeight) * 100));

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      contentLabel='Hand Add Measure Modal'
      className='modal slim'
      overlayClassName='overlay z-40'
      shouldCloseOnOverlayClick={false}
      preventScroll={true}
    >
      <div className='flex h-full flex-col justify-between gap-6'>
        <div>
          <TextHeader text={t('handAddAssist.measureTitle', { ingredient: item.name })} />
          <p className='mb-3 text-center text-text'>{t('handAddAssist.target', { amount: targetWeight.toFixed(1) })}</p>
          <p className='mb-6 text-center text-neutral'>
            {t('handAddAssist.current', { amount: currentWeight.toFixed(1) })}
          </p>
          <ProgressBar className='h-16 w-full' fillPercent={progress} />
        </div>
        <button type='button' className='button-neutral w-full px-4 py-3' onClick={onClose}>
          {t('back')}
        </button>
      </div>
    </Modal>
  );
};

export default HandAddMeasureModal;
