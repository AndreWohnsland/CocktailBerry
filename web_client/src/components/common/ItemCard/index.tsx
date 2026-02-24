import type { ReactNode } from 'react';

interface ItemCardProps {
  title: string;
  subtitle?: string;
  description?: string;
  highlighted?: boolean;
  actions?: ReactNode;
  children?: ReactNode;
}

const ItemCard = ({ title, subtitle, description, highlighted = false, actions, children }: ItemCardProps) => {
  return (
    <div className={`border p-4 rounded-xl ${highlighted ? 'border-secondary' : 'border-primary'}`}>
      <div className='flex justify-between items-center'>
        <div className='flex flex-col'>
          <h3 className='text-lg text-secondary font-semibold'>{title}</h3>
          {subtitle && <span className='text-sm text-neutral'>{subtitle}</span>}
        </div>
        {actions && <div className='flex gap-2'>{actions}</div>}
      </div>
      {description && <p className='mt-4'>{description}</p>}
      {children}
    </div>
  );
};

export default ItemCard;
