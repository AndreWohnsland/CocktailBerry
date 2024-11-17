import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTheme } from '../ThemeProvider.tsx';

const Header: React.FC = () => {
  const { onThemeChange } = useTheme();
  const themes = ['default', 'berry', 'bavaria', 'alien', 'custom'];

  return (
    <header className='sticky top-0 bg-background shadow-sm shadow-neutral z-50 overflow-x-auto'>
      <div className='flex justify-between items-center p-4'>
        <nav className='flex space-x-4'>
          <NavLink
            to='/cocktails'
            className={({ isActive }) => (isActive ? 'nav-link text-secondary border-secondary' : 'nav-link')}
          >
            Cocktails
          </NavLink>
          <NavLink
            to='/ingredients'
            className={({ isActive }) => (isActive ? 'nav-link text-secondary border-secondary' : 'nav-link')}
          >
            Ingredients
          </NavLink>
          <NavLink
            to='/recipes'
            className={({ isActive }) => (isActive ? 'nav-link text-secondary border-secondary' : 'nav-link')}
          >
            Recipes
          </NavLink>
          <NavLink
            to='/bottles'
            className={({ isActive }) => (isActive ? 'nav-link text-secondary border-secondary' : 'nav-link')}
          >
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
