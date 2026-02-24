import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaPlus, FaTrashAlt } from 'react-icons/fa';
import { createSumupReader, deleteSumupReader, setActiveSumupReader, useSumupReaders } from '../../api/options';
import { useConfig } from '../../providers/ConfigProvider';
import type { SumupReader } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import Button from '../common/Button';
import ErrorComponent from '../common/ErrorComponent';
import ItemCard from '../common/ItemCard';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';
import TextInput from '../common/TextInput';
import TileButton from '../common/TileButton';

const SumupManager: React.FC = () => {
  const { data: readers, isLoading, error, refetch } = useSumupReaders();
  const { config, refetchConfig } = useConfig();
  const [name, setName] = useState<string>('');
  const [pairingCode, setPairingCode] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const { t } = useTranslation();

  const activeReaderId = config.PAYMENT_SUMUP_TERMINAL_ID;

  const handleCreate = async () => {
    if (!name.trim() || !pairingCode.trim()) return;

    setIsCreating(true);
    const success = await executeAndShow(async () => {
      const reader = await createSumupReader({ name: name.trim(), pairing_code: pairingCode.trim() });
      return { message: t('sumup.readerCreated', { name: reader.name }) };
    });
    setIsCreating(false);

    if (success) {
      setName('');
      setPairingCode('');
      refetch();
    }
  };

  const handleDelete = async (reader: SumupReader) => {
    const success = await confirmAndExecute(t('sumup.deleteReader', { name: reader.name }), () =>
      deleteSumupReader(reader.id),
    );
    if (success) {
      refetch();
    }
  };

  const handleUse = async (reader: SumupReader) => {
    const success = await executeAndShow(() => setActiveSumupReader(reader.id));
    if (success) {
      refetch();
      refetchConfig();
    }
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const isFormValid = name.trim() !== '' && pairingCode.trim() !== '';

  return (
    <div className='p-4 w-full max-w-3xl'>
      <TextHeader text={t('sumup.manageSumup')} />

      <form onSubmit={handleCreate} className='border border-primary p-4 rounded-xl mb-4'>
        <h3 className='text-lg text-secondary font-semibold mb-4'>{t('sumup.createReader')}</h3>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-4'>
          <TextInput value={name} large handleInputChange={setName} placeholder={t('sumup.readerNamePlaceholder')} />
          <TextInput
            value={pairingCode}
            large
            handleInputChange={setPairingCode}
            placeholder={t('sumup.pairingCodePlaceholder')}
          />
        </div>
        <TileButton
          label={isCreating ? t('sumup.creating') : t('sumup.create')}
          icon={FaPlus}
          textSize='md'
          filled
          disabled={!isFormValid || isCreating}
          onClick={handleCreate}
        />
      </form>

      <div className='grid grid-cols-1 gap-2'>
        {readers?.length === 0 && <p className='text-neutral text-center'>{t('sumup.noReaders')}</p>}
        {readers?.map((reader) => {
          const isActive = reader.id === activeReaderId;
          return (
            <ItemCard
              key={reader.id}
              title={reader.name}
              subtitle={isActive ? t('sumup.activeReader') : undefined}
              highlighted={isActive}
              actions={
                <>
                  {!isActive && (
                    <Button
                      filled
                      icon={FaCheck}
                      label={t('sumup.use')}
                      className='px-4'
                      onClick={() => handleUse(reader)}
                    />
                  )}
                  <Button
                    style='danger'
                    filled
                    icon={FaTrashAlt}
                    label={t('delete')}
                    className='px-4'
                    onClick={() => handleDelete(reader)}
                  />
                </>
              }
            />
          );
        })}
      </div>
    </div>
  );
};

export default SumupManager;
