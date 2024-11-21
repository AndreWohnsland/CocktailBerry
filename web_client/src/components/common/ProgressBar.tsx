import React from 'react';

interface ProgressBarProps {
  fillPercent: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ fillPercent }) => {
  return (
    <div
      className='border-2 border-neutral bg-neutral text-background font-bold rounded-full text-center overflow-hidden flex items-center justify-center'
      style={{ position: 'relative', zIndex: 1 }}
    >
      <div
        className='bg-primary rounded-full'
        style={{ width: `${fillPercent}%`, height: '100%', position: 'absolute', left: 0, top: 0 }}
      ></div>
      <span style={{ position: 'relative', zIndex: 2 }}>{fillPercent}%</span>
    </div>
  );
};

export default ProgressBar;
