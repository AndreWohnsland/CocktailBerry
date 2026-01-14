import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { errorToast } from '../../../utils';
import Button from '../Button';
import TextHeader from '../TextHeader';
import TextInput from '../TextInput';

export interface PasswordPageProps {
  passwordName: string;
  setAuthenticated: (password: number) => void;
  authMethod: (password: number) => Promise<{ message: string }>;
}

const PasswordPage: React.FC<PasswordPageProps> = ({ passwordName, setAuthenticated, authMethod }) => {
  const [password, setPassword] = useState('');
  const { t } = useTranslation();

  const handlePasswordSubmit = () => {
    const usedPassword = Number(password);
    authMethod(usedPassword)
      .then(() => {
        setAuthenticated(usedPassword);
      })
      .catch((err) => {
        errorToast(err);
      });
  };

  return (
    <div className='flex flex-col justify-between items-center p-4 w-full max-w-md'>
      <TextHeader text={t('password.passwordNeeded', { passwordName })} />
      <p className='w-full text-center'>{t('password.passwordProtectedBy', { passwordName })}</p>
      <p className='mt-2 w-full text-center'>{t('password.enterThePassword')}</p>
      <form className='w-full mt-4'>
        <TextInput
          type='password'
          value={password}
          handleInputChange={setPassword}
          placeholder={t('password.enterPassword')}
        />
        <Button label={t('submit')} filled onClick={handlePasswordSubmit} className='w-full mt-6' />
      </form>
    </div>
  );
};

export default PasswordPage;
