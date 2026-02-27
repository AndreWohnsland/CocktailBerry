import type React from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus, FaTrashAlt } from 'react-icons/fa';
import { addAddon, deleteAddon, updateAddon, useAddonData } from '../../api/options';
import type { AddonData } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import Button from '../common/Button';
import ErrorComponent from '../common/ErrorComponent';
import ItemCard from '../common/ItemCard';
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
        <Button
          filled
          icon={FaPlus}
          label={`${t('add')} (${addon.version})`}
          className='px-4'
          onClick={() => handleInstall(addon)}
        />
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
        <Button
          style='danger'
          filled
          icon={FaTrashAlt}
          label={t('delete')}
          className='px-4'
          onClick={() => handleDelete(addon)}
        />
      );
    }
  };
  return (
    <div className='p-4 w-full max-w-3xl'>
      <TextHeader text={t('addons.manageAddons')} />
      <div className='grid grid-cols-1 gap-2'>
        {sortedAddons?.map((addon) => (
          <ItemCard
            key={addon.name}
            title={addon.name}
            subtitle={addon.local_version ? t('addons.localVersion', { version: addon.local_version }) : undefined}
            description={addon.description}
            actions={createAddonButton(addon)}
          >
            {addon.can_update && (
              <Button
                filled
                label={t('addons.update', { version: addon.version })}
                className='px-4 mt-6 w-full'
                onClick={() => handleUpdate(addon)}
              />
            )}
          </ItemCard>
        ))}
      </div>
    </div>
  );
};

export default AddonManager;
