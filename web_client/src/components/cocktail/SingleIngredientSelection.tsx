import React, { useState } from 'react';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { useIngredients, prepareIngredient } from '../../api/ingredients';
import { Ingredient } from '../../types/models';
import { errorToast } from '../../utils';
import { FaMinus, FaPlus } from 'react-icons/fa';
import ProgressModal from './ProgressModal';
import { useTranslation } from 'react-i18next';

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
          <button onClick={onClose}>
            <AiOutlineCloseCircle className='text-danger' size={34} />
          </button>
        </div>

        <div className='max-w-md w-full h-full flex flex-col p-2'>
          <div className='flex-grow'></div>
          <div className='flex flex-col items-center'>
            <select
              className='select-base w-full !p-3 mb-8'
              value={selectedId || ''}
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
              <button className='button-primary p-4 flex justify-center items-center' onClick={handleDecrement}>
                <FaMinus size={30} />
              </button>
              <span className='text-secondary text-3xl'>{amount}</span>
              <button
                className='button-primary button-primary p-4 flex justify-center items-center'
                onClick={handleIncrement}
              >
                <FaPlus size={30} />
              </button>
            </div>

            <button
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
        displayName={allIngredients.find((ingredient) => ingredient.id === selectedId)?.name || ''}
        triggerOnClose={onClose}
      />
    </>
  );
};

export default SingleIngredientSelection;
