import React from 'react';

interface ProgressBarProps {
  fillPercent: number;
  className?: string;
  onClick?: () => void;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ fillPercent, className, onClick }) => {
  return (
    <div
      className={
        'border-2 border-neutral bg-neutral text-background font-bold rounded-full text-center overflow-hidden flex items-center justify-center' +
        (className ? ` ${className}` : '')
      }
      style={{ position: 'relative', zIndex: 1 }}
      onClick={onClick}
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
