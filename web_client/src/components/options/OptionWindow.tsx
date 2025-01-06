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
import { MdOutlineSignalWifiStatusbarConnectedNoInternet4, MdWaterDrop } from 'react-icons/md';
import { FaChartSimple, FaDownload, FaGear, FaScaleUnbalanced, FaUpload, FaWifi } from 'react-icons/fa6';
import { BsBootstrapReboot } from 'react-icons/bs';
import { RiShutDownLine } from 'react-icons/ri';
import { GrUpdate } from 'react-icons/gr';
import { FaCocktail, FaExclamationTriangle, FaInfoCircle, FaRegClock } from 'react-icons/fa';
import { TiDocumentAdd } from 'react-icons/ti';

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
          <button className='button-primary-filled p-4 flex items-center justify-center' onClick={cleanClick}>
            <MdWaterDrop size={22} className='mr-2' />
            {t('options.cleaning')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => navigate('calibration')}
          >
            <FaScaleUnbalanced size={20} className='mr-2' />
            {t('options.calibration')}
          </button>
          <button
            className='button-primary-filled p-4 flex items-center justify-center'
            onClick={() => navigate('configuration')}
          >
            <FaGear size={20} className='mr-2' />
            {t('options.configuration')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('data')}>
            <FaChartSimple size={20} className='mr-2' />
            {t('options.data')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => executeAndShow(getBackupClick)}
          >
            <FaDownload size={20} className='mr-2' />
            {t('options.backup')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => executeAndShow(uploadBackupClick)}
          >
            <FaUpload size={20} className='mr-2' />
            {t('options.restore')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => confirmAndExecute(t('options.rebootTheSystem'), rebootSystem)}
          >
            <BsBootstrapReboot size={20} className='mr-2' />
            {t('options.reboot')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => confirmAndExecute(t('options.shutdownTheSystem'), shutdownSystem)}
          >
            <RiShutDownLine size={20} className='mr-2' />
            {t('options.shutdown')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('logs')}>
            <FaInfoCircle size={20} className='mr-2' />
            {t('options.logs')}
          </button>
          <button
            className='button-primary-filled p-4 flex items-center justify-center'
            onClick={() => confirmAndExecute(t('options.updateTheSystem'), updateSystem)}
          >
            <GrUpdate size={20} className='mr-2' />
            {t('options.updateSystem')}
          </button>
          <button
            className='button-primary-filled p-4 col-span-1 md:col-span-2 flex items-center justify-center'
            onClick={() => executeAndShow(updateSoftware)}
          >
            <FaCocktail size={20} className='mr-2' />
            {t('options.updateCocktailBerry')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('wifi')}>
            <FaWifi size={20} className='mr-2' />
            {t('options.wifi')}
          </button>
          <button
            className='button-primary p-4 flex items-center justify-center'
            onClick={() => executeAndShow(checkInternetConnection)}
          >
            <MdOutlineSignalWifiStatusbarConnectedNoInternet4 size={20} className='mr-2' />
            {t('options.internetCheck')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('addons')}>
            <TiDocumentAdd size={24} className='mr-2' />
            {t('options.addons')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('time')}>
            <FaRegClock size={20} className='mr-2' />
            {t('options.adjustTime')}
          </button>
          <button className='button-primary p-4 flex items-center justify-center' onClick={() => navigate('/issues')}>
            <FaExclamationTriangle size={20} className='mr-2' />
            {t('options.issues')}
          </button>
        </div>
      </div>
    </>
  );
};

export default OptionWindow;
