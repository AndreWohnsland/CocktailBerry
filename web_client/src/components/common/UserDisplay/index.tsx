import React from 'react';
import { useTranslation } from 'react-i18next';
import { MdChildCare, MdPerson } from 'react-icons/md';
import { PaymentUserData } from '../../../types/models';

interface UserDisplayProps {
  user: PaymentUserData | null;
}
const UserDisplay: React.FC<UserDisplayProps> = ({ user }) => {
  const { t } = useTranslation();

  const elementStyle =
    'px-2 bg-background border border-primary rounded-md text-center text-primary font-bold h-10 align-middle flex items-center justify-center';
  const noUserElement = <div className={elementStyle}>{t('userDisplay.noUser')}</div>;

  const Icon = user?.is_adult ? MdPerson : MdChildCare;
  const userElement = (
    <div className={elementStyle}>
      <Icon className='inline mr-2' size={26} />
      <span className='text-lg'>{t('userDisplay.userBalance', { balance: user?.balance })}</span>
    </div>
  );

  return (
    <div className='sticky-top mb-2 float-left mr-2'>
      <div className='flex-shrink inline-block'>{user ? userElement : noUserElement}</div>
    </div>
  );
};

export default UserDisplay;
