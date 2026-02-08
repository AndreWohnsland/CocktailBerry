import type React from 'react';

interface TabSelectorProps {
  tabs: string[];
  selectedTab: string;
  onSelectTab: (tab: string) => void;
  className?: string;
}

const createClass = (isActive: boolean) => {
  const baseClass = 'px-1 flex items-center border-2 font-semibold';
  const activeClass = 'text-background bg-secondary border-secondary rounded-full';
  return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
};

const TabSelector: React.FC<TabSelectorProps> = ({ tabs, selectedTab, onSelectTab, className }) => {
  return (
    <div className={`flex flex-row py-2 w-full items-center justify-center overflow-auto ${className ?? ''}`}>
      {tabs.map((tab) => (
        <button type='button' key={tab} onClick={() => onSelectTab(tab)} className={createClass(selectedTab === tab)}>
          {tab}
        </button>
      ))}
    </div>
  );
};

export default TabSelector;
