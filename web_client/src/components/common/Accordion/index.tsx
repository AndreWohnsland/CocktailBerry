import { useState } from 'react';
import { FaChevronRight } from 'react-icons/fa';

interface AccordionProps {
  title: React.ReactNode;
  children: React.ReactNode;
}

const Accordion: React.FC<AccordionProps> = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={'[&:not(:last-child)]:border-b border-primary'}>
      <button
        type='button'
        className={`flex justify-between items-center p-2 cursor-pointer w-full text-left ${
          isOpen ? 'text-secondary' : 'text-primary'
        }`}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span>{title}</span>
        <FaChevronRight
          className={`transition-[rotate] duration-150 ease-[cubic-bezier(0.2,0,0,1)] ${isOpen ? 'rotate-90' : ''}`}
        />
      </button>
      {isOpen && <div className='p-2 pt-0 pb-4'>{children}</div>}
    </div>
  );
};

export default Accordion;
