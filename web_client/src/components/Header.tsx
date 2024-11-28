import React from 'react';
import { NavLink } from 'react-router-dom';

const Header: React.FC = () => {
  const getNavLinkClass = (isActive: boolean) => {
    const baseClass = 'nav-link px-2 flex items-center border-2 font-semibold';
    const activeClass = 'text-background bg-secondary border-secondary rounded-full';
    return isActive ? `${baseClass} ${activeClass}` : `${baseClass} border-transparent`;
  };

  return (
    <header className='fixed top-0 left-0 right-0 bg-background shadow-sm shadow-neutral z-10'>
      <div className='flex justify-center items-center py-1 px-4'>
        <nav className='flex space-x-1 overflow-x-auto'>
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
          <NavLink to='/options' className={({ isActive }) => getNavLinkClass(isActive)}>
            Options
          </NavLink>
        </nav>
      </div>
    </header>
  );
};

export default Header;
