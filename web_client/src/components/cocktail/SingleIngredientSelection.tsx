import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaMinus, FaPlus } from 'react-icons/fa';
import { prepareIngredient, useIngredients } from '../../api/ingredients';
import type { Ingredient } from '../../types/models';
import { errorToast } from '../../utils';
import CloseButton from '../common/CloseButton';
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
            <select
              className='select-base w-full !p-3 mb-8'
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
            >
              <option value='' disabled>
                {t('cocktails.selectIngredient')}
              </option>
              {allIngredients
                .filter((ingredient: Ingredient) => ingredient.bottle !== null)
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((ingredient: Ingredient) => (
                  <option key={ingredient.id} value={ingredient.id}>
                    {ingredient.name}
                  </option>
                ))}
            </select>

            <div className='flex items-center space-x-8 mb-8'>
              <button
                type='button'
                className='button-primary p-4 flex justify-center items-center'
                onClick={handleDecrement}
              >
                <FaMinus size={30} />
              </button>
              <span className='text-secondary text-3xl'>{amount}</span>
              <button
                type='button'
                className='button-primary button-primary p-4 flex justify-center items-center'
                onClick={handleIncrement}
              >
                <FaPlus size={30} />
              </button>
            </div>

            <button
              type='button'
              className={`${selectedId ? 'button-primary-filled' : 'button-neutral'} p-2 w-full text-xl`}
              onClick={handleSpend}
              disabled={!selectedId}
            >
              {t('cocktails.spend')}
            </button>
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
