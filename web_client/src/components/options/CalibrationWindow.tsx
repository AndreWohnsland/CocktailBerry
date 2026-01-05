import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaMinus, FaPlus } from 'react-icons/fa';
import { calibrateBottle } from '../../api/bottles';
import { updateOptions } from '../../api/options';
import { useConfig } from '../../providers/ConfigProvider';
import { executeAndShow } from '../../utils';
import NumberInput from '../common/NumberInput';
import TextHeader from '../common/TextHeader';

const MAX_DEVIATION_FACTOR = 20;

type CalibrationStep = 'target' | 'measure';

const CalibrationWindow = () => {
  const [step, setStep] = useState<CalibrationStep>('target');
  const [channel, setChannel] = useState(1);
  const [amount, setAmount] = useState(10);
  const [targetVolume, setTargetVolume] = useState(0);
  const [measuredVolume, setMeasuredVolume] = useState(0);
  const { config, refetchConfig } = useConfig();
  const { t } = useTranslation();

  const currentFlow = config?.PUMP_CONFIG?.[channel - 1]?.volume_flow || 0;

  const calculateNewFlow = (): number | null => {
    const measured = measuredVolume;
    if (!measured || measured <= 0 || targetVolume <= 0) {
      return null;
    }

    const deviationFactor = targetVolume / measured;
    if (deviationFactor > MAX_DEVIATION_FACTOR || deviationFactor < 1 / MAX_DEVIATION_FACTOR) {
      return null;
    }

    return Math.round(currentFlow * deviationFactor * 10) / 10;
  };

  const newFlow = calculateNewFlow();

  const handleStartPumping = async () => {
    const success = await executeAndShow(() => calibrateBottle(channel, amount));
    if (!success) return;
    setTargetVolume((prev) => prev + amount);
  };

  const handleNext = () => {
    setStep('measure');
  };

  const handleContinuePumping = () => {
    setStep('target');
  };

  const handleApplyNewFlow = async () => {
    if (newFlow === null) return;

    const updatedPumpConfig = [...config.PUMP_CONFIG];
    updatedPumpConfig[channel - 1] = {
      ...updatedPumpConfig[channel - 1],
      volume_flow: newFlow,
    };
    await executeAndShow(() => updateOptions({ PUMP_CONFIG: updatedPumpConfig as any }));
    await refetchConfig();
    handleReset();
  };

  const handleReset = () => {
    setStep('target');
    setTargetVolume(0);
    setMeasuredVolume(0);
  };

  return (
    <div className='flex flex-col justify-between items-center p-4 w-full h-full max-w-md max-h-[40rem]'>
      <TextHeader text={t('calibration.pumpCalibrationProgram')} />

      <div className='text-center text-lg font-semibold text-neutral mt-2'>
        <span className='mr-4'>{t('calibration.targetAmount', { amount: targetVolume })}</span>
        <button className='button-primary text-sm px-3 py-1' onClick={handleReset}>
          {t('calibration.reset')}
        </button>
      </div>

      <div className='flex-grow py-2'></div>

      {step === 'target' && (
        <>
          <div className='grid grid-cols-3 gap-4 items-center w-full max-w-sm'>
            <div className='text-center'>
              <div className='text-4xl font-bold'>{channel}</div>
            </div>
            <div className='flex flex-col space-y-2'>
              <button
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setChannel(Math.min(channel + 1, config.MAKER_NUMBER_BOTTLES))}
                disabled={targetVolume > 0}
              >
                <FaPlus size={30} />
              </button>
              <button
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setChannel(Math.max(1, channel - 1))}
                disabled={targetVolume > 0}
              >
                <FaMinus size={30} />
              </button>
            </div>
            <div className='text-center text-lg font-semibold text-neutral'>{t('calibration.pump')}</div>

            <div className='text-center'>
              <div className='text-4xl font-bold'>{amount}</div>
            </div>
            <div className='flex flex-col space-y-2'>
              <button
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setAmount(amount + 10)}
              >
                <FaPlus size={30} />
              </button>
              <button
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setAmount(Math.max(10, amount - 10))}
              >
                <FaMinus size={30} />
              </button>
            </div>
            <div className='text-center text-lg font-semibold text-neutral'>{t('calibration.amount')}</div>
          </div>
          <div className='flex-grow py-2'></div>
          <div className='w-full space-y-3'>
            {targetVolume > 0 && (
              <button className='button-primary text-lg p-4 w-full' onClick={handleNext}>
                {t('calibration.next')}
              </button>
            )}
            <button className='button-primary-filled text-lg p-4 w-full' onClick={handleStartPumping}>
              {t('start')}
            </button>
          </div>
        </>
      )}

      {step === 'measure' && (
        <>
          <div className='w-full max-w-sm space-y-6'>
            <div className='space-y-2'>
              <label className='block text-center text-lg font-semibold text-neutral'>
                {t('calibration.measuredAmount')}
              </label>
              <NumberInput value={measuredVolume} handleInputChange={(v) => setMeasuredVolume(v)} suffix='ml' />
            </div>

            <div className='text-center text-lg font-semibold text-neutral min-h-[2rem]'>
              {newFlow !== null
                ? t('calibration.newVolumeFlow', { flow: newFlow })
                : measuredVolume
                ? t('calibration.deviationTooLarge')
                : t('calibration.enterMeasuredAmount')}
            </div>
          </div>

          <div className='flex-grow py-2'></div>

          <div className='w-full space-y-3'>
            <button className='button-primary text-lg p-4 w-full' onClick={handleContinuePumping}>
              {t('calibration.continuePumping')}
            </button>
            <button
              className='button-primary-filled text-lg p-4 w-full'
              onClick={handleApplyNewFlow}
              disabled={newFlow === null}
            >
              {t('calibration.apply')}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default CalibrationWindow;
