import React from 'react';
import { FaCog } from 'react-icons/fa';

const GettingConfiguration: React.FC = () => (
  <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
    <FaCog className='animate-spin text-neutral' size={100} />
    <span className='mt-8 text-2xl text-secondary text-center'>Getting Configuration</span>
    <span className='mt-4 text-lg text-center'>Fetching data from backend for setup, this should be quick ...</span>
    <span className='mt-4 text-md text-neutral text-center'>
      If this persists, please check that CocktailBerry is running and you are in the same network!
    </span>
  </div>
);

export default GettingConfiguration;
