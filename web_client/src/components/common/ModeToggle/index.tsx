import type React from 'react';
import { useTranslation } from 'react-i18next';
import { MdDarkMode, MdLightMode } from 'react-icons/md';
import { useConfig } from '../../../providers/ConfigProvider';

/** Per-browser light/dark Mode toggle. Hidden for the custom Theme (ADR 0003). */
const ModeToggle: React.FC = () => {
  const { t } = useTranslation();
  const { mode, toggleMode, theme } = useConfig();

  if (theme === 'custom') {
    return null;
  }

  return (
    <button
      type='button'
      onClick={toggleMode}
      aria-label={t('header.toggleMode')}
      className='shrink-0 flex items-center text-primary pr-2'
    >
      {mode === 'dark' ? <MdDarkMode size={22} /> : <MdLightMode size={22} />}
    </button>
  );
};

export default ModeToggle;
