import React, { useState } from 'react';
import { Bottle } from '../../types/models';

interface BottleProps {
  bottle: Bottle;
}

const BottleComponent: React.FC<BottleProps> = ({ bottle }) => {
  const [isNew, setIsNew] = useState(false);

  const getClass = () => {
    const color = isNew ? 'secondary' : 'primary';
    return `max-w-20 border-2 rounded-md border-${color} text-${color}`;
  };

  const fillPercent = Math.round(
    ((bottle.ingredient?.fill_level || 0) / (bottle.ingredient?.bottle_volume || 1)) * 100,
  );

  return (
    <>
      <button onClick={() => setIsNew(!isNew)} className={getClass()}>
        New
      </button>
      <span className='text-right text-secondary pr-1'>{bottle.ingredient?.name || 'No Name'}:</span>
      <div
        className='border-2 border-neutral bg-neutral text-background font-bold rounded-full text-center overflow-hidden flex items-center justify-center'
        style={{ position: 'relative' }}
      >
        <div
          className='bg-primary rounded-full'
          style={{ width: `${fillPercent}%`, height: '100%', position: 'absolute', left: 0, top: 0 }}
        ></div>
        <span style={{ position: 'relative', zIndex: 1 }}>{fillPercent}%</span>
      </div>
      <select>{bottle.ingredient?.name}</select>
      <div className='place-content-center text-center text-secondary font-bold max-w-12'>{bottle.number}</div>
    </>
  );
};

export default BottleComponent;
