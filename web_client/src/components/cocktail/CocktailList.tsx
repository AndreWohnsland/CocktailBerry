import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MdNoDrinks } from 'react-icons/md';
import Modal from 'react-modal';
import { useCocktails } from '../../api/cocktails';
import { API_URL } from '../../api/common';
import { usePaymentWebSocket } from '../../api/payment';
import { useConfig } from '../../providers/ConfigProvider';
import { Cocktail } from '../../types/models';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import LockScreen from '../common/LockScreen';
import SearchBar from '../common/SearchBar';
import UserDisplay from '../common/UserDisplay';
import CocktailSelection from './CocktailSelection';
import SingleIngredientSelection from './SingleIngredientSelection';

const CocktailList: React.FC = () => {
  const { config } = useConfig();
  const { data: cocktails, error, isLoading } = useCocktails(true, config.MAKER_MAX_HAND_INGREDIENTS ?? 0);
  const [selectedCocktail, setSelectedCocktail] = useState<Cocktail | null>(null);
  const [singleIngredientOpen, setSingleIngredientOpen] = useState(false);
  const [search, setSearch] = useState<string | null>(null);
  const [showOnlyVirginPossible, setShowOnlyVirginPossible] = useState(false);
  const { t } = useTranslation();

  // Use payment websocket if payment is active
  const { user, cocktails: paymentCocktails, isConnected } = usePaymentWebSocket(config.PAYMENT_ACTIVE ?? false);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  // Show lock screen if payment is active, lock screen is enabled, and no user is logged in
  // additionally if a cocktail is selected, we cannot show this because otherwise directly after preparation, this is shown again
  if (config.PAYMENT_ACTIVE && config.PAYMENT_LOCK_SCREEN_NO_USER && !user?.nfc_id && selectedCocktail === null) {
    return <LockScreen title={t('lockScreen.paymentTitle')} message={t('lockScreen.paymentMessage')} />;
  }

  const handleCloseModal = () => {
    setSelectedCocktail(null);
  };

  // Use payment cocktails if payment is active, connected, and has data
  // Otherwise fall back to regular cocktails
  let displayedCocktails = cocktails;
  if (config.PAYMENT_ACTIVE && isConnected && paymentCocktails && paymentCocktails.length > 0) {
    displayedCocktails = paymentCocktails;
  }

  if (search) {
    displayedCocktails = displayedCocktails?.filter(
      (cocktail) =>
        cocktail.name.toLowerCase().includes(search.toLowerCase()) ||
        cocktail.ingredients.some((ingredient) => ingredient.name.toLowerCase().includes(search.toLowerCase())),
    );
  }
  if (search !== null && showOnlyVirginPossible) {
    displayedCocktails = displayedCocktails?.filter((cocktail) => cocktail.virgin_available);
    displayedCocktails = displayedCocktails?.map((cocktail) => {
      return { ...cocktail, only_virgin: true };
    });
  }

  const virginToggleButton = (
    <button
      onClick={() => setShowOnlyVirginPossible(!showOnlyVirginPossible)}
      className={`h-10 w-10 flex items-center justify-center p-2 !border pointer-events-auto ${
        showOnlyVirginPossible ? 'button-secondary' : 'button-primary'
      }`}
    >
      <MdNoDrinks size={20} />
    </button>
  );

  return (
    <div className='px-2 centered max-w-7xl'>
      {(config.PAYMENT_ACTIVE ?? false) && <UserDisplay user={user} />}
      <SearchBar search={search} setSearch={setSearch} afterInput={virginToggleButton} />
      <div className='flex flex-wrap gap-3 justify-center items-center w-full mb-4'>
        {displayedCocktails
          ?.sort((a, b) => a.name.localeCompare(b.name))
          .map((cocktail) => {
            const isNotAllowed = config.PAYMENT_ACTIVE && !cocktail.is_allowed;
            const shouldHide = config.PAYMENT_ACTIVE && !config.PAYMENT_SHOW_NOT_POSSIBLE && isNotAllowed;

            if (shouldHide) {
              return null;
            }

            return (
              <div
                key={cocktail.id}
                className={`border-2 rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold ${
                  isNotAllowed
                    ? 'border-neutral bg-neutral text-background opacity-50 cursor-not-allowed'
                    : 'border-primary active:border-secondary bg-primary active:bg-secondary text-background cursor-pointer'
                }`}
                onClick={() => !isNotAllowed && setSelectedCocktail(cocktail)}
                role='button'
              >
                <p className='text-center py-1 flex items-center justify-center'>
                  {cocktail.virgin_available && (
                    <MdNoDrinks
                      className={`mr-2 ${cocktail.only_virgin && 'border-2 border-background rounded-full'}`}
                    />
                  )}
                  {cocktail.name}
                </p>
                <div className='relative w-full' style={{ paddingTop: '100%' }}>
                  <img
                    src={`${API_URL}${cocktail.image}`}
                    alt={cocktail.name}
                    className='absolute top-0 left-0 w-full h-full object-cover'
                  />
                </div>
              </div>
            );
          })}
        {config.MAKER_ADD_SINGLE_INGREDIENT && !config.PAYMENT_ACTIVE && (
          <div
            className='border-2 border-primary active:border-secondary rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold bg-primary active:bg-secondary text-background'
            onClick={() => setSingleIngredientOpen(true)}
            role='button'
          >
            <p className='text-center py-1 flex items-center justify-center'>{t('cocktails.singleIngredient')}</p>
            <div className='relative w-full' style={{ paddingTop: '100%' }}>
              <img
                src={`${API_URL}/static/default/default.jpg`}
                alt='Single Ingredient'
                className='absolute top-0 left-0 w-full h-full object-cover'
              />
            </div>
          </div>
        )}
      </div>

      <Modal
        isOpen={!!selectedCocktail}
        onRequestClose={handleCloseModal}
        contentLabel='Cocktail Details'
        className='modal'
        overlayClassName='overlay z-20'
        preventScroll={true}
      >
        {selectedCocktail && (
          <CocktailSelection
            selectedCocktail={selectedCocktail}
            handleCloseModal={handleCloseModal}
            cocktails={displayedCocktails?.sort((a, b) => a.name.localeCompare(b.name)) || []}
            setSelectedCocktail={setSelectedCocktail}
          />
        )}
      </Modal>
      <Modal isOpen={singleIngredientOpen} className='modal slim' overlayClassName='overlay z-20' preventScroll={true}>
        <SingleIngredientSelection onClose={() => setSingleIngredientOpen(false)} />
      </Modal>
    </div>
  );
};

export default CocktailList;
