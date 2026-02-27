import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaQuestion } from 'react-icons/fa';
import { MdNoDrinks } from 'react-icons/md';
import { prepareCocktail } from '../../api/cocktails';
import { API_URL } from '../../api/common';
import { Tabs } from '../../constants/tabs';
import { useConfig } from '../../providers/ConfigProvider';
import type { Cocktail, PrepareResult } from '../../types/models';
import { errorToast } from '../../utils';
import CloseButton from '../common/CloseButton';
import ProgressModal from './ProgressModal';
import RefillPrompt from './RefillPrompt';
import ServingSizeButtons from './ServingSizeButtons';
import TeamSelection from './TeamSelection';
import { FALLBACK_SERVING_SIZES } from './utils';

interface RandomCocktailSelectionProps {
  handleCloseModal: () => void;
  cocktails: Cocktail[];
}

const RandomCocktailSelection: React.FC<RandomCocktailSelectionProps> = ({ handleCloseModal, cocktails }) => {
  const [isVirgin, setIsVirgin] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [chosenCocktailName, setChosenCocktailName] = useState('');
  const [isRefillOpen, setIsRefillOpen] = useState(false);
  const [refillMessage, setRefillMessage] = useState('');
  const [emptyBottleNumber, setEmptyBottleNumber] = useState(0);
  const [isTeamOpen, setIsTeamOpen] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const { config } = useConfig();
  const { t } = useTranslation();

  const pool = isVirgin ? cocktails.filter((c) => c.virgin_available) : cocktails.filter((c) => !c.only_virgin);
  const hasVirginOption = cocktails.some((c) => c.virgin_available);

  const possibleServingSizes = config.MAKER_USE_RECIPE_VOLUME
    ? [0]
    : (config.MAKER_PREPARE_VOLUME ?? FALLBACK_SERVING_SIZES);

  const pickAndPrepare = async (amount: number, teamName: string | undefined = undefined) => {
    if (pool.length === 0) return;
    const chosen = pool[Math.floor(Math.random() * pool.length)];
    const factor = isVirgin ? 0 : 1;
    const prepareAmount = config.MAKER_USE_RECIPE_VOLUME ? chosen.amount : amount;
    const displayPrefix = isVirgin ? 'Virgin ' : '';
    setChosenCocktailName(`${displayPrefix}${chosen.name}`);
    prepareCocktail(chosen, prepareAmount, factor, teamName)
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

  const handlePrepareClick = (amount: number) => {
    if (config.TEAMS_ACTIVE) {
      setSelectedAmount(amount);
      setIsTeamOpen(true);
    } else {
      pickAndPrepare(amount);
    }
  };

  return (
    <>
      <div className='flex flex-col sm:flex-row items-center md:items-start justify-center w-full h-full'>
        <div className='relative w-full h-full sm:mr-2 mb-2 flex-1'>
          <img
            src={`${API_URL}/static/default/default.jpg`}
            alt={t('cocktails.randomCocktail')}
            className='w-full h-full object-cover border-2 border-neutral rounded-lg overflow-hidden'
          />
        </div>
        <div className='flex flex-col justify-between items-center w-full flex-1 self-stretch'>
          <div className='flex items-center justify-between mb-2 shrink w-full'>
            <span className='ml-4 text-secondary font-bold w-6 text-xl'>?</span>
            <div className='flex space-x-2'>
              {hasVirginOption && (
                <button
                  type='button'
                  onClick={() => setIsVirgin(!isVirgin)}
                  className={`w-8 p-2 rounded-full ${isVirgin ? 'bg-secondary' : 'bg-primary'}`}
                >
                  <MdNoDrinks className='text-background' />
                </button>
              )}
            </div>
            <CloseButton onClick={handleCloseModal} />
          </div>
          <div className='flex-grow flex flex-col justify-center w-full'>
            <p className='text-2xl md:text-3xl lg:text-4xl font-bold text-center text-neutral underline mb-2'>
              {t('cocktails.randomCocktail')}
            </p>
            <div className='my-2 flex flex-col items-center justify-center gap-4'>
              <FaQuestion className='text-secondary' size={60} />
              <p className='text-center text-xl text-text'>{t('cocktails.beSurprised')}</p>
            </div>
          </div>
          <ServingSizeButtons
            servingSizes={possibleServingSizes}
            onSelect={handlePrepareClick}
            getLabel={config.MAKER_USE_RECIPE_VOLUME ? () => t('cocktails.beSurprised') : undefined}
            disabled={pool.length === 0}
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
        displayName={chosenCocktailName}
        triggerOnClose={handleCloseModal}
      />
      <TeamSelection
        isOpen={isTeamOpen}
        amount={selectedAmount || 0}
        prepareCocktail={(amount, teamName) => pickAndPrepare(amount, teamName)}
        onClose={() => setIsTeamOpen(false)}
      />
    </>
  );
};

export default RandomCocktailSelection;
