import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaEdit, FaPlus, FaTrashAlt } from 'react-icons/fa';
import {
  createWaiter,
  deleteWaiter,
  updateWaiter,
  useWaiterLogs,
  useWaiters,
  useWaiterWebSocket,
} from '../../api/waiters';
import { useConfig } from '../../providers/ConfigProvider';
import type { Waiter, WaiterPermissions } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import Button from '../common/Button';
import CheckBox from '../common/CheckBox';
import ErrorComponent from '../common/ErrorComponent';
import ItemCard from '../common/ItemCard';
import LoadingData from '../common/LoadingData';
import TabSelector from '../common/TabSelector';
import TextHeader from '../common/TextHeader';
import TextInput from '../common/TextInput';
import TileButton from '../common/TileButton';
import WaiterStatistics from '../common/WaiterStatistics';

const TABS = ['Management', 'Statistics'] as const;
type WaiterTab = (typeof TABS)[number];

const WaiterWindow: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<WaiterTab>('Management');
  const { t } = useTranslation();

  return (
    <div className='p-4 w-full max-w-3xl h-full'>
      <TextHeader text={t('waiter.title')} />
      <TabSelector tabs={[...TABS]} selectedTab={selectedTab} onSelectTab={(tab) => setSelectedTab(tab as WaiterTab)} />
      <div className='my-4' />
      {selectedTab === 'Management' && <ManagementTab />}
      {selectedTab === 'Statistics' && <StatisticsTab />}
    </div>
  );
};

const DEFAULT_PERMISSIONS: WaiterPermissions = {
  maker: true,
  ingredients: false,
  recipes: false,
  bottles: false,
};
const PERMISSION_KEYS = ['maker', 'ingredients', 'recipes', 'bottles'] as const;

const ManagementTab: React.FC = () => {
  const { config } = useConfig();
  const { data: waiters, isLoading, error, refetch } = useWaiters();
  const { waiter: currentWaiter } = useWaiterWebSocket(config.WAITER_MODE);
  const [nfcId, setNfcId] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [createPermissions, setCreatePermissions] = useState<WaiterPermissions>({ ...DEFAULT_PERMISSIONS });
  const [editingWaiter, setEditingWaiter] = useState<string | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editPermissions, setEditPermissions] = useState<WaiterPermissions>({ ...DEFAULT_PERMISSIONS });
  const { t } = useTranslation();

  const handleCreate = async () => {
    if (!nfcId.trim() || !name.trim()) return;
    setIsCreating(true);
    const success = await executeAndShow(async () => {
      const waiter = await createWaiter({ nfc_id: nfcId.trim(), name: name.trim(), permissions: createPermissions });
      return { message: t('waiter.created', { name: waiter.name }) };
    });
    setIsCreating(false);
    if (success) {
      setNfcId('');
      setName('');
      setCreatePermissions({ ...DEFAULT_PERMISSIONS });
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
    setEditPermissions({ ...waiter.permissions });
  };

  const handleSaveEdit = async (nfcIdToEdit: string) => {
    if (!editName.trim()) return;
    const success = await executeAndShow(async () => {
      await updateWaiter(nfcIdToEdit, { name: editName.trim(), permissions: editPermissions });
      return { message: t('waiter.updated') };
    });
    if (success) {
      setEditingWaiter(null);
      setEditName('');
      refetch();
    }
  };

  const handleCancelEdit = () => {
    setEditingWaiter(null);
    setEditName('');
  };

  // Pre-fill NFC ID from current scan if available
  const handleUseScannedNfc = () => {
    if (currentWaiter?.nfc_id) {
      setNfcId(currentWaiter.nfc_id);
    }
  };

  if (isLoading)
    return (
      <div className='flex justify-center w-full'>
        <LoadingData />
      </div>
    );
  if (error) return <ErrorComponent text={error.message} />;

  const isFormValid = nfcId.trim() !== '' && name.trim() !== '';

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
        <p className='text-sm text-neutral mb-2'>{t('waiter.permissionsLabel')}</p>
        <div className='flex flex-wrap gap-4 mb-4'>
          {PERMISSION_KEYS.map((key) => (
            <CheckBox
              key={key}
              value={createPermissions[key]}
              checkName={t(`waiter.permissions.${key}`)}
              handleInputChange={(val) => setCreatePermissions((prev) => ({ ...prev, [key]: val }))}
            />
          ))}
        </div>
        <TileButton
          label={isCreating ? t('waiter.creating') : t('create')}
          icon={FaPlus}
          textSize='md'
          filled
          disabled={!isFormValid || isCreating}
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
                <p className='text-sm text-neutral mb-2'>{t('waiter.permissionsLabel')}</p>
                <div className='flex flex-wrap gap-4'>
                  {PERMISSION_KEYS.map((key) => (
                    <CheckBox
                      key={key}
                      value={editPermissions[key]}
                      checkName={t(`waiter.permissions.${key}`)}
                      handleInputChange={(val) => setEditPermissions((prev) => ({ ...prev, [key]: val }))}
                    />
                  ))}
                </div>
              </div>
            );
          }

          const activePermissions = PERMISSION_KEYS.filter((key) => waiter.permissions[key]);

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
              {activePermissions.length > 0 && (
                <div className='flex flex-wrap gap-2 mt-2'>
                  {activePermissions.map((key) => (
                    <span
                      key={key}
                      className='text-sm px-2 py-0.5 rounded-full border-2 border-secondary text-secondary'
                    >
                      {t(`waiter.permissions.${key}`)}
                    </span>
                  ))}
                </div>
              )}
            </ItemCard>
          );
        })}
      </div>
    </>
  );
};

const StatisticsTab: React.FC = () => {
  const { data: logs, isLoading, error } = useWaiterLogs();

  if (isLoading)
    return (
      <div className='flex justify-center w-full'>
        <LoadingData />
      </div>
    );
  if (error) return <ErrorComponent text={error.message} />;

  return <WaiterStatistics logs={logs ?? []} />;
};

export default WaiterWindow;
