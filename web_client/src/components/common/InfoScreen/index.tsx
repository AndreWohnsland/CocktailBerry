import React from 'react';

export interface InfoScreenProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  hint?: string;
  button?: React.ReactNode;
}

const InfoScreen: React.FC<InfoScreenProps> = ({ icon, title, description, hint, button }) => {
  return (
    <div className='h-full w-full max-w-md flex items-center justify-center flex-col'>
      {icon}
      <span className='mt-8 text-2xl text-secondary text-center'>{title}</span>
      {description && <span className='mt-4 text-lg text-center'>{description}</span>}
      {hint && <span className='mt-4 text-md text-neutral text-center'>{hint}</span>}
      {button && <div className='mt-4'>{button}</div>}
    </div>
  );
};

export default InfoScreen;
