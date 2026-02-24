import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { updateBottle } from '../../api/bottles';
import type { Bottle, Ingredient } from '../../types/models';
import { errorToast, executeAndShow } from '../../utils';
import Modal from 'react-modal';
import Button from '../common/Button';
import CloseButton from '../common/CloseButton';
import DropDown from '../common/DropDown';
import MinMaxInput from '../common/MinMaxInput';
import ProgressBar from '../common/ProgressBar';

interface BottleProps {
  bottle: Bottle;
  isToggled: boolean;
  onToggle: () => void;
  freeIngredients: Ingredient[];
  setFreeIngredients: (value: Ingredient[]) => void;
}

const BottleComponent: React.FC<BottleProps> = ({
  bottle,
  isToggled,
  onToggle,
  freeIngredients,
  setFreeIngredients,
}) => {
  const [selectedIngredientId, setSelectedIngredientId] = useState(bottle.ingredient?.id ?? 0);
  const [selectedIngredient, setSelectedIngredient] = useState<Ingredient | undefined>(bottle.ingredient);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tempFillLevel, setTempFillLevel] = useState(selectedIngredient?.fill_level ?? 0);
  const { t } = useTranslation();

  const getClass = () => {
    let color = 'border-primary text-primary';
    if (isToggled) {
      color = 'border-secondary bg-secondary text-background';
    }
    return `max-w-40 px-4 ml-2 border-2 font-bold rounded-md ${color}`;
  };

  const openModal = () => {
    if (!selectedIngredient) return;
    setTempFillLevel(Math.max(selectedIngredient?.fill_level, 0) ?? 0);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleAdjustment = async () => {
    if (!selectedIngredient) return;
    executeAndShow(() => updateBottle(bottle.number, selectedIngredient.id, tempFillLevel)).then((success) => {
      if (!success) return;
      setSelectedIngredient({ ...selectedIngredient, fill_level: tempFillLevel });
      setIsModalOpen(false);
    });
  };

  const fillPercent = Math.max(
    Math.round(((selectedIngredient?.fill_level ?? 0) / (selectedIngredient?.bottle_volume ?? 1)) * 100),
    0,
  );

  const handleSelectionChange = async (value: string) => {
    const newIngredientId = Number.parseInt(value, 10);
    let possibleIngredients = freeIngredients;
    let newIngredient: Ingredient | undefined;

    // Find the new ingredient only if the selected ID is not 0
    if (newIngredientId !== 0) {
      newIngredient = freeIngredients.find((ingredient) => ingredient.id === newIngredientId);
      if (newIngredient) {
        // remove the selected ingredient from possible ones
        possibleIngredients = possibleIngredients.filter((ingredient) => ingredient.id !== newIngredientId);
      }
    }

    // add the old (previous) ingredient to the possible ones
    if (selectedIngredient) {
      possibleIngredients = [...possibleIngredients, selectedIngredient];
    }

    try {
      await updateBottle(bottle.number, newIngredientId);
      setSelectedIngredient(newIngredient);
      setSelectedIngredientId(newIngredientId);
      setFreeIngredients(possibleIngredients);
    } catch (error) {
      console.error('Error updating bottle:', error);
      errorToast(error);
    }
  };

  return (
    <>
      <div className='h-full grid grid-cols-2 place-items-stretch gap-2 w-full mb-2 sm:mb-0'>
        <div className='flex flex-row col-span-2 sm:col-span-1 max-h-20'>
          <div className='place-content-center text-center text-secondary font-bold text-2xl mx-1 w-12'>
            {bottle.number}
          </div>
          <DropDown
            className='block w-full !p-2'
            id={`ingredient-bottle-${bottle.number}`}
            value={selectedIngredientId.toString()}
            allowedValues={[
              ...(selectedIngredient
                ? [{ value: selectedIngredient.id.toString(), label: selectedIngredient.name }]
                : []),
              { value: '0', label: '-' },
              ...freeIngredients
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((ingredient) => ({ value: ingredient.id.toString(), label: ingredient.name })),
            ]}
            handleInputChange={handleSelectionChange}
          />
          <button type='button' onClick={onToggle} className={getClass()}>
            {t('new')}
          </button>
        </div>
        <ProgressBar fillPercent={fillPercent} onClick={openModal} className='col-span-2 sm:col-span-1 max-h-20' />
      </div>
      <Modal
        isOpen={isModalOpen}
        onRequestClose={closeModal}
        className='modal slim'
        overlayClassName='overlay z-20'
        preventScroll
      >
        <div className='px-1 rounded w-full h-full flex flex-col'>
          <div className='flex justify-between items-center mb-2'>
            <p className='text-xl font-bold text-secondary'>{selectedIngredient?.name ?? 'Ingredient'}</p>
            <CloseButton onClick={closeModal} />
          </div>
          <div className='w-full h-full flex flex-col px-2'>
            <p className='text-neutral text-center mt-4'>
              {t('bottles.adjustHeader', { maximum: selectedIngredient?.bottle_volume })}
            </p>
            <div className='flex-grow'></div>
            <MinMaxInput
              value={tempFillLevel}
              onChange={setTempFillLevel}
              max={selectedIngredient?.bottle_volume ?? 0}
              delta={50}
              className='mb-4'
            />
            <div className='flex-grow'></div>
          </div>
          <Button label={t('save')} filled className='w-full' onClick={handleAdjustment} />
        </div>
      </Modal>
    </>
  );
};

export default BottleComponent;
