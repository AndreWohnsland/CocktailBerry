import { FaArrowUp } from 'react-icons/fa';

export const JumpToTopButton: React.FC = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  return (
    <div className='sticky-bottom'>
      <button
        onClick={scrollToTop}
        className='button-primary max-w-20 flex items-center justify-center p-3 m-1 ml-auto pointer-events-auto'
      >
        <FaArrowUp size={30} />
      </button>
    </div>
  );
};
