import React from 'react';
import { useTranslation } from 'react-i18next';
import { PaymentUserData } from '../../../types/models';

interface UserDisplayProps {
  user: PaymentUserData | null;
}
const UserDisplay: React.FC<UserDisplayProps> = ({ user }) => {
  const { t } = useTranslation();

  const elementStyle = 'p-2 bg-background border border-primary rounded-md text-center text-primary font-bold h-10';
  const noUserElement = <div className={elementStyle}>{t('userDisplay.noUser')}</div>;
  const userElement = <div className={elementStyle}>{t('userDisplay.userBalance', { balance: user?.balance })}</div>;

  return (
    <div className='sticky-top mb-2 float-left mr-2'>
      <div className='flex-shrink inline-block'>{user ? userElement : noUserElement}</div>
    </div>
  );
};

export default UserDisplay;
