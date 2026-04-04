import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { calibrateScale, readScale, tareScale, useScaleStatus } from '../../api/scale';
import { executeAndShow } from '../../utils';
import NumberInput from '../common/NumberInput';
import TextHeader from '../common/TextHeader';

type CalibrationStep = 'tare' | 'weigh' | 'result';

const ScaleCalibrationWindow = () => {
  const [step, setStep] = useState<CalibrationStep>('tare');
  const [knownWeight, setKnownWeight] = useState(100);
  const [currentReading, setCurrentReading] = useState<number | null>(null);
  const [calibrationFactor, setCalibrationFactor] = useState<number | null>(null);
  const { data: scaleStatus, isLoading } = useScaleStatus();
  const { t } = useTranslation();

  const hasScale = scaleStatus?.data ?? false;

  const handleTare = async () => {
    const success = await executeAndShow(async () => {
      await tareScale();
      return t('scaleCalibration.tareSuccess');
    });
    if (success) {
      setStep('weigh');
    }
  };

  const handleReadWeight = async () => {
    const result = await readScale();
    setCurrentReading(result.data);
  };

  const handleCalibrate = async () => {
    const result = await calibrateScale(knownWeight);
    setCalibrationFactor(result.data);
    setStep('result');
  };

  const handleReset = () => {
    setStep('tare');
    setCurrentReading(null);
    setCalibrationFactor(null);
  };

  if (isLoading) {
    return <div className='flex justify-center items-center h-full'>{t('scaleCalibration.loading')}</div>;
  }

  if (!hasScale) {
    return (
      <div className='flex flex-col justify-center items-center p-4 w-full h-full max-w-md'>
        <TextHeader text={t('scaleCalibration.header')} />
        <div className='text-center text-lg font-semibold text-error mt-8'>{t('scaleCalibration.notAvailable')}</div>
      </div>
    );
  }

  return (
    <div className='flex flex-col justify-between items-center p-4 w-full h-full max-w-md max-h-[40rem]'>
      <TextHeader text={t('scaleCalibration.header')} />

      <div className='flex-grow py-2'></div>

      {step === 'tare' && (
        <>
          <div className='w-full max-w-sm space-y-6 text-center'>
            <p className='text-lg text-neutral'>{t('scaleCalibration.tareInstruction')}</p>
          </div>
          <div className='flex-grow py-2'></div>
          <button type='button' className='button-primary-filled text-lg p-4 w-full' onClick={handleTare}>
            {t('scaleCalibration.tare')}
          </button>
        </>
      )}

      {step === 'weigh' && (
        <>
          <div className='w-full max-w-sm space-y-6'>
            <p className='text-center text-lg text-neutral'>{t('scaleCalibration.placeWeightInstruction')}</p>
            <div className='space-y-2'>
              <label className='block text-center text-lg font-semibold text-neutral' htmlFor='known-weight'>
                {t('scaleCalibration.knownWeight')}
              </label>
              <NumberInput
                id='known-weight'
                value={knownWeight}
                handleInputChange={(v) => setKnownWeight(v)}
                suffix='g'
              />
            </div>
            {currentReading !== null && (
              <div className='text-center text-lg font-semibold text-neutral'>
                {t('scaleCalibration.currentReading', { weight: currentReading })}
              </div>
            )}
          </div>
          <div className='flex-grow py-2'></div>
          <div className='w-full space-y-3'>
            <button type='button' className='button-primary text-lg p-4 w-full' onClick={handleReadWeight}>
              {t('scaleCalibration.readWeight')}
            </button>
            <button
              type='button'
              className='button-primary-filled text-lg p-4 w-full'
              onClick={() => executeAndShow(handleCalibrate)}
            >
              {t('scaleCalibration.calibrate')}
            </button>
          </div>
        </>
      )}

      {step === 'result' && (
        <>
          <div className='w-full max-w-sm space-y-6 text-center'>
            <p className='text-2xl font-bold text-success'>{t('scaleCalibration.calibrationDone')}</p>
            {calibrationFactor !== null && (
              <p className='text-lg text-neutral'>
                {t('scaleCalibration.newFactor', { factor: calibrationFactor.toFixed(4) })}
              </p>
            )}
          </div>
          <div className='flex-grow py-2'></div>
          <button type='button' className='button-primary text-lg p-4 w-full' onClick={handleReset}>
            {t('scaleCalibration.recalibrate')}
          </button>
        </>
      )}
    </div>
  );
};

export default ScaleCalibrationWindow;
