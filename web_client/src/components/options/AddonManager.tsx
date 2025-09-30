import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus, FaTrashAlt } from 'react-icons/fa';
import { addAddon, deleteAddon, updateAddon, useAddonData } from '../../api/options';
import { AddonData } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';

const AddonManager: React.FC = () => {
  const { data: addons, isLoading, error, refetch } = useAddonData();
  const { t } = useTranslation();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const sortedAddons = addons?.sort((a, b) => {
    const getPriority = (addon: AddonData) => {
      if (!addon.official) return 10;
      if (addon.is_installable && addon.installed) return 1;
      if (addon.installed) return 2;
      if (addon.is_installable && !addon.installed) return 3;
      return 4;
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

  const handleUpdate = async (addon: AddonData) => {
    confirmAndExecute(t('addons.updateTheAddon', { addon: addon.name }), () => updateAddon(addon)).then((success) => {
      if (success) {
        refetch();
      }
    });
  };

  const createAddonButton = (addon: AddonData) => {
    if (addon.is_installable && addon.official && !addon.installed) {
      return (
        <button onClick={() => handleInstall(addon)} className='button-primary-filled flex items-center p-2 px-4'>
          <FaPlus className='mr-2' />
          {t('add')} ({addon.version})
        </button>
      );
    } else if (!addon.satisfy_min_version && !addon.installed) {
      return (
        <div className='button-neutral !border !font-normal p-2 px-4'>
          {t('addons.minVersionNotMet', { version: addon.minimal_version })}
        </div>
      );
    } else if (!addon.is_installable && !addon.installed) {
      return <div className='button-neutral !border !font-normal p-2 px-4'>{t('addons.cannotBeInstalled')}</div>;
    } else if (!addon.official) {
      return <div className='button-neutral !border !font-normal p-2 px-4'>{t('addons.notOfficial')}</div>;
    } else {
      return (
        <button onClick={() => handleDelete(addon)} className='button-danger-filled flex items-center p-2 px-4'>
          <FaTrashAlt className='mr-2' /> {t('delete')}
        </button>
      );
    }
  };
  return (
    <div className='p-4 w-full max-w-3xl'>
      <TextHeader text={t('addons.manageAddons')} />
      <div className='grid grid-cols-1 gap-2'>
        {sortedAddons?.map((addon) => (
          <div key={addon.name} className='border border-primary p-4 rounded-xl'>
            <div className='flex justify-between items-center mb-4'>
              <div className='flex flex-col'>
                <h3 className='text-lg text-secondary font-semibold'>{addon.name}</h3>
                {addon.local_version && (
                  <h4 className='text-secondary text-sm font-normal'>
                    {t('addons.localVersion', { version: addon.local_version })}
                  </h4>
                )}
              </div>
              {createAddonButton(addon)}
            </div>
            <p>{addon.description}</p>
            {addon.can_update && (
              <button onClick={() => handleUpdate(addon)} className='button-primary-filled p-2 px-4 mt-6 w-full'>
                {t('addons.update', { version: addon.version })}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AddonManager;
