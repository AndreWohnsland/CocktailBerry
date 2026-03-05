import { Activity, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaUserTie } from 'react-icons/fa6';
import { IoClose } from 'react-icons/io5';
import { MdLogout } from 'react-icons/md';
import { logoutWaiter } from '../../../api/waiters';
import type { CurrentWaiterState } from '../../../types/models';
import Button from '../Button';

interface WaiterDisplayProps {
  waiter: CurrentWaiterState | null;
  initialOpen?: boolean;
}

const WaiterDisplay: React.FC<WaiterDisplayProps> = ({ waiter, initialOpen = false }) => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(initialOpen);
  const hasWaiter = waiter?.nfc_id != null;

  const badgeStyle =
    'px-2 border rounded-md text-center font-bold h-10 align-middle flex items-center justify-center bg-background border-primary text-primary';

  if (!hasWaiter) {
    return (
      <div className='sticky-top mb-2 float-left mr-2 relative z-20'>
        <div className='flex-shrink inline-block'>
          <div className={badgeStyle}>{t('waiter.noWaiter')}</div>
        </div>
      </div>
    );
  }

  const displayName = waiter?.waiter?.name ?? (waiter?.nfc_id ? t('waiter.unknown', { nfcId: waiter.nfc_id }) : null);

  const toggle = () => setIsOpen((prev) => !prev);

  const handleLogout = async () => {
    await logoutWaiter();
    setIsOpen(false);
  };

  return (
    <div className='sticky-top mb-2 float-left mr-2 relative z-20'>
      <div className='flex-shrink inline-flex items-center gap-1'>
        <Activity mode={isOpen ? 'hidden' : 'visible'}>
          <Button
            style='primary'
            icon={FaUserTie}
            label={displayName ?? ''}
            onClick={toggle}
            className='h-10'
            textSize='md'
          />
        </Activity>
        <Activity mode={isOpen ? 'visible' : 'hidden'}>
          <Button style='neutral' icon={IoClose} iconSize={26} label='' onClick={toggle} className='h-10' />
          <Button
            style='danger'
            filled
            icon={MdLogout}
            label={t('waiter.logout')}
            onClick={handleLogout}
            className='h-10'
            textSize='md'
          />
        </Activity>
      </div>
    </div>
  );
};

export default WaiterDisplay;
