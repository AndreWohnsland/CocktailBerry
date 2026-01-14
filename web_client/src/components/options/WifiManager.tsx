import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { updateWifiData, useAvailableSsids } from '../../api/options';
import { confirmAndExecute } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';

const WifiManager: React.FC = () => {
  const { data: ssids, isLoading, error } = useAvailableSsids();
  const [selectedSsid, setSelectedSsid] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [isInputMode, setIsInputMode] = useState<boolean>(false);
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    confirmAndExecute(t('wifi.connectToWifi', { selectedSsid }), () =>
      updateWifiData({ ssid: selectedSsid, password }),
    );
  };

  const dataValid = () => {
    return selectedSsid !== '' && password !== '';
  };

  const toggleInputMode = () => {
    setIsInputMode(!isInputMode);
    if (isInputMode && ssids && ssids.length > 0) {
      setSelectedSsid(ssids[0]);
    }
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  return (
    <div className='p-4 w-full max-w-3xl'>
      <TextHeader text={t('wifi.setupWifi')} />
      <form onSubmit={handleSubmit} className='grid grid-cols-1 md:grid-cols-2 gap-2'>
        <button type='button' onClick={toggleInputMode} className='col-span-1 md:col-span-2 button-secondary p-2 my-4'>
          {isInputMode ? t('wifi.switchToSelect') : t('wifi.switchToInput')}
        </button>
        <label className='text-neutral text-center' htmlFor='wifi-input'>
          {'SSID:'}
          {isInputMode ? (
            <input
              type='text'
              id='wifi-input'
              value={selectedSsid}
              onChange={(e) => setSelectedSsid(e.target.value)}
              required
              className='input-base w-full !p-2'
            />
          ) : (
            <select
              id='wifi-input'
              value={selectedSsid}
              onChange={(e) => setSelectedSsid(e.target.value)}
              required
              className='select-base w-full !p-2'
            >
              <option value='' disabled>
                {t('wifi.selectSsid')}
              </option>
              {ssids?.map((ssid) => (
                <option key={ssid} value={ssid}>
                  {ssid}
                </option>
              ))}
            </select>
          )}
        </label>
        <label className='text-neutral text-center' htmlFor='wifi-password'>
          {t('wifi.password')}:
          <input
            type='password'
            id='wifi-password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className='input-base !p-2'
          />
        </label>
        <button
          type='submit'
          disabled={!dataValid()}
          className={`col-span-1 md:col-span-2 button-primary-filled p-2 mt-4 ${!dataValid() && 'disabled'}`}
        >
          {t('submit')}
        </button>
      </form>
    </div>
  );
};

export default WifiManager;
