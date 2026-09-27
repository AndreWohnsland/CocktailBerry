import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQueryClient } from 'react-query';
import { updateAccessPoint, useAccessPoint } from '../../api/options';
import { confirmAndExecute } from '../../utils';
import Button from '../common/Button';
import CheckBox from '../common/CheckBox';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';
import TextInput from '../common/TextInput';

const AP_ADDRESS = 'http://10.42.0.1';
const SSID_LENGTH = [1, 32];
const PASSWORD_LENGTH = [8, 63];

const AccessPointManager = () => {
  const { data: status, isLoading, error } = useAccessPoint();
  const queryClient = useQueryClient();
  const [enabled, setEnabled] = useState(false);
  const [ssid, setSsid] = useState('');
  const [password, setPassword] = useState('');
  const { t } = useTranslation();

  useEffect(() => {
    if (!status) return;
    setEnabled(status.enabled);
    setSsid(status.ssid);
    setPassword(status.password);
  }, [status]);

  const dataValid =
    ssid.length >= SSID_LENGTH[0] &&
    ssid.length <= SSID_LENGTH[1] &&
    password.length >= PASSWORD_LENGTH[0] &&
    password.length <= PASSWORD_LENGTH[1];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await confirmAndExecute(t('accessPoint.confirm'), () =>
      updateAccessPoint({ enabled, ssid, password }),
    );
    if (success) queryClient.invalidateQueries('accessPoint');
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  return (
    <div className='p-4 w-full max-w-3xl'>
      <TextHeader text={t('accessPoint.title')} />
      <form onSubmit={handleSubmit} className='flex flex-col gap-4 text-neutral'>
        <CheckBox value={enabled} checkName={t('accessPoint.enabled')} handleInputChange={setEnabled} />
        <TextInput prefix={`${t('accessPoint.ssid')}:`} value={ssid} handleInputChange={setSsid} />
        <TextInput prefix={`${t('accessPoint.password')}:`} value={password} handleInputChange={setPassword} />
        <Button type='submit' label={t('accessPoint.apply')} disabled={!dataValid} className='w-full' />
      </form>
      {status?.qr_code && (
        <div className='flex flex-col items-center gap-2 mt-6 text-neutral text-center'>
          <img src={`data:image/png;base64,${status.qr_code}`} alt='WiFi QR code' className='w-64 h-64' />
          <p>{t('accessPoint.qrHint')}</p>
          <p>
            {t('accessPoint.address')} {AP_ADDRESS}
          </p>
        </div>
      )}
    </div>
  );
};

export default AccessPointManager;
