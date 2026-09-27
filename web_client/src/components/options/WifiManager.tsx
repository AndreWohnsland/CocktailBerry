import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { updateWifiData, useAvailableSsids } from '../../api/options';
import { confirmAndExecute } from '../../utils';
import Button from '../common/Button';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';
import TextInput from '../common/TextInput';

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
        <Button
          style='secondary'
          label={isInputMode ? t('wifi.switchToSelect') : t('wifi.switchToInput')}
          className='col-span-1 md:col-span-2 my-4'
          onClick={toggleInputMode}
        />
        {isInputMode ? (
          <TextInput label='SSID' value={selectedSsid} large handleInputChange={setSelectedSsid} />
        ) : (
          <DropDown
            label='SSID'
            value={selectedSsid}
            allowedValues={ssids ?? []}
            placeholder={t('wifi.selectSsid')}
            className='p-2!'
            handleInputChange={setSelectedSsid}
          />
        )}
        <TextInput label={t('wifi.password')} type='password' value={password} large handleInputChange={setPassword} />
        <Button
          type='submit'
          filled
          label={t('submit')}
          disabled={!dataValid()}
          className='col-span-1 md:col-span-2 mt-4'
        />
      </form>
    </div>
  );
};

export default WifiManager;
