import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { confirmAndExecute } from '../../utils';
import { updateDateTime } from '../../api/options';

const TimeManager: React.FC = () => {
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dataValid()) return;
    console.log('Setting time to:', date, time);
    confirmAndExecute(t('timeManager.adjustTimeConfirmation'), () => updateDateTime(date, time));
  };

  const dataValid = () => {
    return date !== '' && time !== '';
  };

  return (
    <div className='p-4 w-full max-w-xl'>
      <h2 className='text-2xl text-center mb-4 text-secondary font-bold'>{t('timeManager.adjustTime')}</h2>
      <form onSubmit={handleSubmit} className='grid grid-cols-1 md:grid-cols-2 gap-2'>
        <label className='text-neutral text-center'>
          {t('date')}:
          <input
            type='date'
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
            className='input-base !p-2'
          />
        </label>
        <label className='text-neutral text-center'>
          {t('time')}:
          <input
            type='time'
            value={time}
            onChange={(e) => setTime(e.target.value)}
            required
            className='input-base !p-2'
          />
        </label>
        <button
          type='submit'
          className={`col-span-1 md:col-span-2 p-2 mt-4 button-primary-filled ${!dataValid() && 'disabled'}`}
          disabled={!dataValid()}
        >
          {t('submit')}
        </button>
      </form>
    </div>
  );
};

export default TimeManager;
