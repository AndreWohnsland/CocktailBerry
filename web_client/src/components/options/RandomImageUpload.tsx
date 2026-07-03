import type React from 'react';
import { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { FaTrashAlt, FaUpload } from 'react-icons/fa';
import { deleteRandomImage, uploadRandomImage } from '../../api/options';
import { confirmAndExecute, errorToast, executeAndShow } from '../../utils';

const RandomImageUpload: React.FC = () => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      errorToast('Please select a file before uploading.');
      return;
    }
    await executeAndShow(() => uploadRandomImage(file));
  };

  const handleDelete = async () => {
    await confirmAndExecute(t('recipes.deleteExistingImage'), deleteRandomImage);
  };

  return (
    <div className='flex items-center pt-1'>
      <button type='button' onClick={handleUpload} className='p-2 mr-1 button-secondary'>
        <FaUpload />
      </button>
      <input type='file' accept='image/*' ref={fileInputRef} className='input-base p-1 mr-1' />
      <button type='button' onClick={handleDelete} className='button-danger p-2'>
        <FaTrashAlt />
      </button>
    </div>
  );
};

export default RandomImageUpload;
