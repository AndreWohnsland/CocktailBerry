import React, { useState } from 'react';
import { errorToast } from '../../utils';

interface PasswordPageProps {
  requiredPassword: number;
  passwordName: string;
  setAuthenticated: () => void;
}

const PasswordPage: React.FC<PasswordPageProps> = ({ requiredPassword, passwordName, setAuthenticated }) => {
  const [password, setPassword] = useState('');

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (Number(password) === requiredPassword) {
      setAuthenticated();
    } else {
      errorToast('Incorrect password');
    }
  };

  return (
    <div className='flex flex-col justify-between items-center p-4 w-full max-w-md'>
      <h1 className='text-secondary text-2xl font-bold mb-8'>Password needed</h1>
      <p>This section is protected by the {passwordName}</p>
      <p className='mt-2'>Enter the password to continue:</p>
      <form className='w-full mt-4' onSubmit={handlePasswordSubmit}>
        <input
          className='input-base'
          type='password'
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder='Enter password'
        />
        <button className='button-primary-filled p-2 w-full mt-8' type='submit'>
          Submit
        </button>
      </form>
    </div>
  );
};

export default PasswordPage;
