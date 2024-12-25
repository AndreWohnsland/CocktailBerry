import React, { useEffect, useState } from 'react';
import { FaWineBottle } from 'react-icons/fa';
import { IoClose } from 'react-icons/io5';
import Modal from 'react-modal';
import { useNavigate } from 'react-router-dom';

interface RefillPromptProps {
  isOpen: boolean;
  message: string;
  onClose: () => void;
}

const RefillPrompt: React.FC<RefillPromptProps> = ({ isOpen, message, onClose }) => {
  const [isChecked, setIsChecked] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setIsChecked(false);
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} className='modal slim' overlayClassName='overlay z-30'>
      <div className='flex flex-col items-center justify-center w-full h-full'>
        <div className='flex justify-between w-full mb-2'>
          <button
            className='button-primary-filled p-2 px-4 flex flex-row items-center'
            onClick={() => navigate('/manage/bottles')}
          >
            <FaWineBottle className='mr-3' size={25} />
            Go to Bottles
          </button>
          <button className='button-danger p-2 px-4 flex flex-row items-center' onClick={onClose}>
            Later
            <IoClose className='ml-3' size={25} />
          </button>
        </div>
        <div className='flex-grow'></div>
        <div className='text-center mb-6'>
          <p>{message}</p>
        </div>
        <div className='flex items-center gap-2 mb-2'>
          <input
            type='checkbox'
            id='doneCheck'
            checked={isChecked}
            onChange={(e) => setIsChecked(e.target.checked)}
            className='cursor-pointer'
          />
          <label htmlFor='doneCheck' className='cursor-pointer text-neutral'>
            Bottle is refilled
          </label>
        </div>
        <div className='flex-grow'></div>
        <button
          className={`${isChecked ? 'button-primary-filled' : 'button-neutral'} px-4 py-2 w-full`}
          onClick={() => {
            if (isChecked) {
              alert('Apply clicked!');
            }
          }}
          disabled={!isChecked}
        >
          Apply Refill
        </button>
      </div>
    </Modal>
  );
};

export default RefillPrompt;
