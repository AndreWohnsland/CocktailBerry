import React from 'react';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { useRestrictedMode } from '../providers/RestrictedModeProvider';

const Header: React.FC = () => {
  const { t } = useTranslation();
  const { restrictedModeActive } = useRestrictedMode();
  const getNavLinkClass = (isActive: boolean) => {
    const baseClass = 'nav-link px-2 flex items-center border-2 font-semibold';
    const activeClass = 'text-background bg-secondary border-secondary rounded-full';
    return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
  };

  if (restrictedModeActive) {
    return null;
  }

  return (
    <header className='fixed top-0 left-0 right-0 bg-background shadow-sm shadow-neutral z-10'>
      <div className='flex justify-center items-center py-1 px-4'>
        <nav className='flex space-x-1 overflow-x-auto'>
          <NavLink to='/cocktails' className={({ isActive }) => getNavLinkClass(isActive)}>
            {t('header.cocktails')}
          </NavLink>
          <NavLink to='/manage/ingredients' className={({ isActive }) => getNavLinkClass(isActive)}>
            {t('header.ingredients')}
          </NavLink>
          <NavLink to='/manage/recipes' className={({ isActive }) => getNavLinkClass(isActive)}>
            {t('header.recipes')}
          </NavLink>
          <NavLink to='/manage/bottles' className={({ isActive }) => getNavLinkClass(isActive)}>
            {t('header.bottles')}
          </NavLink>
          <NavLink to='/options' className={({ isActive }) => getNavLinkClass(isActive)}>
            {t('header.options')}
          </NavLink>
        </nav>
      </div>
    </header>
  );
};

export default Header;
