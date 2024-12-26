import React, { useState } from 'react';
import { errorToast } from '../../utils';
import { useTranslation } from 'react-i18next';

interface PasswordPageProps {
  passwordName: string;
  setAuthenticated: (password: number) => void;
  authMethod: (password: number) => Promise<{ message: string }>;
}

const PasswordPage: React.FC<PasswordPageProps> = ({ passwordName, setAuthenticated, authMethod }) => {
  const [password, setPassword] = useState('');
  const { t } = useTranslation();

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
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
      <h1 className='text-secondary text-2xl font-bold mb-8'>{t('password.passwordNeeded', { passwordName })}</h1>
      <p className='w-full text-center'>{t('password.passwordProtectedBy', { passwordName })}</p>
      <p className='mt-2 w-full text-center'>{t('password.enterThePassword')}</p>
      <form className='w-full mt-4' onSubmit={handlePasswordSubmit}>
        <input
          className='input-base'
          type='password'
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={t('password.enterPassword')}
        />
        <button className='button-primary-filled p-2 w-full mt-8' type='submit'>
          {t('submit')}
        </button>
      </form>
    </div>
  );
};

export default PasswordPage;
