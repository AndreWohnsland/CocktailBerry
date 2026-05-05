import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaEdit, FaPlus, FaTrashAlt } from 'react-icons/fa';
import { createRole, deleteRole, updateRole, useRoles } from '../../../api/roles';
import type { OptionTiles, Role, TabPermission } from '../../../types/models';
import { confirmAndExecute, executeAndShow } from '../../../utils';
import Button from '../../common/Button';
import CheckBox from '../../common/CheckBox';
import ErrorComponent from '../../common/ErrorComponent';
import ItemCard from '../../common/ItemCard';
import LoadingData from '../../common/LoadingData';
import TextInput from '../../common/TextInput';
import TileButton from '../../common/TileButton';
import {
  ALL_TILE_KEYS,
  buildEmptyTiles,
  DEFAULT_PERMISSIONS,
  PERMISSION_KEYS,
  TILE_GROUPS,
  TILE_TRANSLATION_KEYS,
} from './constants';

const RolesTab: React.FC = () => {
  const { data: roles, isLoading, error, refetch } = useRoles();
  const [name, setName] = useState<string>('');
  const [permissions, setPermissions] = useState<TabPermission>({
    ...DEFAULT_PERMISSIONS,
  });
  const [tilePermissions, setTilePermissions] = useState<OptionTiles>(buildEmptyTiles());
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [editingRole, setEditingRole] = useState<number | null>(null);
  const [editName, setEditName] = useState<string>('');
  const [editPermissions, setEditPermissions] = useState<TabPermission>({
    ...DEFAULT_PERMISSIONS,
  });
  const [editTiles, setEditTiles] = useState<OptionTiles>(buildEmptyTiles());
  const { t } = useTranslation();

  const handleCreate = async () => {
    if (!name.trim()) return;
    setIsCreating(true);
    const success = await executeAndShow(async () => {
      const role = await createRole({
        name: name.trim(),
        permissions,
        tile_permissions: tilePermissions,
      });
      return { message: t('role.created', { name: role.name }) };
    });
    setIsCreating(false);
    if (success) {
      setName('');
      setPermissions({ ...DEFAULT_PERMISSIONS });
      setTilePermissions(buildEmptyTiles());
      refetch();
    }
  };

  const handleDelete = async (role: Role) => {
    const success = await confirmAndExecute(t('role.confirmDelete', { name: role.name }), () => deleteRole(role.id));
    if (success) {
      refetch();
    }
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role.id);
    setEditName(role.name);
    setEditPermissions({ ...role.permissions });
    setEditTiles({ ...buildEmptyTiles(), ...role.tile_permissions });
  };

  const handleSaveEdit = async (roleId: number) => {
    if (!editName.trim()) return;
    const success = await executeAndShow(async () => {
      await updateRole(roleId, {
        name: editName.trim(),
        permissions: editPermissions,
        tile_permissions: editTiles,
      });
      return { message: t('role.updated') };
    });
    if (success) {
      setEditingRole(null);
      refetch();
    }
  };

  const handleCancelEdit = () => {
    setEditingRole(null);
  };

  if (isLoading)
    return (
      <div className='flex justify-center w-full'>
        <LoadingData />
      </div>
    );
  if (error) return <ErrorComponent text={error.message} />;

  return (
    <>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleCreate();
        }}
        className='border border-primary p-4 rounded-xl mb-4'
      >
        <h3 className='text-lg text-secondary font-semibold mb-4'>{t('role.create')}</h3>
        <TextInput
          value={name}
          large
          handleInputChange={setName}
          placeholder={t('role.namePlaceholder')}
          className='mb-6'
        />
        <PermissionGrid permissions={permissions} onChange={setPermissions} />
        <TilePermissionGrid tiles={tilePermissions} onChange={setTilePermissions} />
        <TileButton
          label={isCreating ? t('waiter.creating') : t('create')}
          icon={FaPlus}
          textSize='md'
          filled
          disabled={!name.trim() || isCreating}
          onClick={handleCreate}
          className='mt-8'
        />
      </form>

      <div className='grid grid-cols-1 gap-2'>
        {roles?.length === 0 && <p className='text-neutral text-center'>{t('role.noRoles')}</p>}
        {roles?.map((role) => {
          const isEditing = editingRole === role.id;

          if (isEditing) {
            return (
              <div key={role.id} className='border border-secondary rounded-xl p-4'>
                <div className='flex gap-2 items-center mb-3'>
                  <TextInput
                    value={editName}
                    large
                    handleInputChange={setEditName}
                    placeholder={t('role.namePlaceholder')}
                  />
                  <Button filled label={t('save')} className='px-4' onClick={() => handleSaveEdit(role.id)} />
                  <Button label={t('cancel')} className='px-4' onClick={handleCancelEdit} />
                </div>
                <PermissionGrid permissions={editPermissions} onChange={setEditPermissions} />
                <TilePermissionGrid tiles={editTiles} onChange={setEditTiles} />
              </div>
            );
          }

          const activePermissions = PERMISSION_KEYS.filter((key) => role.permissions[key]);
          const activeTiles = ALL_TILE_KEYS.filter((key) => role.tile_permissions[key]);

          return (
            <ItemCard
              key={role.id}
              title={role.name}
              actions={
                <>
                  <Button icon={FaEdit} label={t('edit')} className='px-4' onClick={() => handleEdit(role)} />
                  <Button
                    style='danger'
                    filled
                    icon={FaTrashAlt}
                    label={t('delete')}
                    className='px-4'
                    onClick={() => handleDelete(role)}
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
              {activeTiles.length > 0 && (
                <div className='flex flex-wrap gap-2 mt-2'>
                  {activeTiles.map((key) => (
                    <span key={key} className='text-xs px-2 py-0.5 rounded-full border border-primary text-primary'>
                      {t(TILE_TRANSLATION_KEYS[key])}
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

interface PermissionGridProps {
  permissions: TabPermission;
  onChange: (next: TabPermission) => void;
}

const PermissionGrid: React.FC<PermissionGridProps> = ({ permissions, onChange }) => {
  const { t } = useTranslation();
  return (
    <>
      <p className='text-md text-neutral mb-2'>{t('role.tabPermissions')}</p>
      <div className='grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6'>
        {PERMISSION_KEYS.map((key) => (
          <CheckBox
            key={key}
            value={permissions[key]}
            checkName={t(`waiter.permissions.${key}`)}
            handleInputChange={(val) => onChange({ ...permissions, [key]: val })}
          />
        ))}
      </div>
    </>
  );
};

interface TilePermissionGridProps {
  tiles: OptionTiles;
  onChange: (next: OptionTiles) => void;
}

const TilePermissionGrid: React.FC<TilePermissionGridProps> = ({ tiles, onChange }) => {
  const { t } = useTranslation();
  return (
    <>
      <p className='text-md text-neutral mb-2'>{t('role.tilePermissions')}</p>
      <div className='flex flex-col gap-4 mb-4'>
        {Object.entries(TILE_GROUPS).map(([group, keys]) => (
          <div key={group}>
            <p className='text-xs text-neutral uppercase mb-2'>{t(`role.tileGroups.${group}`)}</p>
            <div className='grid grid-cols-1 sm:grid-cols-2 gap-2'>
              {keys.map((key) => (
                <CheckBox
                  key={key}
                  value={tiles[key]}
                  checkName={t(TILE_TRANSLATION_KEYS[key])}
                  handleInputChange={(val) => onChange({ ...tiles, [key]: val })}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
};

export default RolesTab;
