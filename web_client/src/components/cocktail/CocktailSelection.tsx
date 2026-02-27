import type React from 'react';
import { useEffect, useState } from 'react';
import { FaSkullCrossbones } from 'react-icons/fa';
import { GrFormNextLink, GrFormPreviousLink } from 'react-icons/gr';
import { IoIosHappy } from 'react-icons/io';
import { MdNoDrinks } from 'react-icons/md';
import { prepareCocktail } from '../../api/cocktails';
import { API_URL } from '../../api/common';
import { Tabs } from '../../constants/tabs';
import { useConfig } from '../../providers/ConfigProvider';
import type { Cocktail, PrepareResult } from '../../types/models';
import { errorToast, scaleCocktail } from '../../utils';
import CloseButton from '../common/CloseButton';
import ProgressModal from './ProgressModal';
import RefillPrompt from './RefillPrompt';
import ServingSizeButtons from './ServingSizeButtons';
import TeamSelection from './TeamSelection';
import { FALLBACK_SERVING_SIZES } from './utils';

interface CocktailModalProps {
  selectedCocktail: Cocktail;
  handleCloseModal: () => void;
  cocktails: Cocktail[];
  setSelectedCocktail: (cocktail: Cocktail) => void;
}

type alcoholState = 'high' | 'low' | 'normal' | 'virgin';

const alcoholFactor = {
  high: 1.25,
  low: 0.75,
  normal: 1,
  virgin: 0,
};

const CocktailSelection: React.FC<CocktailModalProps> = ({
  selectedCocktail,
  handleCloseModal,
  cocktails,
  setSelectedCocktail,
}) => {
  const originalCocktail = structuredClone(selectedCocktail);
  const [alcohol, setAlcohol] = useState<alcoholState>('normal');
  const [displayCocktail, setDisplayCocktail] = useState<Cocktail>(selectedCocktail);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  // Refill state
  const [isRefillOpen, setIsRefillOpen] = useState(false);
  const [refillMessage, setRefillMessage] = useState('');
  const [emptyBottleNumber, setEmptyBottleNumber] = useState(0);
  // Team selection state
  const [isTeamOpen, setIsTeamOpen] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const { config } = useConfig();
  const possibleServingSizes = config.MAKER_USE_RECIPE_VOLUME
    ? [displayCocktail.amount]
    : (config.MAKER_PREPARE_VOLUME ?? FALLBACK_SERVING_SIZES);

  useEffect(() => {
    const initialAlcoholState = selectedCocktail.only_virgin ? 'virgin' : 'normal';
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setAlcohol(initialAlcoholState);
    setDisplayCocktail(initialAlcoholState === 'virgin' ? scaleCocktail(selectedCocktail, 0) : selectedCocktail);
  }, [selectedCocktail]);

  const changeCocktailBy = (number: number) => {
    const currentIndex = cocktails.findIndex((c) => c.id === selectedCocktail.id);
    const nextIndex = (currentIndex + number + cocktails.length) % cocktails.length;
    setSelectedCocktail(cocktails[nextIndex]);
  };

  const handleAlcoholState = (state: alcoholState) => {
    if (state === alcohol) {
      setAlcohol('normal');
      setDisplayCocktail(originalCocktail);
    } else {
      setAlcohol(state);
      setDisplayCocktail(scaleCocktail(originalCocktail, alcoholFactor[state]));
    }
  };

  const prepareCocktailClick = async (amount: number) => {
    if (config.TEAMS_ACTIVE) {
      setSelectedAmount(amount);
      setIsTeamOpen(true);
    } else {
      handlePrepareCocktail(amount);
    }
  };

  const handlePrepareCocktail = async (amount: number, teamName: string | undefined = undefined) => {
    const factor = alcoholFactor[alcohol];
    prepareCocktail(displayCocktail, amount, factor, teamName)
      .then(() => {
        setIsProgressModalOpen(true);
      })
      .catch((error) => {
        const errorReason = error.status as PrepareResult | undefined;
        const refillAllowed = !(config.UI_MAKER_PASSWORD && config.UI_LOCKED_TABS[Tabs.Bottles]);
        if (errorReason === 'NOT_ENOUGH_INGREDIENTS' && refillAllowed) {
          setRefillMessage(error.detail);
          setEmptyBottleNumber(error.bottle);
          setIsRefillOpen(true);
          return;
        }
        errorToast(error);
      });
  };

  const ingredientsWithAmount = displayCocktail.ingredients.filter((ingredient) => ingredient.amount > 0);
  const showAlcoholControls =
    selectedCocktail.ingredients.length > 1 && config.PAYMENT_TYPE === 'Disabled' && !selectedCocktail.only_virgin;
  const machineIngredients = ingredientsWithAmount
    .filter((ingredient) => !ingredient.hand)
    .sort((a, b) => b.amount - a.amount);
  const handIngredients = ingredientsWithAmount
    .filter((ingredient) => ingredient.hand)
    .sort((a, b) => b.amount - a.amount);

  const calculateDisplayPrice = (amount: number, pricePer100: number): string => {
    if (config.PAYMENT_TYPE === 'Disabled') return '';
    const virginMultiplier = alcohol === 'virgin' ? config.PAYMENT_VIRGIN_MULTIPLIER / 100 : 1;
    const rawPrice = ((amount * pricePer100) / 100) * virginMultiplier;
    const roundTo = config.PAYMENT_PRICE_ROUNDING;
    const price = roundTo > 0 ? Math.ceil(rawPrice / roundTo) * roundTo : rawPrice;
    // Determine decimal places from roundTo
    const decimalPlaces = (roundTo.toString().split('.')[1] || '').length;
    const formatted = price.toFixed(decimalPlaces).replace(/\.?0+$/, '');
    return `: ${formatted}€`;
  };

  return (
    <>
      <div className='flex flex-col sm:flex-row items-center md:items-start justify-center w-full h-full'>
        <div className='relative w-full h-full sm:mr-2 mb-2 flex-1'>
          <img
            src={`${API_URL}${selectedCocktail.image}`}
            alt={selectedCocktail.name}
            className='w-full h-full object-cover border-2 border-neutral rounded-lg overflow-hidden'
          />
          <button
            type='button'
            onClick={() => changeCocktailBy(-1)}
            className='absolute left-2 top-1/2 -translate-y-1/2 bg-background opacity-80 rounded-full'
            aria-label='previous'
          >
            <GrFormPreviousLink className='text-primary' size={80} />
          </button>
          <button
            type='button'
            onClick={() => changeCocktailBy(1)}
            className='absolute right-2 top-1/2 -translate-y-1/2 bg-background opacity-80 rounded-full'
            aria-label='next'
          >
            <GrFormNextLink className='text-primary' size={80} />
          </button>
        </div>
        <div className='flex flex-col justify-between items-center w-full flex-1 self-stretch'>
          <div className='flex items-center justify-between mb-2 shrink w-full'>
            {selectedCocktail.ingredients.length > 1 && (
              <span className='ml-4 text-secondary font-bold w-6 text-xl'>{displayCocktail.alcohol}%</span>
            )}
            <div className='flex space-x-2'>
              {selectedCocktail.virgin_available && !selectedCocktail.only_virgin && (
                <button
                  type='button'
                  onClick={() => handleAlcoholState('virgin')}
                  className={`w-8 p-2 rounded-full ${alcohol === 'virgin' ? 'bg-secondary' : 'bg-primary'}`}
                  disabled={selectedCocktail.only_virgin}
                >
                  <MdNoDrinks className='text-background' />
                </button>
              )}
              {showAlcoholControls && (
                <>
                  <button
                    type='button'
                    onClick={() => handleAlcoholState('low')}
                    className={`w-8 p-2 rounded-full ${alcohol === 'low' ? 'bg-secondary' : 'bg-primary'} ${
                      selectedCocktail.only_virgin && 'disabled'
                    }`}
                    disabled={selectedCocktail.only_virgin}
                  >
                    <IoIosHappy className='text-background' />
                  </button>
                  <button
                    type='button'
                    onClick={() => handleAlcoholState('high')}
                    className={`w-8 p-2 rounded-full ${alcohol === 'high' ? 'bg-secondary' : 'bg-primary'} ${
                      selectedCocktail.only_virgin && 'disabled'
                    }`}
                    disabled={selectedCocktail.only_virgin}
                  >
                    <FaSkullCrossbones className='text-background' />
                  </button>
                </>
              )}
            </div>
            <CloseButton onClick={handleCloseModal} />
          </div>
          <div className='flex-grow flex flex-col justify-center w-full'>
            <p className='text-2xl md:text-3xl lg:text-4xl font-bold text-center text-neutral underline mb-2'>
              {alcohol === 'virgin' && 'Virgin '}
              {selectedCocktail.name}
            </p>
            <div className='my-2'>
              <ul className='text-center text-base md:text-lg lg:text-xl space-y-1'>
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
          <ServingSizeButtons
            servingSizes={possibleServingSizes}
            onSelect={prepareCocktailClick}
            getLabel={(amount) => amount + calculateDisplayPrice(amount, displayCocktail.price_per_100_ml)}
          />
        </div>
      </div>
      <RefillPrompt
        isOpen={isRefillOpen}
        bottleNumber={emptyBottleNumber}
        message={refillMessage}
        onClose={() => setIsRefillOpen(false)}
      />
      <ProgressModal
        isOpen={isProgressModalOpen}
        onRequestClose={() => setIsProgressModalOpen(false)}
        progress={0}
        displayName={`${alcohol === 'virgin' ? 'Virgin ' : ''}${displayCocktail.name}`}
        triggerOnClose={handleCloseModal}
      />
      <TeamSelection
        isOpen={isTeamOpen}
        amount={selectedAmount || 0}
        prepareCocktail={handlePrepareCocktail}
        onClose={() => setIsTeamOpen(false)}
      />
    </>
  );
};

export default CocktailSelection;
