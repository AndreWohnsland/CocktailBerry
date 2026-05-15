import { useEffect, useState } from 'react';
import Modal from 'react-modal';
import { type ConfirmRequest, registerConfirmListener, unregisterConfirmListener } from '../../confirmDialog';

const ConfirmDialog = () => {
  const [pending, setPending] = useState<ConfirmRequest | null>(null);

  useEffect(() => {
    registerConfirmListener((request) => {
      setPending(request);
    });
    return () => unregisterConfirmListener();
  }, []);

  const handleResponse = (value: boolean) => {
    pending?.resolve(value);
    setPending(null);
  };

  return (
    <Modal
      isOpen={pending !== null}
      shouldCloseOnOverlayClick={false}
      shouldCloseOnEsc={false}
      className='modal slim'
      overlayClassName='overlay z-30'
    >
      <div className='flex flex-col bg-background p-6 rounded-lg h-full'>
        <div className='grow' />
        <p className='text-primary text-center text-lg leading-relaxed'>{pending?.message}</p>
        <div className='grow' />
        <div className='flex justify-between px-2'>
          <button
            type='button'
            className='button-primary-filled min-w-36 px-2 py-2'
            onClick={() => handleResponse(true)}
          >
            {pending?.yesLabel}
          </button>
          <button type='button' className='button-neutral min-w-36 px-2 py-2' onClick={() => handleResponse(false)}>
            {pending?.noLabel}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
