import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaInfoCircle, FaMinus, FaPlus } from 'react-icons/fa';
import { calibrateBottle } from '../../api/bottles';
import { updateIngredient, useIngredients } from '../../api/ingredients';
import { updateOptions } from '../../api/options';
import { useConfig } from '../../providers/ConfigProvider';
import type { Ingredient, PossibleConfigValue } from '../../types/models';
import { executeAndShow } from '../../utils';
import DropDown from '../common/DropDown';
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
  const [selectedIngredientId, setSelectedIngredientId] = useState<string>('');
  const { config, refetchConfig } = useConfig();
  const { data: ingredients = [], refetch: refetchIngredients } = useIngredients(false);
  const { t } = useTranslation();

  const currentFlow = config?.PUMP_CONFIG?.[channel - 1]?.volume_flow || 0;
  const selectedIngredient: Ingredient | null =
    ingredients.find((i) => i.id.toString() === selectedIngredientId) ?? null;

  const calculateDeviationFactor = (): number | null => {
    const measured = measuredVolume;
    if (!measured || measured <= 0 || targetVolume <= 0) {
      return null;
    }

    const deviationFactor = measured / targetVolume;
    if (deviationFactor > MAX_DEVIATION_FACTOR || deviationFactor < 1 / MAX_DEVIATION_FACTOR) {
      return null;
    }

    return deviationFactor;
  };

  const deviationFactor = calculateDeviationFactor();
  const newFlow = deviationFactor ? Math.round(currentFlow * deviationFactor * 10) / 10 : null;
  const newPumpSpeed = deviationFactor ? Math.round(100 * deviationFactor) : null;

  const isIngredientCalibration = selectedIngredientId !== '';
  const hasValidCalibration = isIngredientCalibration ? newPumpSpeed !== null : newFlow !== null;

  const getCalibrationMessage = () => {
    if (isIngredientCalibration) {
      if (newPumpSpeed) return t('calibration.newPumpSpeed', { speed: newPumpSpeed });
      if (measuredVolume) return t('calibration.deviationTooLarge');
      return t('calibration.enterMeasuredAmount');
    }
    if (newFlow) return t('calibration.newVolumeFlow', { flow: newFlow });
    if (measuredVolume) return t('calibration.deviationTooLarge');
    return t('calibration.enterMeasuredAmount');
  };

  const ingredientDropdownOptions = [
    { value: '', label: '-' },
    ...[...ingredients]
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((i) => ({ value: i.id.toString(), label: i.name })),
  ];

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
    await executeAndShow(() => updateOptions({ PUMP_CONFIG: updatedPumpConfig as unknown as PossibleConfigValue }));
    await refetchConfig();
    handleReset();
  };

  const handleApplyIngredientPumpSpeed = async () => {
    if (newPumpSpeed === null || !selectedIngredient) return;

    await executeAndShow(() =>
      updateIngredient({
        id: selectedIngredient.id,
        name: selectedIngredient.name,
        alcohol: selectedIngredient.alcohol,
        bottle_volume: selectedIngredient.bottle_volume,
        fill_level: selectedIngredient.fill_level,
        cost: selectedIngredient.cost,
        pump_speed: newPumpSpeed,
        hand: selectedIngredient.hand,
        unit: selectedIngredient.unit,
      }),
    );
    await refetchIngredients();
    handleReset();
  };

  const handleApplyCalibration = async () => {
    if (isIngredientCalibration) {
      await handleApplyIngredientPumpSpeed();
    } else {
      await handleApplyNewFlow();
    }
  };

  const handleReset = () => {
    setStep('target');
    setTargetVolume(0);
    setMeasuredVolume(0);
    setSelectedIngredientId('');
  };

  return (
    <div className='flex flex-col justify-between items-center p-4 w-full h-full max-w-md max-h-[40rem]'>
      <TextHeader text={t('calibration.pumpCalibrationProgram')} />

      <div className='text-center text-lg font-semibold text-neutral mt-2'>
        <span className='mr-4'>{t('calibration.targetAmount', { amount: targetVolume })}</span>
        <button type='button' className='button-primary text-sm px-3 py-1' onClick={handleReset}>
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
                type='button'
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setChannel(Math.min(channel + 1, config.MAKER_NUMBER_BOTTLES))}
                disabled={targetVolume > 0}
              >
                <FaPlus size={30} />
              </button>
              <button
                type='button'
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
                type='button'
                className='button-primary p-2 flex justify-center items-center'
                onClick={() => setAmount(amount + 10)}
              >
                <FaPlus size={30} />
              </button>
              <button
                type='button'
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
              <button type='button' className='button-primary text-lg p-4 w-full' onClick={handleNext}>
                {t('calibration.next')}
              </button>
            )}
            <button type='button' className='button-primary-filled text-lg p-4 w-full' onClick={handleStartPumping}>
              {t('start')}
            </button>
          </div>
        </>
      )}

      {step === 'measure' && (
        <>
          <div className='w-full max-w-sm space-y-6'>
            <div className='space-y-2'>
              <label className='block text-center text-lg font-semibold text-neutral' htmlFor='measured-volume'>
                {t('calibration.measuredAmount')}
              </label>
              <NumberInput
                id='measured-volume'
                value={measuredVolume}
                handleInputChange={(v) => setMeasuredVolume(v)}
                suffix='ml'
              />
            </div>

            <div className='space-y-2'>
              <label
                className='flex items-center justify-center gap-2 text-lg font-semibold text-neutral'
                htmlFor='ingredient-calibration'
              >
                {t('calibration.ingredientCalibration')}
                <FaInfoCircle
                  className='text-neutral cursor-help'
                  title={t('calibration.ingredientCalibrationTooltip')}
                />
              </label>
              <DropDown
                id='ingredient-calibration'
                value={selectedIngredientId}
                allowedValues={ingredientDropdownOptions}
                handleInputChange={(v) => setSelectedIngredientId(v)}
              />
            </div>

            <div className='text-center text-lg font-semibold text-neutral min-h-[2rem]'>{getCalibrationMessage()}</div>
          </div>

          <div className='flex-grow py-2'></div>

          <div className='w-full space-y-3'>
            <button type='button' className='button-primary text-lg p-4 w-full' onClick={handleContinuePumping}>
              {t('calibration.continuePumping')}
            </button>
            <button
              type='button'
              className='button-primary-filled text-lg p-4 w-full'
              onClick={handleApplyCalibration}
              disabled={!hasValidCalibration}
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
