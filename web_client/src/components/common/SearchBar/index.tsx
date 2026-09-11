import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaEraser, FaSearch } from 'react-icons/fa';

interface SearchBarProps {
  search: string | null;
  setSearch: (value: string | null) => void;
  tabBarVisible: boolean;
  afterInput?: React.ReactNode;
  initiallyOpen?: boolean;
}
// note: the internal search should never be null, but we communicate to external component with null
// if the search is hidden. This is to know externally if the search is shown or not, and should be applied.
const SearchBar: React.FC<SearchBarProps> = ({
  search,
  setSearch,
  tabBarVisible,
  afterInput,
  initiallyOpen = false,
}) => {
  const [savedSearch, setSavedSearch] = React.useState<string>(search ?? '');
  const [showSearch, setShowSearch] = React.useState(initiallyOpen);
  const { t } = useTranslation();

  const handleHideToggle = () => {
    // it is currently shown, so need to save the search value and hide it
    if (showSearch) {
      setSavedSearch(search ?? '');
      setSearch(null);
    } else {
      setSearch(savedSearch);
    }
    setShowSearch(!showSearch);
  };

  return (
    <div className={`z-10 sticky mb-2 flex flex-row pointer-events-none ${tabBarVisible ? 'top-10' : 'top-1'}`}>
      <div className='grow' />
      {/* Stays mounted so the reveal can animate: the wrapper slides out from the
          toggle button (clipped on the left via justify-end) while fading in. */}
      <div
        className={`flex justify-end w-full overflow-hidden transition-[max-width,opacity,visibility] duration-200 ease-[cubic-bezier(0.2,0,0,1)] ${
          showSearch ? 'max-w-120 opacity-100 visible' : 'max-w-0 opacity-0 invisible'
        }`}
      >
        <input
          type='text'
          name='searchInput'
          placeholder={t('search')}
          value={search ?? ''}
          onChange={(e) => setSearch(e.target.value)}
          className='h-10 input-base mr-1 w-full p-3 max-w-sm pointer-events-auto'
        />
        <button
          type='button'
          onClick={() => setSearch('')}
          className='h-10 w-10 button-neutral flex items-center justify-center p-2 mr-1 border! pointer-events-auto'
        >
          <FaEraser size={20} />
        </button>
        {afterInput && <div className='mr-1 pointer-events-auto'>{afterInput}</div>}
      </div>
      <button
        type='button'
        onClick={handleHideToggle}
        className='h-10 w-10 button-primary flex items-center justify-center p-2 border! pointer-events-auto'
      >
        <FaSearch size={20} />
      </button>
    </div>
  );
};

export default SearchBar;
