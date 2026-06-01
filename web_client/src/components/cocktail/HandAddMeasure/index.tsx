import type React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaTimes } from 'react-icons/fa';
import { FaScaleUnbalanced } from 'react-icons/fa6';
import { readHandAdd, tareHandAdd } from '../../../api/cocktails';
import type { HandAddMeasure as HandAddItem } from '../../../types/models';
import Button from '../../common/Button';
import ProgressBar from '../../common/ProgressBar';

interface HandAddMeasureProps {
  handAdds: HandAddItem[];
  onFinish: () => void;
  /** Tare the scale. Injectable for tests/storybook; defaults to the real API call. */
  tare?: () => Promise<unknown>;
  /** Read the current weight in grams. Injectable for tests/storybook. */
  read?: () => Promise<number>;
  pollIntervalMs?: number;
}

/**
 * Scale-assisted hand-add window (v2). Lists weighable (ml) hand adds with a measure
 * button each and non-ml hand adds as static instructions. Tapping measure tares, then
 * tracks current grams / target ml on a progress bar until the target is reached (rows can
 * be measured in any order). Auto-finishes when every weighable row is done and there are
 * no text-only rows; Finish is always available to complete early.
 */
const HandAddMeasure: React.FC<HandAddMeasureProps> = ({
  handAdds,
  onFinish,
  tare = tareHandAdd,
  read = readHandAdd,
  pollIntervalMs = 250,
}) => {
  const { t } = useTranslation();
  const [doneIndices, setDoneIndices] = useState<Set<number>>(new Set());
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [grams, setGrams] = useState(0);
  const finishedRef = useRef(false);

  const measurableIndices = handAdds.map((ha, i) => (ha.measurable ? i : -1)).filter((i) => i >= 0);
  const textOnly = handAdds.filter((ha) => !ha.measurable);
  const allMeasurableDone = measurableIndices.every((i) => doneIndices.has(i));

  const triggerFinish = useCallback(() => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    onFinish();
  }, [onFinish]);

  // auto-finish when everything weighable is done and nothing needs manual confirmation;
  // require at least one measurable row so an (unexpected) empty list never auto-finishes on mount
  useEffect(() => {
    if (activeIndex === null && measurableIndices.length > 0 && allMeasurableDone && textOnly.length === 0) {
      triggerFinish();
    }
  }, [activeIndex, measurableIndices.length, allMeasurableDone, textOnly.length, triggerFinish]);

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

  const progressPercent = (index: number) => {
    const target = handAdds[index].amount;
    if (target <= 0) return 0;
    return Math.max(0, Math.min(100, Math.round((grams / target) * 100)));
  };

  return (
    // grow + center keeps the rows in the middle of the modal body; the Finish button is
    // rendered by the modal's own bottom button slot (see ProgressModal) so it sits at the
    // bottom alongside the other modal actions. Auto-finish still flows through onFinish.
    <div className='flex flex-col grow w-full justify-center px-2'>
      <div className='flex flex-col gap-3 min-h-0 overflow-y-auto'>
        {measurableIndices
          .filter((i) => !doneIndices.has(i))
          .map((i) => {
            const ha = handAdds[i];
            return activeIndex === i ? (
              <div key={`${ha.name}-${i}`} className='flex items-center gap-3'>
                <span className='shrink-0 text-text'>{ha.name}</span>
                <ProgressBar className='grow h-9' fillPercent={progressPercent(i)} />
                <Button
                  icon={FaTimes}
                  label=''
                  iconSize={22}
                  style='danger'
                  className='w-14 h-11'
                  onClick={cancelMeasure}
                />
              </div>
            ) : (
              <div key={`${ha.name}-${i}`} className='flex items-center gap-4'>
                <span className='flex-1 min-w-0 text-text'>{ha.name}</span>
                <span className='w-16 shrink-0 text-right text-secondary'>
                  {ha.amount} {ha.unit}
                </span>
                <Button
                  icon={FaScaleUnbalanced}
                  label=''
                  iconSize={22}
                  filled
                  className='w-14 h-11'
                  onClick={() => startMeasure(i)}
                  disabled={activeIndex !== null}
                />
              </div>
            );
          })}
        {textOnly.length > 0 && (
          <>
            <p className='text-neutral mt-2'>{t('cocktails.handAdd.alsoAdd')}</p>
            {textOnly.map((ha) => (
              <div key={`text-${ha.name}-${ha.unit}-${ha.amount}`} className='flex items-center gap-4'>
                <span className='flex-1 min-w-0 text-text'>{ha.name}</span>
                <span className='w-16 shrink-0 text-right text-secondary'>
                  {ha.amount} {ha.unit}
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default HandAddMeasure;
