import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { prepareIngredient, useIngredients } from '../../api/ingredients';
import type { Ingredient } from '../../types/models';
import { errorToast } from '../../utils';
import Button from '../common/Button';
import CloseButton from '../common/CloseButton';
import DropDown from '../common/DropDown';
import StepperControl from '../common/StepperControl';
import ProgressModal from './ProgressModal';

interface SingleIngredientSelectionProps {
  onClose: () => void;
}

const SingleIngredientSelection: React.FC<SingleIngredientSelectionProps> = ({ onClose }) => {
  const { data: allIngredients = [] } = useIngredients(false, true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [amount, setAmount] = useState<number>(10);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const { t } = useTranslation();

  const handleDecrement = () => {
    setAmount((prev) => Math.max(10, prev - 10));
  };

  const handleIncrement = () => {
    setAmount((prev) => prev + 10);
  };

  const handleSpend = async () => {
    if (!selectedId) return;
    prepareIngredient(selectedId, amount)
      .then(() => {
        setIsProgressModalOpen(true);
      })
      .catch((error) => {
        errorToast(error);
      });
  };

  return (
    <>
      <div className='w-full h-full flex flex-col justify-center items-center'>
        <div className='flex justify-end w-full'>
          <CloseButton onClick={onClose} />
        </div>

        <div className='max-w-md w-full h-full flex flex-col p-2'>
          <div className='flex-grow'></div>
          <div className='flex flex-col items-center'>
            <DropDown
              className='w-full !p-3 mb-8'
              value={selectedId?.toString() ?? ''}
              placeholder={t('cocktails.selectIngredient')}
              allowedValues={allIngredients
                .filter((ingredient: Ingredient) => ingredient.bottle !== null)
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((ingredient: Ingredient) => ({
                  value: ingredient.id.toString(),
                  label: ingredient.name,
                }))}
              handleInputChange={(v) => setSelectedId(Number(v))}
            />

            <StepperControl
              value={amount}
              onDecrement={handleDecrement}
              onIncrement={handleIncrement}
              size='lg'
              className='mb-8'
            />

            <Button
              filled={!!selectedId}
              style={selectedId ? 'primary' : 'neutral'}
              label={t('cocktails.spend')}
              textSize='lg'
              disabled={!selectedId}
              className='w-full'
              onClick={handleSpend}
            />
          </div>
          <div className='flex-grow'></div>
        </div>
      </div>
      <ProgressModal
        isOpen={isProgressModalOpen}
        onRequestClose={() => setIsProgressModalOpen(false)}
        progress={0}
        displayName={allIngredients.find((ingredient) => ingredient.id === selectedId)?.name ?? ''}
        triggerOnClose={onClose}
      />
    </>
  );
};

export default SingleIngredientSelection;
