import { useEffect, useState } from 'react';
import { FaArrowUp } from 'react-icons/fa';

export const JumpToTopButton: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateVisibility = () => {
      const root = document.documentElement;
      const canScroll = root.scrollHeight > root.clientHeight;
      const isAtTop = window.scrollY <= 0;
      setIsVisible(canScroll && !isAtTop);
    };

    updateVisibility();
    window.addEventListener('scroll', updateVisibility, { passive: true });
    window.addEventListener('resize', updateVisibility);

    return () => {
      window.removeEventListener('scroll', updateVisibility);
      window.removeEventListener('resize', updateVisibility);
    };
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className='sticky-bottom'>
      <button
        type='button'
        onClick={scrollToTop}
        className='button-primary max-w-20 flex items-center justify-center p-3 m-1 ml-auto pointer-events-auto'
      >
        <FaArrowUp size={30} />
      </button>
    </div>
  );
};
