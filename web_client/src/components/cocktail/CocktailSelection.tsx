import React, { useState } from 'react';
import { Cocktail } from '../../types/models';
import { FaSkullCrossbones, FaGlassMartiniAlt, FaWineGlassAlt } from 'react-icons/fa';
import { IoIosHappy } from 'react-icons/io';
import { PiPintGlassFill } from 'react-icons/pi';
import { ImMug } from 'react-icons/im';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { TbGlassChampagne } from 'react-icons/tb';
import { MdNoDrinks } from 'react-icons/md';
import { scaleCocktail } from '../../utils';
import { prepareCocktail } from '../../api/cocktails';
import ProgressModal from './ProgressModal';
import { toast, ToastContainer } from 'react-toastify';

interface CocktailModalProps {
  selectedCocktail: Cocktail;
  handleCloseModal: () => void;
}

type alcoholState = 'high' | 'low' | 'normal' | 'virgin';

const mlAmounts = [200, 250, 300];
const icons = [TbGlassChampagne, FaWineGlassAlt, FaGlassMartiniAlt, PiPintGlassFill, ImMug];
const alcoholFactor = {
  high: 1.25,
  low: 0.75,
  normal: 1,
  virgin: 0,
};

const CocktailSelection: React.FC<CocktailModalProps> = ({ selectedCocktail, handleCloseModal }) => {
  const originalCocktail = JSON.parse(JSON.stringify(selectedCocktail));
  const [alcohol, setAlcohol] = useState<alcoholState>('normal');
  const [displayCocktail, setDisplayCocktail] = useState<Cocktail>(selectedCocktail);
  const [isProgressModalOpen, setProgressModalOpen] = useState(false);

  const handleAlcoholState = (state: alcoholState) => {
    if (state === alcohol) {
      setAlcohol('normal');
      setDisplayCocktail(originalCocktail);
    } else {
      setAlcohol(state);
      const factor = alcoholFactor[state];
      setDisplayCocktail(scaleCocktail(originalCocktail, factor));
    }
  };

  const prepareCocktailClick = async (amount: number) => {
    const factor = alcoholFactor[alcohol];
    prepareCocktail(displayCocktail, amount, factor, alcohol === 'virgin')
      .then((status) => {
        console.log(status);
        setProgressModalOpen(true);
      })
      .catch((error) => {
        const errorMessage = error.response?.data?.detail?.detail || 'An error occurred';
        toast(errorMessage, {
          toastId: 'cocktail-error',
          pauseOnHover: false,
        });
      });
  };

  const machineIngredients = displayCocktail.ingredients
    .filter((ingredient) => !ingredient.hand)
    .sort((a, b) => b.amount - a.amount);
  const handIngredients = displayCocktail.ingredients
    .filter((ingredient) => ingredient.hand)
    .sort((a, b) => b.amount - a.amount);

  const getIconIndex = (index: number, length: number) => {
    const middle = Math.floor(length / 2);
    return middle + index - Math.floor(length / 2);
  };

  return (
    <>
      <ToastContainer position='top-center' />
      <div className='flex flex-col md:flex-row items-center md:items-start justify-center w-full h-full'>
        <div className='w-full flex items-center justify-center border-2 border-neutral rounded-lg box-border overflow-hidden h-full md:mr-4 flex-1'>
          <img
            src={`${import.meta.env.VITE_APP_API_URL}${selectedCocktail.image}`}
            alt={selectedCocktail.name}
            className='w-full h-full object-cover'
          />
        </div>
        <div className='flex flex-col justify-between items-center w-full flex-1 self-stretch'>
          <div className='flex items-center justify-between mb-2 shrink w-full'>
            {/* Left-Aligned Section */}
            <span className='ml-4 text-secondary font-bold w-6 text-xl'>{displayCocktail.alcohol}%</span>

            {/* Center Section */}
            <div className='flex space-x-2'>
              <button
                onClick={() => handleAlcoholState('high')}
                className={`w-8 p-2 rounded-full ${alcohol === 'high' ? 'bg-secondary' : 'bg-primary'}`}
              >
                <FaSkullCrossbones className='text-background' />
              </button>
              <button
                onClick={() => handleAlcoholState('low')}
                className={`w-8 p-2 rounded-full ${alcohol === 'low' ? 'bg-secondary' : 'bg-primary'}`}
              >
                <IoIosHappy className='text-background' />
              </button>
              {selectedCocktail.virgin_available && (
                <button
                  onClick={() => handleAlcoholState('virgin')}
                  className={`w-8 p-2 rounded-full ${alcohol === 'virgin' ? 'bg-secondary' : 'bg-primary'}`}
                >
                  <MdNoDrinks className='text-background' />
                </button>
              )}
            </div>

            {/* Right-Aligned Section */}
            <button onClick={handleCloseModal} aria-label='close'>
              <AiOutlineCloseCircle className='text-danger' size={34} />
            </button>
          </div>
          <div>
            <h2 className='text-2xl font-bold text-center text-neutral underline'>{selectedCocktail.name}</h2>
            <div className='mt-2'>
              <ul className='text-center'>
                {machineIngredients.map((ingredient) => (
                  <li key={ingredient.id} className='text-text'>
                    {ingredient.name}:
                    <span className='text-secondary ml-2'>
                      {ingredient.amount} {ingredient.unit}
                    </span>
                  </li>
                ))}
                {handIngredients.map((ingredient) => (
                  <li key={ingredient.id} className='text-text'>
                    <span className='text-neutral mr-2'>[Hand]</span>
                    {ingredient.name}
                    <span className='text-secondary ml-2'>
                      {ingredient.amount} {ingredient.unit}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className='flex justify-center items-end w-full mt-auto'>
            {mlAmounts.map((amount, index) => {
              const Icon = icons[getIconIndex(index, mlAmounts.length)];
              return (
                <button
                  key={amount}
                  className='button-primary-filled m-1 w-full max-w-xs py-2 rounded-lg flex items-center justify-center text-xl'
                  onClick={() => prepareCocktailClick(amount)}
                >
                  <Icon className='mr-2 text-2xl' />
                  {amount}
                </button>
              );
            })}
          </div>
        </div>
      </div>
      <ProgressModal
        isOpen={isProgressModalOpen}
        onRequestClose={() => setProgressModalOpen(false)}
        progress={0}
        cocktailName={displayCocktail.name}
        triggerOnClose={handleCloseModal}
      />
    </>
  );
};

export default CocktailSelection;