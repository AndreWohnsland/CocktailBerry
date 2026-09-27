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
      <form onSubmit={handleSubmit} className='grid grid-cols-1 md:grid-cols-2 gap-2 text-neutral'>
        <div className='col-span-1 md:col-span-2 mb-2 flex justify-center'>
          <CheckBox value={enabled} checkName={t('accessPoint.enabled')} handleInputChange={setEnabled} />
        </div>
        <TextInput label={t('accessPoint.ssid')} value={ssid} large handleInputChange={setSsid} />
        <div>
          <TextInput label={t('accessPoint.password')} value={password} large handleInputChange={setPassword} />
          <p className='text-sm text-center opacity-70'>
            {t('accessPoint.passwordHint', { min: PASSWORD_LENGTH[0], max: PASSWORD_LENGTH[1] })}
          </p>
        </div>
        <Button
          type='submit'
          filled
          label={t('accessPoint.apply')}
          disabled={!dataValid}
          className='col-span-1 md:col-span-2 mt-4'
        />
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
