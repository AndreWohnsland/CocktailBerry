import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../ThemeProvider.tsx';

const Header: React.FC = () => {
  const { onThemeChange } = useTheme();
  const themes = ['default', 'berry', 'bavaria', 'alien', 'custom'];

  const getNavLinkClass = (isActive: boolean) => {
    const baseClass = 'nav-link px-2 flex items-center';
    const activeClass = 'text-secondary border-secondary border-2 rounded-full font-bold';
    return isActive ? `${baseClass} ${activeClass}` : baseClass;
  };

  return (
    <header className='fixed top-0 left-0 right-0 bg-background shadow-sm shadow-neutral z-10'>
      <div className='flex justify-between items-center py-1 px-4'>
        <nav className='flex space-x-1'>
          <NavLink to='/cocktails' className={({ isActive }) => getNavLinkClass(isActive)}>
            Cocktails
          </NavLink>
          <NavLink to='/ingredients' className={({ isActive }) => getNavLinkClass(isActive)}>
            Ingredients
          </NavLink>
          <NavLink to='/recipes' className={({ isActive }) => getNavLinkClass(isActive)}>
            Recipes
          </NavLink>
          <NavLink to='/bottles' className={({ isActive }) => getNavLinkClass(isActive)}>
            Bottles
          </NavLink>
        </nav>
        <div className='dropdown-container'>
          <label htmlFor='theme-dropdown'>Theme: </label>
          <select className='theme-dropdown' onChange={(e) => onThemeChange(e.target.value)}>
            {themes.map((theme) => (
              <option key={theme} value={theme}>
                {theme.charAt(0).toUpperCase() + theme.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
};

export default Header;
