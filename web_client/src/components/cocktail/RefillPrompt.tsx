import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaWineBottle } from 'react-icons/fa';
import { IoClose } from 'react-icons/io5';
import Modal from 'react-modal';
import { useNavigate } from 'react-router-dom';
import { executeAndShow } from '../../utils';
import { refillBottle } from '../../api/bottles';

interface RefillPromptProps {
  isOpen: boolean;
  message: string;
  bottleNumber: number;
  onClose: () => void;
}

const RefillPrompt: React.FC<RefillPromptProps> = ({ isOpen, message, bottleNumber, onClose }) => {
  const [isChecked, setIsChecked] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    setIsChecked(false);
  }, [isOpen]);

  const applyRefillBottle = () => {
    if (!isChecked) return;
    executeAndShow(() => refillBottle([bottleNumber])).then((success) => {
      if (success) onClose();
    });
  };

  return (
    <Modal isOpen={isOpen} className='modal slim' overlayClassName='overlay z-30'>
      <div className='flex flex-col items-center justify-center w-full h-full'>
        <div className='flex justify-between w-full mb-2'>
          <button
            className='button-primary-filled p-2 px-4 flex flex-row items-center'
            onClick={() => navigate('/manage/bottles')}
          >
            <FaWineBottle className='mr-3' size={25} />
            {t('cocktails.goToBottles')}
          </button>
          <button className='button-danger p-2 px-4 flex flex-row items-center' onClick={onClose}>
            {t('cocktails.later')}
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
            {t('cocktails.bottleRefilledCheck')}
          </label>
        </div>
        <div className='flex-grow'></div>
        <button
          className={`${!isChecked && 'disabled'} button-primary-filled px-4 py-2 w-full`}
          onClick={applyRefillBottle}
          disabled={!isChecked}
        >
          {t('cocktails.applyRefill')}
        </button>
      </div>
    </Modal>
  );
};

export default RefillPrompt;
