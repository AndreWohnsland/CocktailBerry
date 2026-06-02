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

// the completion view (all-done and/or message) always auto-closes after this, regardless of what it shows
const COMPLETION_LINGER_MS = 10_000;
// while the user is actively resolving hand-adds, close on walk-away; longer when the scale is involved
const MEASURE_WALKAWAY_MS = 120_000;
const MANUAL_WALKAWAY_MS = 60_000;

interface PreparationFinalizeProps {
  handAdds: HandAddItem[];
  onFinish: () => void;
  /** Optional extra info (e.g. payment balance), already newline->br converted; shown in the completion view. */
  message?: string | null;
  /** Experimental-maker display scaling for ml amounts (visual only); defaults to no scaling. */
  expFactor?: number;
  expUnit?: string;
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
 * Post-preparation completion view (v2). Owns the whole terminal display for a finished cocktail:
 *
 * - With hand-adds: weighable rows get a measure button + progress bar, by-hand rows get a confirm
 *   button, and rows resolve in any order (walk-away safety timeout while measuring). Once all rows
 *   resolve, the completion view shows ("all done" + the optional message below it).
 * - Without hand-adds: the completion view renders directly (just the message).
 *
 * The completion view always auto-closes after COMPLETION_LINGER_MS; the modal-footer Finish closes
 * sooner. Rendered by ProgressModal only when there is a message and/or hand-adds.
 */
const PreparationFinalize: React.FC<PreparationFinalizeProps> = ({
  handAdds,
  onFinish,
  message = null,
  expFactor = 1,
  expUnit = 'ml',
  tare = tareScale,
  read = async () => (await readScale()).data,
  pollIntervalMs = 250,
}) => {
  const { t } = useTranslation();
  const [doneIndices, setDoneIndices] = useState<Set<number>>(new Set());
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [grams, setGrams] = useState(0);
  const finishedRef = useRef(false);
  // keep the latest read/onFinish in refs so the timeout/poll effects don't resubscribe every render
  // (the default read prop and the inline onFinish are fresh closures each render)
  const readRef = useRef(read);
  readRef.current = read;
  const onFinishRef = useRef(onFinish);
  onFinishRef.current = onFinish;

  // visual-only display of an amount: ml is scaled by the experimental maker factor/unit, everything
  // else is shown as-is. The measure math always uses the raw ml amount. Mirrors the v1 rounding.
  const formatAmount = (amountMl: number, unit: string): string => {
    const isMl = unit === 'ml';
    const value = isMl ? amountMl * expFactor : amountMl;
    const displayUnit = isMl ? expUnit : unit;
    const threshold = isMl ? 8 : 0;
    const rounded = value >= threshold ? Math.round(value) : Math.round(value * 10) / 10;
    return `${rounded} ${displayUnit}`;
  };

  const measurableIndices = handAdds.map((ha, i) => (ha.measurable ? i : -1)).filter((i) => i >= 0);
  const manualIndices = handAdds.map((ha, i) => (ha.measurable ? -1 : i)).filter((i) => i >= 0);
  const pendingMeasurable = measurableIndices.filter((i) => !doneIndices.has(i));
  const pendingManual = manualIndices.filter((i) => !doneIndices.has(i));
  // no measure rows → no progress column to align to, so center the rest
  const hasMeasurable = measurableIndices.length > 0;
  // all hand-adds resolved → ready to show the completion view
  const allResolved =
    activeIndex === null && handAdds.length > 0 && pendingMeasurable.length === 0 && pendingManual.length === 0;
  // completion view: either there were no hand-adds (message-only), or every row is resolved
  const inCompletion = handAdds.length === 0 || allResolved;

  const triggerFinish = useCallback(() => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    onFinishRef.current();
  }, []);

  // completion view auto-closes after a uniform linger (covers all-done, all-done+message, message-only)
  useEffect(() => {
    if (!inCompletion) return;
    const id = setTimeout(triggerFinish, COMPLETION_LINGER_MS);
    return () => clearTimeout(id);
  }, [inCompletion, triggerFinish]);

  // walk-away safety while still resolving hand-adds (interactive phase only)
  useEffect(() => {
    if (handAdds.length === 0 || allResolved) return;
    const id = setTimeout(triggerFinish, hasMeasurable ? MEASURE_WALKAWAY_MS : MANUAL_WALKAWAY_MS);
    return () => clearTimeout(id);
  }, [handAdds.length, allResolved, hasMeasurable, triggerFinish]);

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
        current = await readRef.current();
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
  }, [activeIndex, handAdds, pollIntervalMs]);

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

  // the message arrives already newline->br converted from the backend; rendered in the completion
  // view styled identically to the "all done" text
  const messageBlock = message ? (
    <p
      className='text-xl'
      // biome-ignore lint/security/noDangerouslySetInnerHtml: it is from our backend, so its okay for now
      dangerouslySetInnerHTML={{ __html: message }}
    />
  ) : null;

  return (
    // one grid aligns action / name / amount across rows; the amount cell swaps to the progress bar
    // while a row is measuring. Finish lives in ProgressModal
    <div className='flex flex-col grow w-full max-w-lg mx-auto justify-center px-2'>
      {inCompletion ? (
        <div className='flex flex-col items-center justify-center text-center gap-5 grow'>
          {/* the check always caps the finalize view; the all-done line only applies when hand-adds were added */}
          <span className='flex items-center justify-center text-secondary mb-4'>
            <FaCheck size={50} />
          </span>
          {handAdds.length > 0 && <p className='text-xl'>{t('cocktails.handAdd.allDone')}</p>}
          {messageBlock}
        </div>
      ) : (
        <>
          <p className='text-neutral text-center mb-4'>{t('cocktails.handAdd.intro')}</p>
          {/* last track fills the row (amount OR progress bar live here); its width is set by the grid,
              not its content, so swapping amount<->bar never shifts. the h-11 button anchors row height */}
          <div className='max-w-sm w-full mx-auto grid items-center gap-x-3 gap-y-1 overflow-y-auto grid-cols-[auto_auto_minmax(0,1fr)]'>
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
                  <span className={`whitespace-nowrap font-bold ${isDone ? 'line-through opacity-50' : ''}`}>
                    {ha.name}
                  </span>
                  {/* same fixed cell: progress while measuring, otherwise the target amount (no shift) */}
                  {isActive ? (
                    <ProgressBar className='w-full h-11' fillPercent={progressPercent(i)} />
                  ) : (
                    <span
                      className={`text-right text-secondary font-bold whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}
                    >
                      {formatAmount(ha.amount, ha.unit)}
                    </span>
                  )}
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
                  <span className={`font-bold whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}>
                    {ha.name}
                  </span>
                  <span
                    className={`text-right text-secondary font-bold whitespace-nowrap ${isDone ? 'line-through opacity-50' : ''}`}
                  >
                    {formatAmount(ha.amount, ha.unit)}
                  </span>
                </Fragment>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default PreparationFinalize;
