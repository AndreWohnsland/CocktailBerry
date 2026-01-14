import type React from 'react';
import { useRestrictedMode } from '../../providers/RestrictedModeProvider';
import { OPTIONTABS } from '../../utils';

interface TabSelectorProps {
  selectedTab: string;
  onSelectTab: (tab: string) => void;
}

const createClass = (isActive: boolean) => {
  const baseClass = 'px-1 flex items-center border-2 font-semibold';
  const activeClass = 'text-background bg-secondary border-secondary rounded-full';
  return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
};

const TabSelector: React.FC<TabSelectorProps> = ({ selectedTab, onSelectTab }) => {
  const { restrictedModeActive } = useRestrictedMode();

  return (
    <div
      className={`flex flex-row fixed py-2 bg-background z-9 w-full items-center justify-center overflow-auto ${
        restrictedModeActive ? 'top-0' : 'top-9'
      }`}
    >
      {OPTIONTABS.map((tab) => (
        <button type='button' key={tab} onClick={() => onSelectTab(tab)} className={createClass(selectedTab === tab)}>
          {tab}
        </button>
      ))}
    </div>
  );
};

export default TabSelector;
