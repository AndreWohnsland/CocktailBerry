import React from 'react';
import { FaSpinner } from 'react-icons/fa';

const LoadingData: React.FC = () => (
  <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
    <FaSpinner className='animate-spin text-neutral' size={100} />
    <span className='mt-8 text-2xl text-secondary text-center'>Loading data...</span>
    <span className='mt-4 text-lg text-center'>Fetching data from backend, this should be quick ...</span>
  </div>
);

export default LoadingData;
