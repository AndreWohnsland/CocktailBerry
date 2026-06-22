import type React from 'react';
import { useTranslation } from 'react-i18next';
import { MdLiquor, MdLocalBar, MdMenuBook, MdSettings, MdWaterDrop } from 'react-icons/md';
import { NavLink } from 'react-router';
import { useRestrictedMode } from '../providers/RestrictedModeProvider';
import ModeToggle from './common/ModeToggle';

const NAV_LINKS = [
  { to: '/cocktails', icon: MdLocalBar, label: 'header.cocktails' },
  { to: '/manage/ingredients', icon: MdWaterDrop, label: 'header.ingredients' },
  { to: '/manage/recipes', icon: MdMenuBook, label: 'header.recipes' },
  { to: '/manage/bottles', icon: MdLiquor, label: 'header.bottles' },
  { to: '/options', icon: MdSettings, label: 'header.options' },
] as const;

const Header: React.FC = () => {
  const { t } = useTranslation();
  const { restrictedModeActive } = useRestrictedMode();
  const getNavLinkClass = (isActive: boolean) => {
    // Icon sits inline with the label; in portrait the label hides and the
    // icon-only link gets a bit more horizontal padding.
    const baseClass = 'nav-link flex items-center gap-1.5 px-2 portrait:px-4 border-2 font-semibold';
    const activeClass = 'text-on-secondary bg-secondary border-secondary rounded-full';
    return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
  };

  if (restrictedModeActive) {
    return null;
  }

  return (
    <header className='fixed top-0 left-0 w-screen bg-[color-mix(in_srgb,var(--neutral-color)_15%,var(--background-color))] z-10'>
      <div className='flex items-center gap-2 py-1 px-4'>
        <nav className='flex-1 overflow-x-auto'>
          {/* w-max + mx-auto centers when it fits, but collapses to the left
              (both ends scrollable) when it overflows — unlike justify-center. */}
          <div className='flex space-x-1 w-max mx-auto'>
            {NAV_LINKS.map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} className={({ isActive }) => getNavLinkClass(isActive)}>
                <Icon size={18} aria-hidden='true' />
                <span className='portrait:hidden'>{t(label)}</span>
              </NavLink>
            ))}
          </div>
        </nav>
        <ModeToggle />
      </div>
    </header>
  );
};

export default Header;
