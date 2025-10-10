import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaEraser, FaSearch } from 'react-icons/fa';

interface SearchBarProps {
  search: string | null;
  setSearch: (value: string | null) => void;
  afterInput?: React.ReactNode;
  initiallyOpen?: boolean;
}
// note: the internal search should never be null, but we communicate to external component with null
// if the search is hidden. This is to know externally if the search is shown or not, and should be applied.
const SearchBar: React.FC<SearchBarProps> = ({ search, setSearch, afterInput, initiallyOpen = false }) => {
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
    <div className='sticky-top mb-2 flex flex-row'>
      <div className='flex-grow'></div>
      <input
        type='text'
        placeholder={t('search')}
        value={search ?? ''}
        onChange={(e) => setSearch(e.target.value)}
        className='input-base mr-1 w-full p-3 max-w-sm'
        hidden={!showSearch}
      />
      <div className={`flex ${showSearch ? '' : 'hidden'}`}>
        <button
          onClick={() => setSearch('')}
          className='button-neutral flex items-center justify-center p-2 mr-1 !border'
        >
          <FaEraser size={20} />
        </button>
      </div>
      {afterInput && <div className={`mr-1 ${showSearch ? '' : 'hidden'}`}>{afterInput}</div>}
      <button
        onClick={handleHideToggle}
        className='button-primary flex items-center justify-center p-2 !border pointer-events-auto'
      >
        <FaSearch size={20} />
      </button>
    </div>
  );
};

export default SearchBar;
