import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from 'react-modal';
import type { HandAddAssistItem } from '../../types/models';
import TextHeader from '../common/TextHeader';
import HandAddMeasureModal from './HandAddMeasureModal';

interface HandAddAssistModalProps {
  isOpen: boolean;
  items: HandAddAssistItem[];
  introMessage?: string;
  onFinish: () => void;
}

const HandAddAssistModal = ({ isOpen, items, introMessage, onFinish }: HandAddAssistModalProps) => {
  const { t } = useTranslation();
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const [measuringItem, setMeasuringItem] = useState<HandAddAssistItem | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setCompletedIds(new Set());
      setMeasuringItem(null);
    }
  }, [isOpen]);

  const allDone = useMemo(() => items.length > 0 && completedIds.size === items.length, [completedIds, items.length]);

  useEffect(() => {
    if (allDone) {
      onFinish();
    }
  }, [allDone, onFinish]);

  const markDone = (itemId: string) => {
    setCompletedIds((current) => new Set(current).add(itemId));
    setMeasuringItem(null);
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onRequestClose={onFinish}
        contentLabel='Hand Add Assist Modal'
        className='modal'
        overlayClassName='overlay z-30'
        shouldCloseOnOverlayClick={false}
        preventScroll={true}
      >
        <div className='flex h-full flex-col gap-6'>
          <div>
            <TextHeader text={t('handAddAssist.title')} />
            {introMessage && <p className='mt-3 text-center text-text'>{introMessage}</p>}
          </div>
          <div className='flex grow flex-col gap-3 overflow-y-auto'>
            {items.map((item) => {
              const isCompleted = completedIds.has(item.item_id);
              return (
                <div
                  key={item.item_id}
                  className={`flex items-center justify-between gap-4 rounded-lg border-2 border-neutral p-4 ${
                    isCompleted ? 'opacity-60' : ''
                  }`}
                >
                  <div>
                    <p className='text-lg font-bold text-text'>
                      {t('handAddAssist.instruction', {
                        ingredient: item.name,
                        amount: item.display_amount,
                        unit: item.display_unit,
                      })}
                    </p>
                    {isCompleted && <p className='text-secondary'>{t('done')}</p>}
                  </div>
                  {!isCompleted && (
                    <button
                      type='button'
                      className='button-primary min-w-28 px-4 py-2'
                      onClick={() => (item.measurable ? setMeasuringItem(item) : markDone(item.item_id))}
                    >
                      {t(item.measurable ? 'handAddAssist.measure' : 'handAddAssist.markDone')}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <button type='button' className='button-neutral w-full px-4 py-3' onClick={onFinish}>
            {t('handAddAssist.finish')}
          </button>
        </div>
      </Modal>
      <HandAddMeasureModal
        isOpen={!!measuringItem}
        item={measuringItem}
        onClose={() => setMeasuringItem(null)}
        onComplete={markDone}
      />
    </>
  );
};

export default HandAddAssistModal;
