import { useConfig } from '../../ConfigProvider';
import {
  cleanMachine,
  rebootSystem,
  shutdownSystem,
  updateSystem,
  updateSoftware,
  checkInternetConnection,
  createBackup,
  uploadBackup,
  updateOptions,
} from '../../api/options';
import { confirmAndExecute, executeAndShow } from '../../utils';
import { useNavigate } from 'react-router-dom';
import ProgressModal from '../cocktail/ProgressModal';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const OptionWindow = () => {
  const { theme, changeTheme } = useConfig();
  const navigate = useNavigate();
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const themes = ['default', 'berry', 'bavaria', 'alien', 'custom'];
  const { t } = useTranslation();

  const cleanClick = async () => {
    const started = await confirmAndExecute(t('options.startCleaningProgram'), cleanMachine);
    if (!started) return;
    setIsProgressModalOpen(true);
  };

  const getBackupClick = async () => {
    try {
      const { data, fileName } = await createBackup();
      const options = {
        suggestedName: fileName,
        types: [
          {
            description: 'Backup Files',
            accept: { 'application/octet-stream': ['.zip'] },
          },
        ],
      };
      const fileHandle = await window.showSaveFilePicker(options);
      const writable = await fileHandle.createWritable();
      await writable.write(new Blob([data], { type: 'application/octet-stream' }));
      await writable.close();
    } catch (error) {
      console.error('Error saving backup:', error);
    }
  };

  const uploadBackupClick = async () => {
    let file = undefined;
    try {
      const [fileHandle] = await window.showOpenFilePicker();
      file = await fileHandle.getFile();
    } catch {
      return;
    }
    return uploadBackup(file);
  };

  const themeSelect = async (theme: string) => {
    const success = await executeAndShow(() => updateOptions({ MAKER_THEME: theme }));
    if (success) changeTheme(theme);
  };

  return (
    <>
      <ProgressModal
        isOpen={isProgressModalOpen}
        onRequestClose={() => setIsProgressModalOpen(false)}
        progress={0}
        displayName={t('options.cleaningTheMachine')}
      />
      <div className='flex flex-col items-center max-w-5xl w-full p-2 pt-0'>
        <div className='dropdown-container flex flex-row items-center mb-4 w-full max-w-md'>
          <p className='mr-2 text-neutral'>Theme:</p>
          <select className='select-base w-full !p-2' value={theme} onChange={(e) => themeSelect(e.target.value)}>
            {themes.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div className='grid gap-1 w-full grid-cols-1 md:grid-cols-2'>
          <button className='button-primary-filled p-4' onClick={cleanClick}>
            {t('options.cleaning')}
          </button>
          <button className='button-primary p-4' onClick={() => navigate('calibration')}>
            {t('options.calibration')}
          </button>
          <button className='button-primary-filled p-4' onClick={() => navigate('configuration')}>
            {t('options.configuration')}
          </button>
          <button className='button-primary p-4' onClick={() => navigate('data')}>
            {t('options.data')}
          </button>
          <button className='button-primary p-4' onClick={() => executeAndShow(getBackupClick)}>
            {t('options.backup')}
          </button>
          <button className='button-primary p-4' onClick={() => executeAndShow(uploadBackupClick)}>
            {t('options.restore')}
          </button>
          <button
            className='button-primary p-4'
            onClick={() => confirmAndExecute(t('options.rebootTheSystem'), rebootSystem)}
          >
            {t('options.reboot')}
          </button>
          <button
            className='button-primary p-4'
            onClick={() => confirmAndExecute(t('options.shutdownTheSystem'), shutdownSystem)}
          >
            {t('options.shutdown')}
          </button>
          <button className='button-primary p-4' onClick={() => navigate('logs')}>
            {t('options.logs')}
          </button>
          <button
            className='button-primary-filled p-4'
            onClick={() => confirmAndExecute(t('options.updateTheSystem'), updateSystem)}
          >
            {t('options.updateSystem')}
          </button>
          <button
            className='button-primary-filled p-4 col-span-1 md:col-span-2'
            onClick={() => executeAndShow(updateSoftware)}
          >
            {t('options.updateCocktailBerry')}
          </button>
          <button className='button-primary p-4' onClick={() => navigate('wifi')}>
            {t('options.wifi')}
          </button>
          <button className='button-primary p-4' onClick={() => executeAndShow(checkInternetConnection)}>
            {t('options.internetCheck')}
          </button>
          <button className='button-primary p-4' onClick={() => navigate('addons')}>
            {t('options.addons')}
          </button>
          <button className='button-neutral p-4' disabled={true}>
            {t('options.writeRfid')}
          </button>
        </div>
      </div>
    </>
  );
};

export default OptionWindow;
