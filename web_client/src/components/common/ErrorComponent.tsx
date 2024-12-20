import React from 'react';
import { FaExclamationTriangle } from 'react-icons/fa';

const ErrorComponent: React.FC<{ text?: string }> = ({ text }) => (
  <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
    <FaExclamationTriangle className='text-danger' size={100} />
    <span className='mt-8 text-2xl text-secondary text-center'>Error</span>
    <span className='mt-4 text-lg text-center'>{text || 'Could not load data'}</span>
    <span className='mt-4 text-md text-neutral text-center'>
      If this persists, please check that CocktailBerry is running and you are in the same network!
    </span>
  </div>
);

export default ErrorComponent;
