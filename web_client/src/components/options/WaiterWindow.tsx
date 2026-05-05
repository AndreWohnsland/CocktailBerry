import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import TabSelector from '../common/TabSelector';
import TextHeader from '../common/TextHeader';
import ManagementTab from './waiter/ManagementTab';
import RolesTab from './waiter/RolesTab';
import StatisticsTab from './waiter/StatisticsTab';

const TAB_KEYS = ['management', 'statistics', 'roles'] as const;
type TabKey = (typeof TAB_KEYS)[number];

const WaiterWindow: React.FC = () => {
  const { t } = useTranslation();
  const [selectedKey, setSelectedKey] = useState<TabKey>('management');
  const labels = TAB_KEYS.map((k) => t(`waiter.tabs.${k}`));
  const selectedLabel = t(`waiter.tabs.${selectedKey}`);
  const handleSelect = (label: string) => {
    const idx = labels.indexOf(label);
    if (idx >= 0) setSelectedKey(TAB_KEYS[idx]);
  };

  return (
    <div className='p-4 w-full max-w-3xl h-full'>
      <TextHeader text={t('waiter.title')} />
      <TabSelector tabs={labels} selectedTab={selectedLabel} onSelectTab={handleSelect} />
      <div className='my-4' />
      {selectedKey === 'management' && <ManagementTab />}
      {selectedKey === 'statistics' && <StatisticsTab />}
      {selectedKey === 'roles' && <RolesTab />}
    </div>
  );
};

export default WaiterWindow;
