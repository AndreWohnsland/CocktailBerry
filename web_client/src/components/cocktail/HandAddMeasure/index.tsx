import type React from 'react';
import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaTimes } from 'react-icons/fa';
import { FaRegCircle, FaScaleUnbalanced } from 'react-icons/fa6';
import { readScale, tareScale } from '../../../api/scale';
import type { HandAddMeasure as HandAddItem } from '../../../types/models';
import Button from '../../common/Button';
import ProgressBar from '../../common/ProgressBar';
import TextHeader from '../../common/TextHeader';

// how long the completion message lingers before the window auto-closes
const HAND_ADD_LINGER_MS = 5000;

interface HandAddMeasureProps {
  handAdds: HandAddItem[];
  onFinish: () => void;
  /** Tare the scale. Injectable for tests/storybook; defaults to the real API call. */
  tare?: () => Promise<unknown>;
  /** Read the current weight in grams. Injectable for tests/storybook. */
  read?: () => Promise<number>;
  pollIntervalMs?: number;
}

// resolved-row marker; sized like the action buttons so the column does not shift on resolve
const DoneCheck: React.FC = () => (
  <span className='text-secondary w-14 h-11 flex items-center justify-center'>
    <FaCheck size={30} />
  </span>
);

// borderless tap-to-confirm for a by-hand row: a plain button avoids Button's border / active-press flash
const ManualCheckButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button type='button' className='p-2 flex items-center justify-center w-14 h-11 text-primary' onClick={onClick}>
    <FaRegCircle size={30} />
  </button>
);

/**
 * Scale-assisted hand-add window (v2): weighable rows get a measure button + progress bar, by-hand
 * rows get a confirm button, and rows resolve in any order. Once all rows resolve, a completion
 * message shows and the window lingers briefly before auto-finishing; the modal-footer Finish
 * closes early.
 */
const HandAddMeasure: React.FC<HandAddMeasureProps> = ({
  handAdds,
  onFinish,
  tare = tareScale,
  read = async () => (await readScale()).data,
  pollIntervalMs = 250,
}) => {
  const { t } = useTranslation();
  const [doneIndices, setDoneIndices] = useState<Set<number>>(new Set());
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [grams, setGrams] = useState(0);
  const finishedRef = useRef(false);

  const measurableIndices = handAdds.map((ha, i) => (ha.measurable ? i : -1)).filter((i) => i >= 0);
  const manualIndices = handAdds.map((ha, i) => (ha.measurable ? -1 : i)).filter((i) => i >= 0);
  const pendingMeasurable = measurableIndices.filter((i) => !doneIndices.has(i));
  const pendingManual = manualIndices.filter((i) => !doneIndices.has(i));
  // no measure rows → no progress column to align to, so center the rest
  const hasMeasurable = measurableIndices.length > 0;
  // require at least one row so an empty list never counts as resolved
  const allResolved =
    activeIndex === null && handAdds.length > 0 && pendingMeasurable.length === 0 && pendingManual.length === 0;

  const triggerFinish = useCallback(() => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    onFinish();
  }, [onFinish]);

  // all resolved → linger on the completion message, then finish
  useEffect(() => {
    if (!allResolved) return;
    const id = setTimeout(triggerFinish, HAND_ADD_LINGER_MS);
    return () => clearTimeout(id);
  }, [allResolved, triggerFinish]);

  // poll the scale while a measurement is active
  useEffect(() => {
    if (activeIndex === null) return;
    const active = handAdds[activeIndex];
    if (!active) return;
    const target = active.amount;
    let cancelled = false;
    const id = setInterval(async () => {
      let current: number;
      try {
        current = await read();
      } catch {
        return;
      }
      if (cancelled) return;
      setGrams(current);
      if (target > 0 && current >= target) {
        setDoneIndices((prev) => new Set(prev).add(activeIndex));
        setActiveIndex(null);
        setGrams(0);
      }
    }, pollIntervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [activeIndex, handAdds, read, pollIntervalMs]);

  const startMeasure = async (index: number) => {
    if (activeIndex !== null) return;
    try {
      await tare();
    } catch {
      return;
    }
    setGrams(0);
    setActiveIndex(index);
  };

  const cancelMeasure = () => {
    setActiveIndex(null);
    setGrams(0);
  };

  const confirmManual = (index: number) => {
    setDoneIndices((prev) => new Set(prev).add(index));
  };

  const progressPercent = (index: number) => {
    const target = handAdds[index].amount;
    if (target <= 0) return 0;
    return Math.max(0, Math.min(100, Math.round((grams / target) * 100)));
  };

  return (
    // one grid aligns action / amount / name / progress across both sections; Finish lives in ProgressModal
    <div className='flex flex-col grow w-full max-w-lg mx-auto justify-center px-2'>
      {allResolved ? (
        <div className='flex flex-col items-center justify-center text-center gap-5 grow'>
          <span className='flex items-center justify-center text-secondary mb-4'>
            <FaCheck size={50} />
          </span>
          <p className='text-xl'>{t('cocktails.handAdd.allDone')}</p>
        </div>
      ) : (
        <>
          <p className='text-neutral text-center mb-4'>{t('cocktails.handAdd.intro')}</p>
          <div
            className={`grid items-center gap-x-3 gap-y-1 overflow-y-auto ${
              hasMeasurable
                ? 'grid-cols-[auto_auto_auto_minmax(120px,1fr)]'
                : 'grid-cols-[auto_auto_auto] justify-center'
            }`}
          >
            {measurableIndices.length > 0 && (
              <div className='col-span-full'>
                <TextHeader subheader space={4} text={t('cocktails.handAdd.withScale')} />
              </div>
            )}
            {measurableIndices.map((i) => {
              const ha = handAdds[i];
              const isActive = activeIndex === i;
              const isDone = doneIndices.has(i);
              return (
                <Fragment key={`m-${ha.name}-${i}`}>
                  {isDone ? (
                    <DoneCheck />
                  ) : isActive ? (
                    <Button
                      icon={FaTimes}
                      label=''
                      iconSize={22}
                      style='danger'
                      className='w-14 h-11'
                      onClick={cancelMeasure}
                    />
                  ) : (
                    <Button
                      icon={FaScaleUnbalanced}
                      label=''
                      iconSize={22}
                      filled
                      className='w-14 h-11'
                      onClick={() => startMeasure(i)}
                      disabled={activeIndex !== null}
                    />
                  )}
                  <span
                    className={`text-right text-secondary whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}
                  >
                    {ha.amount} {ha.unit}
                  </span>
                  <span className={`text-text whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}>
                    {ha.name}
                  </span>
                  <ProgressBar className='w-full h-11' fillPercent={isDone ? 100 : isActive ? progressPercent(i) : 0} />
                </Fragment>
              );
            })}
            {manualIndices.length > 0 && (
              <div className='col-span-full mt-4'>
                <TextHeader subheader space={hasMeasurable ? 2 : 4} text={t('cocktails.handAdd.manually')} />
              </div>
            )}
            {manualIndices.map((i) => {
              const ha = handAdds[i];
              const isDone = doneIndices.has(i);
              return (
                <Fragment key={`t-${ha.name}-${i}`}>
                  {isDone ? <DoneCheck /> : <ManualCheckButton onClick={() => confirmManual(i)} />}
                  <span
                    className={`text-right text-secondary whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}
                  >
                    {ha.amount} {ha.unit}
                  </span>
                  <span className={`text-text whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}>
                    {ha.name}
                  </span>
                  {/* empty progress cell to keep manual rows aligned with measure rows */}
                  {hasMeasurable && <span aria-hidden />}
                </Fragment>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default HandAddMeasure;
