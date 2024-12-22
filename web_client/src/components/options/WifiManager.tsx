import React, { useState } from 'react';
import { useAvailableSsids, updateWifiData } from '../../api/options';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import { confirmAndExecute } from '../../utils';

const WifiManager: React.FC = () => {
  const { data: ssids, isLoading, error } = useAvailableSsids();
  const [selectedSsid, setSelectedSsid] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    confirmAndExecute(`Use data to connect to WiFi ${selectedSsid}`, () =>
      updateWifiData({ ssid: selectedSsid, password }),
    );
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  return (
    <div className='p-4 w-full max-w-3xl'>
      <h2 className='text-2xl text-center mb-4 text-secondary font-bold'>Set Up WiFi</h2>
      <form onSubmit={handleSubmit} className='grid grid-cols-1 md:grid-cols-2 gap-2'>
        <label className='text-neutral text-center'>
          SSID:
          <select
            value={selectedSsid}
            onChange={(e) => setSelectedSsid(e.target.value)}
            required
            className='select-base w-full !p-2'
          >
            <option value='' disabled>
              Select SSID
            </option>
            {ssids?.map((ssid) => (
              <option key={ssid} value={ssid}>
                {ssid}
              </option>
            ))}
          </select>
        </label>
        <label className='text-neutral text-center'>
          Password:
          <input
            type='password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className='input-base !p-2'
          />
        </label>
        <button type='submit' className='col-span-1 md:col-span-2 button-primary-filled p-2 mt-4'>
          Submit
        </button>
      </form>
    </div>
  );
};

export default WifiManager;
