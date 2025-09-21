import { AiOutlineCloseCircle } from 'react-icons/ai';

interface CloseButtonProps {
  iconSize?: number;
  onClick?: () => void;
}

const CloseButton = ({ iconSize = 35, onClick }: CloseButtonProps) => {
  return (
    <button type='button' className='text-danger ml-2' onClick={onClick}>
      <AiOutlineCloseCircle size={iconSize} />
    </button>
  );
};

export default CloseButton;
