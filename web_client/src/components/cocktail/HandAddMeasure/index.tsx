import type React from 'react';
import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaTimes } from 'react-icons/fa';
import { FaScaleUnbalanced } from 'react-icons/fa6';
import { readScale, tareScale } from '../../../api/scale';
import type { HandAddMeasure as HandAddItem } from '../../../types/models';
import Button from '../../common/Button';
import ProgressBar from '../../common/ProgressBar';
import TextHeader from '../../common/TextHeader';

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
 * Scale-assisted hand-add window (v2). One aligned grid holds both sections: weighable (ml)
 * hand adds get a measure button + progress bar (tap to tare, then track grams/target ml),
 * and non-ml hand adds get a check button to confirm they were added by hand. Rows can be
 * resolved in any order; the window auto-finishes once every row is resolved. Finish (in the
 * modal footer) is always available to complete early.
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

  const triggerFinish = useCallback(() => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    onFinish();
  }, [onFinish]);

  // auto-finish once every row (measured + manually confirmed) is resolved; require at least
  // one row so an (unexpected) empty list never auto-finishes on mount
  useEffect(() => {
    if (activeIndex === null && handAdds.length > 0 && pendingMeasurable.length === 0 && pendingManual.length === 0) {
      triggerFinish();
    }
  }, [activeIndex, handAdds.length, pendingMeasurable.length, pendingManual.length, triggerFinish]);

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
    // grow + center keeps the rows in the middle of the modal body; the Finish button is
    // rendered by the modal's own bottom button slot (see ProgressModal). One grid aligns the
    // action / amount / name / progress columns across both sections; headers span all columns.
    <div className='flex flex-col grow w-full max-w-2xl mx-auto justify-center px-2'>
      <div className='grid grid-cols-[auto_auto_auto_minmax(120px,1fr)] items-center gap-x-3 gap-y-3 overflow-y-auto'>
        {pendingMeasurable.length > 0 && (
          <div className='col-span-full'>
            <TextHeader subheader space={0} text={t('cocktails.handAdd.withScale')} />
          </div>
        )}
        {pendingMeasurable.map((i) => {
          const ha = handAdds[i];
          const isActive = activeIndex === i;
          return (
            <Fragment key={`m-${ha.name}-${i}`}>
              {isActive ? (
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
              <span className='text-right text-secondary whitespace-nowrap'>
                {ha.amount} {ha.unit}
              </span>
              <span className='text-text whitespace-nowrap'>{ha.name}</span>
              <ProgressBar className='w-full h-11' fillPercent={isActive ? progressPercent(i) : 0} />
            </Fragment>
          );
        })}
        {pendingManual.length > 0 && (
          <div className='col-span-full'>
            <TextHeader subheader space={0} text={t('cocktails.handAdd.manually')} />
          </div>
        )}
        {pendingManual.map((i) => {
          const ha = handAdds[i];
          return (
            <Fragment key={`t-${ha.name}-${i}`}>
              <Button
                icon={FaCheck}
                label=''
                iconSize={22}
                filled
                className='w-14 h-11'
                onClick={() => confirmManual(i)}
              />
              <span className='text-right text-secondary whitespace-nowrap'>
                {ha.amount} {ha.unit}
              </span>
              <span className='text-text whitespace-nowrap'>{ha.name}</span>
              {/* empty progress cell keeps the manual rows aligned with the measured ones */}
              <span aria-hidden />
            </Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default HandAddMeasure;
