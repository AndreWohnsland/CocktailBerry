import React from 'react';
import { useAddonData, addAddon, deleteAddon } from '../../api/options';
import { AddonData } from '../../types/models';
import { FaPlus, FaTrashAlt } from 'react-icons/fa';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import { confirmAndExecute, executeAndShow } from '../../utils';
import { useTranslation } from 'react-i18next';

const AddonManager: React.FC = () => {
  const { data: addons, isLoading, error, refetch } = useAddonData();
  const { t } = useTranslation();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const sortedAddons = addons?.sort((a, b) => {
    const getPriority = (addon: AddonData) => {
      if (addon.is_installable && addon.official && addon.installed) return 1;
      if (addon.is_installable && !addon.installed) return 2;
      return 3;
    };
    const priorityDifference = getPriority(a) - getPriority(b);
    if (priorityDifference !== 0) {
      return priorityDifference;
    }
    return a.name.localeCompare(b.name);
  });

  const handleInstall = async (addon: AddonData) => {
    executeAndShow(() => addAddon(addon)).then((success) => {
      if (success) {
        refetch();
      }
    });
  };

  const handleDelete = async (addon: AddonData) => {
    confirmAndExecute(t('addons.deleteTheAddon', { addon: addon.name }), () => deleteAddon(addon)).then((success) => {
      if (success) {
        refetch();
      }
    });
  };

  return (
    <div className='p-4 w-full max-w-3xl'>
      <h2 className='text-2xl text-center mb-4 text-secondary font-bold'>{t('addons.manageAddons')}</h2>
      <div className='grid grid-cols-1 gap-2'>
        {sortedAddons?.map((addon) => (
          <div key={addon.name} className='border border-primary p-4 rounded-xl'>
            <div className='flex justify-between items-center mb-4'>
              <h3 className='text-lg text-secondary font-semibold'>{addon.name}</h3>
              {addon.is_installable && addon.official && !addon.installed ? (
                <button
                  onClick={() => handleInstall(addon)}
                  className='button-primary-filled flex items-center p-2 px-4'
                >
                  <FaPlus className='mr-2' />
                  {t('add')}
                </button>
              ) : !addon.is_installable && !addon.installed ? (
                <div className='button-neutral !border !font-normal p-2 px-4'>{t('addons.cannotBeInstalled')}</div>
              ) : (
                <button onClick={() => handleDelete(addon)} className='button-danger-filled flex items-center p-2 px-4'>
                  <FaTrashAlt className='mr-2' /> {t('delete')}
                </button>
              )}
            </div>
            <p>{addon.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AddonManager;
