import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MdNoDrinks } from 'react-icons/md';
import Modal from 'react-modal';
import { getAuthenticatedUser, useCocktails } from '../../api/cocktails';
import { API_URL } from '../../api/common';
import { useConfig } from '../../providers/ConfigProvider';
import { Cocktail } from '../../types/models';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import CocktailSelection from './CocktailSelection';
import SingleIngredientSelection from './SingleIngredientSelection';

const CocktailList: React.FC = () => {
  const { config } = useConfig();
  const { data: cocktails, error, isLoading } = useCocktails(true, config.MAKER_MAX_HAND_INGREDIENTS ?? 0);
  const [selectedCocktail, setSelectedCocktail] = useState<Cocktail | null>(null);
  const [singleIngredientOpen, setSingleIngredientOpen] = useState(false);
  const [search, setSearch] = useState<string | null>(null);
  const [showOnlyVirginPossible, setShowOnlyVirginPossible] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(
    !config.PAYMENT_ACTIVE || !config.PAYMENT_LOCK_SCREEN_NO_USER,
  );
  const { t } = useTranslation();

  // Poll for user authentication when payment locking is active
  useEffect(() => {
    if (!config.PAYMENT_ACTIVE || !config.PAYMENT_LOCK_SCREEN_NO_USER) {
      return;
    }

    let intervalId: ReturnType<typeof setInterval> | null = null;

    const checkAuthentication = async () => {
      const userAuth = await getAuthenticatedUser();
      setIsAuthenticated(userAuth.is_authenticated);
    };

    // Initial check
    checkAuthentication();

    // Poll every 500ms when not authenticated
    intervalId = setInterval(checkAuthentication, 500);

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [config.PAYMENT_ACTIVE, config.PAYMENT_LOCK_SCREEN_NO_USER]);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  // Show NFC scan prompt when payment locking is active and user is not authenticated
  if (config.PAYMENT_ACTIVE && config.PAYMENT_LOCK_SCREEN_NO_USER && !isAuthenticated) {
    return (
      <div className='centered max-w-7xl'>
        <div className='flex flex-col items-center justify-center min-h-[60vh] gap-8 text-center'>
          <h1 className='text-4xl font-bold text-primary'>{t('payment.scanToUnlock')}</h1>
          <p className='text-xl text-neutral'>{t('payment.scanNFCToAccess')}</p>
        </div>
      </div>
    );
  }

  const handleCloseModal = () => {
    setSelectedCocktail(null);
  };

  let displayedCocktails = cocktails;
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
      className={`flex items-center justify-center p-2 !border pointer-events-auto ${
        showOnlyVirginPossible ? 'button-secondary' : 'button-primary'
      }`}
    >
      <MdNoDrinks size={20} />
    </button>
  );

  return (
    <div className='px-2 centered max-w-7xl'>
      <SearchBar search={search} setSearch={setSearch} afterInput={virginToggleButton} />
      <div className='flex flex-wrap gap-3 justify-center items-center w-full mb-4'>
        {displayedCocktails
          ?.sort((a, b) => a.name.localeCompare(b.name))
          .map((cocktail) => (
            <div
              key={cocktail.id}
              className='border-2 border-primary active:border-secondary rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold bg-primary active:bg-secondary text-background'
              onClick={() => setSelectedCocktail(cocktail)}
              role='button'
            >
              <p className='text-center py-1 flex items-center justify-center'>
                {cocktail.virgin_available && (
                  <MdNoDrinks className={`mr-2 ${cocktail.only_virgin && 'border-2 border-background rounded-full'}`} />
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
          ))}
        {config.MAKER_ADD_SINGLE_INGREDIENT && (
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
