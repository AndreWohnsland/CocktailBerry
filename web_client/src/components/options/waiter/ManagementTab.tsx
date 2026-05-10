import type React from 'react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaEdit, FaPlus, FaTrashAlt } from 'react-icons/fa';
import { useRoles } from '../../../api/roles';
import { createWaiter, deleteWaiter, updateWaiter, useWaiters, useWaiterWebSocket } from '../../../api/waiters';
import { useConfig } from '../../../providers/ConfigProvider';
import type { Waiter } from '../../../types/models';
import { confirmAndExecute, executeAndShow } from '../../../utils';
import Button from '../../common/Button';
import DropDown from '../../common/DropDown';
import ErrorComponent from '../../common/ErrorComponent';
import ItemCard from '../../common/ItemCard';
import LoadingData from '../../common/LoadingData';
import TextInput from '../../common/TextInput';
import TileButton from '../../common/TileButton';

const ManagementTab: React.FC = () => {
  const { config } = useConfig();
  const { data: waiters, isLoading, error, refetch } = useWaiters();
  const { data: roles, isLoading: rolesLoading } = useRoles();
  const { waiter: currentWaiter } = useWaiterWebSocket(config.WAITER_MODE);
  const [nfcId, setNfcId] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [createRoleId, setCreateRoleId] = useState<string>('');
  const [editingWaiter, setEditingWaiter] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editRoleId, setEditRoleId] = useState<string>('');
  const { t } = useTranslation();

  const roleOptions = useMemo(() => {
    if (!roles) return {};
    return Object.fromEntries(roles.map((r) => [String(r.id), r.name]));
  }, [roles]);

  const handleCreate = async () => {
    if (!nfcId.trim() || !name.trim() || !createRoleId) return;
    setIsCreating(true);
    const success = await executeAndShow(async () => {
      const waiter = await createWaiter({
        nfc_id: nfcId.trim(),
        name: name.trim(),
        role_id: Number(createRoleId),
      });
      return { message: t('waiter.created', { name: waiter.name }) };
    });
    setIsCreating(false);
    if (success) {
      setNfcId('');
      setName('');
      setCreateRoleId('');
      refetch();
    }
  };

  const handleDelete = async (waiter: Waiter) => {
    const success = await confirmAndExecute(t('waiter.confirmDelete', { name: waiter.name }), () =>
      deleteWaiter(waiter.nfc_id),
    );
    if (success) {
      refetch();
    }
  };

  const handleEdit = (waiter: Waiter) => {
    setEditingWaiter(waiter.nfc_id);
    setEditName(waiter.name);
    setEditRoleId(String(waiter.role_id));
  };

  const handleSaveEdit = async (nfcIdToEdit: string) => {
    if (!editName.trim() || !editRoleId) return;
    const success = await executeAndShow(async () => {
      await updateWaiter(nfcIdToEdit, {
        name: editName.trim(),
        role_id: Number(editRoleId),
      });
      return { message: t('waiter.updated') };
    });
    if (success) {
      setEditingWaiter(null);
      setEditName('');
      setEditRoleId('');
      refetch();
    }
  };

  const handleCancelEdit = () => {
    setEditingWaiter(null);
    setEditName('');
    setEditRoleId('');
  };

  const handleUseScannedNfc = () => {
    if (currentWaiter?.nfc_id) {
      setNfcId(currentWaiter.nfc_id);
    }
  };

  if (isLoading || rolesLoading)
    return (
      <div className='flex justify-center w-full'>
        <LoadingData />
      </div>
    );
  if (error) return <ErrorComponent text={error.message} />;

  const noRoles = !roles || roles.length === 0;
  const isFormValid = nfcId.trim() !== '' && name.trim() !== '' && createRoleId !== '';

  return (
    <>
      {currentWaiter?.nfc_id && (
        <div className='mb-4'>
          <ItemCard
            title={t('waiter.lastScanned')}
            subtitle={currentWaiter.waiter?.name ?? undefined}
            description={currentWaiter.nfc_id}
            actions={<Button label={t('waiter.useScanned')} onClick={handleUseScannedNfc} />}
          />
        </div>
      )}

      {noRoles && (
        <div className='mb-4 p-3 border border-danger rounded-xl text-danger'>{t('role.createFirstHint')}</div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleCreate();
        }}
        className='border border-primary p-4 rounded-xl mb-4'
      >
        <h3 className='text-lg text-secondary font-semibold mb-4'>{t('waiter.registerWaiter')}</h3>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-4'>
          <div className='flex gap-2'>
            <TextInput value={nfcId} large handleInputChange={setNfcId} placeholder={t('waiter.nfcIdPlaceholder')} />
          </div>
          <TextInput value={name} large handleInputChange={setName} placeholder={t('waiter.namePlaceholder')} />
        </div>
        <p className='text-sm text-neutral mb-2'>{t('waiter.roleLabel')}</p>
        <DropDown
          value={createRoleId}
          allowedValues={roleOptions}
          handleInputChange={setCreateRoleId}
          placeholder={t('waiter.selectRole')}
          className='mb-4'
        />
        <TileButton
          label={isCreating ? t('waiter.creating') : t('create')}
          icon={FaPlus}
          textSize='md'
          filled
          disabled={!isFormValid || isCreating || noRoles}
          onClick={handleCreate}
        />
      </form>

      <div className='grid grid-cols-1 gap-2'>
        {waiters?.length === 0 && <p className='text-neutral text-center'>{t('waiter.noWaiters')}</p>}
        {waiters?.map((waiter) => {
          const isActive = currentWaiter?.nfc_id === waiter.nfc_id;
          const isEditing = editingWaiter === waiter.nfc_id;

          if (isEditing) {
            return (
              <div key={waiter.nfc_id} className='border border-secondary rounded-xl p-4'>
                <div className='flex gap-2 items-center mb-3'>
                  <TextInput
                    value={editName}
                    large
                    handleInputChange={setEditName}
                    placeholder={t('waiter.namePlaceholder')}
                  />
                  <Button filled label={t('save')} className='px-4' onClick={() => handleSaveEdit(waiter.nfc_id)} />
                  <Button label={t('cancel')} className='px-4' onClick={handleCancelEdit} />
                </div>
                <p className='text-sm text-neutral mb-2'>{t('waiter.roleLabel')}</p>
                <DropDown
                  value={editRoleId}
                  allowedValues={roleOptions}
                  handleInputChange={setEditRoleId}
                  placeholder={t('waiter.selectRole')}
                />
              </div>
            );
          }

          return (
            <ItemCard
              key={waiter.nfc_id}
              title={waiter.name}
              subtitle={isActive ? t('waiter.active') : undefined}
              description={waiter.nfc_id}
              highlighted={isActive}
              actions={
                <>
                  <Button icon={FaEdit} label={t('edit')} className='px-4' onClick={() => handleEdit(waiter)} />
                  <Button
                    style='danger'
                    filled
                    icon={FaTrashAlt}
                    label={t('delete')}
                    className='px-4'
                    onClick={() => handleDelete(waiter)}
                  />
                </>
              }
            >
              <div className='flex flex-wrap gap-2 mt-2'>
                <span className='text-sm px-2 py-0.5 rounded-full border-2 border-secondary text-secondary'>
                  {waiter.role.name}
                </span>
              </div>
            </ItemCard>
          );
        })}
      </div>
    </>
  );
};

export default ManagementTab;
