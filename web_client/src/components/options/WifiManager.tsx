import type React from 'react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import { getWifiStatus, updateWifiData, useAvailableSsids, useWifiStatus } from '../../api/options';
import { POLL_REQUEST_TIMEOUT_MS, usePolling } from '../../hooks/usePolling';
import type { WifiStatus } from '../../types/models';
import { askYesNo, errorToast } from '../../utils';
import Button from '../common/Button';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';
import TextInput from '../common/TextInput';
import WaitModal from '../common/WaitModal';

// the backend gives the join a minute, then restores the access point and rolls back
const JOIN_PATIENCE_MS = 2 * 60 * 1000;

const WifiManager: React.FC = () => {
  const { data: ssids, isLoading, error } = useAvailableSsids();
  const { data: status, refetch: refetchStatus } = useWifiStatus();
  const [selectedSsid, setSelectedSsid] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [isInputMode, setIsInputMode] = useState<boolean>(false);
  const [joining, setJoining] = useState(false);
  const { t } = useTranslation();
  // the 202 can get lost in the access point blink, so attach to a join the backend already runs
  useEffect(() => {
    if (status?.job.state === 'running') setJoining(true);
  }, [status?.job.state]);

  // Polled instead of awaited: the tablet usually sits on the access point, which blinks while
  // the radio switches channel, so a request spanning the join would break mid-flight.
  const takesLong = usePolling(joining, JOIN_PATIENCE_MS, () => async () => {
    let current: WifiStatus;
    try {
      current = await getWifiStatus({ timeout: POLL_REQUEST_TIMEOUT_MS });
    } catch {
      return false;
    }
    const { job } = current;
    if (job.state === 'running') return false;
    if (job.state === 'succeeded') toast(t('wifi.connected', { ssid: job.ssid, ip: current.ip ?? '?' }));
    if (job.state === 'failed') toast(t('wifi.failed', { ssid: job.ssid, reason: job.reason }));
    setJoining(false);
    void refetchStatus();
    return true;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!(await askYesNo(t('wifi.connectToWifi', { selectedSsid })))) return;
    try {
      await updateWifiData({ ssid: selectedSsid, password });
      setJoining(true);
    } catch (err) {
      errorToast(err);
    }
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

  // outside the loading/error branches, so an SSID refetch error during the join does not hide it
  const wait = (
    <WaitModal
      open={joining}
      title={t('wifi.waitTitle', { ssid: selectedSsid })}
      description={t('wifi.waitDescription')}
      takesLong={takesLong}
      takesLongText={t('wifi.takingLonger')}
    />
  );

  let content: React.ReactNode;
  if (isLoading) content = <LoadingData />;
  else if (error) content = <ErrorComponent text={error.message} />;
  else
    content = (
      <div className='p-4 w-full max-w-3xl'>
        <TextHeader text={t('wifi.setupWifi')} />
        {status && (
          <div className='text-center text-neutral mb-4'>
            <p>
              {status.ssid ? t('wifi.status', { ssid: status.ssid, ip: status.ip ?? '?' }) : t('wifi.notConnected')}
            </p>
            <p className='text-sm opacity-70'>
              {status.hotspot_active ? t('wifi.hotspotActive') : t('wifi.hotspotInactive')}
            </p>
          </div>
        )}
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
          <TextInput
            label={t('wifi.password')}
            type='password'
            value={password}
            large
            handleInputChange={setPassword}
          />
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

  return (
    <>
      {wait}
      {content}
    </>
  );
};

export default WifiManager;
