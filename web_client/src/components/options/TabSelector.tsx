import React from 'react';
import { OPTIONTABS } from '../../utils';

interface TabSelectorProps {
  selectedTab: string;
  onSelectTab: (tab: string) => void;
}

const createClass = (isActive: boolean) => {
  const baseClass = 'px-2 flex items-center border-2 font-semibold';
  const activeClass = 'text-background bg-secondary border-secondary rounded-full';
  return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
};

const TabSelector: React.FC<TabSelectorProps> = ({ selectedTab, onSelectTab }) => {
  return (
    <div className='flex flex-row sticky top-9 py-2 bg-background z-9 w-full items-center justify-center overflow-auto'>
      {OPTIONTABS.map((tab) => (
        <button key={tab} onClick={() => onSelectTab(tab)} className={createClass(selectedTab === tab)}>
          {tab}
        </button>
      ))}
    </div>
  );
};

export default TabSelector;
