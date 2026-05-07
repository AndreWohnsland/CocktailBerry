import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AiOutlineLoading3Quarters } from 'react-icons/ai';
import { BsBootstrapReboot, BsInfoCircleFill } from 'react-icons/bs';
import {
  FaCocktail,
  FaCreditCard,
  FaExclamationTriangle,
  FaInfoCircle,
  FaNewspaper,
  FaRegClock,
  FaUserTie,
} from 'react-icons/fa';
import { FaCalculator, FaChartSimple, FaDownload, FaGear, FaScaleUnbalanced, FaUpload, FaWifi } from 'react-icons/fa6';
import { GrUpdate } from 'react-icons/gr';
import { MdEventNote, MdOutlineSignalWifiStatusbarConnectedNoInternet4, MdWaterDrop } from 'react-icons/md';
import { RiShutDownLine } from 'react-icons/ri';
import { TiDocumentAdd } from 'react-icons/ti';
import { useNavigate } from 'react-router-dom';
import {
  checkInternetConnection,
  cleanMachine,
  createBackup,
  rebootSystem,
  shutdownSystem,
  updateOptions,
  updateSoftware,
  updateSystem,
  uploadBackup,
  useAboutInfo,
} from '../../api/options';
import { useAuth } from '../../providers/AuthProvider';
import { useConfig } from '../../providers/ConfigProvider';
import { useWaiter } from '../../providers/WaiterProvider';
import type { OptionTileName } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import DropDown from '../common/DropDown';
import ProgressModal from '../common/ProgressModal';
import TileButton from '../common/TileButton';
import AboutModal from './AboutModal';

const OptionWindow = () => {
  const { theme, changeTheme, config, isTileBlacklisted } = useConfig();
  const navigate = useNavigate();
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const { data: aboutInfo } = useAboutInfo();
  const themes = ['default', 'berry', 'bavaria', 'alien', 'tropical', 'purple', 'custom'];
  const { t } = useTranslation();
  const { masterAuthenticated } = useAuth();
  const { waiterState } = useWaiter();
  const showTile = (tile: OptionTileName) => {
    if (isTileBlacklisted(tile)) return false;
    if (masterAuthenticated || !config.WAITER_MODE) return true;
    const waiter = waiterState?.waiter;
    return waiter == null ? true : Boolean(waiter.tile_permissions?.[tile]);
  };

  const cleanClick = async () => {
    const started = await confirmAndExecute(t('options.startCleaningProgram'), cleanMachine);
    if (!started) return;
    setIsProgressModalOpen(true);
  };

  const getBackupClick = async () => {
    const { data, fileName } = await createBackup();
    const blob = new Blob([data], { type: 'application/octet-stream' });

    if (globalThis.window.isSecureContext) {
      const options = {
        suggestedName: fileName,
        types: [
          {
            description: 'Backup Files',
            accept: { 'application/octet-stream': ['.zip'] },
          },
        ],
      };

      const fileHandle = await globalThis.window.showSaveFilePicker(options);
      const writable = await fileHandle.createWritable();
      await writable.write(blob);
      await writable.close();

      return t('options.backupSavedSuccessfully', { fileName: fileHandle.name });
    }

    // Fallback: force browser download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    return t('options.backupSavedSuccessfully', { fileName });
  };

  const uploadBackupClick = async () => {
    if (globalThis.window.isSecureContext) {
      const [fileHandle] = await globalThis.window.showOpenFilePicker();
      const file = await fileHandle.getFile();
      return uploadBackup(file);
    }

    // Fallback
    return new Promise((resolve) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.onchange = () => {
        const files = input.files;
        if (!files || files.length === 0) {
          resolve(undefined);
          return;
        }
        resolve(uploadBackup(files[0]));
      };
      input.click();
    });
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
          <DropDown
            value={theme}
            allowedValues={Object.fromEntries(themes.map((t) => [t, t.charAt(0).toUpperCase() + t.slice(1)]))}
            handleInputChange={(value) => themeSelect(value)}
            className='!p-2'
          />
        </div>
        <div className='grid gap-1 w-full grid-cols-1 md:grid-cols-2'>
          {showTile('cleaning') && (
            <TileButton label={t('options.cleaning')} filled icon={MdWaterDrop} iconSize={22} onClick={cleanClick} />
          )}
          {showTile('calibration') && (
            <TileButton
              label={t('options.calibration')}
              filled
              icon={FaScaleUnbalanced}
              onClick={() => navigate('calibration')}
            />
          )}
          {config.SCALE_CONFIG?.enabled && showTile('scale_calibration') && (
            <TileButton
              label={t('options.scaleCalibration')}
              filled
              icon={FaCalculator}
              onClick={() => navigate('scale-calibration')}
            />
          )}
          {showTile('configuration') && (
            <TileButton
              label={t('options.configuration')}
              filled
              icon={FaGear}
              onClick={() => navigate('configuration')}
            />
          )}
          {showTile('data') && (
            <TileButton label={t('options.data')} icon={FaChartSimple} onClick={() => navigate('data')} />
          )}
          {showTile('backup') && (
            <TileButton label={t('options.backup')} icon={FaDownload} onClick={() => executeAndShow(getBackupClick)} />
          )}
          {showTile('restore') && (
            <TileButton
              label={t('options.restore')}
              icon={FaUpload}
              onClick={() => executeAndShow(uploadBackupClick)}
            />
          )}
          {showTile('reboot') && (
            <TileButton
              label={t('options.reboot')}
              icon={BsBootstrapReboot}
              onClick={() => confirmAndExecute(t('options.rebootTheSystem'), rebootSystem)}
            />
          )}
          {showTile('shutdown') && (
            <TileButton
              label={t('options.shutdown')}
              icon={RiShutDownLine}
              onClick={() => confirmAndExecute(t('options.shutdownTheSystem'), shutdownSystem)}
            />
          )}
          {showTile('logs') && (
            <TileButton label={t('options.logs')} icon={FaInfoCircle} onClick={() => navigate('logs')} />
          )}
          {showTile('system_resource_usage') && (
            <TileButton
              label={t('options.systemResourceUsage')}
              icon={AiOutlineLoading3Quarters}
              iconSize={22}
              onClick={() => navigate('resources')}
            />
          )}
          {showTile('events') && (
            <TileButton
              label={t('options.events')}
              icon={MdEventNote}
              iconSize={24}
              onClick={() => navigate('events')}
            />
          )}
          {showTile('update_system') && (
            <TileButton
              label={t('options.updateSystem')}
              filled
              icon={GrUpdate}
              onClick={() => confirmAndExecute(t('options.updateTheSystem'), updateSystem)}
            />
          )}
          {showTile('update_software') && (
            <TileButton
              label={t('options.updateCocktailBerry')}
              filled
              icon={FaCocktail}
              className='md:col-span-2'
              onClick={() => executeAndShow(updateSoftware)}
            />
          )}
          {showTile('wifi') && <TileButton label={t('options.wifi')} icon={FaWifi} onClick={() => navigate('wifi')} />}
          {showTile('internet_check') && (
            <TileButton
              label={t('options.internetCheck')}
              icon={MdOutlineSignalWifiStatusbarConnectedNoInternet4}
              onClick={() => executeAndShow(checkInternetConnection)}
            />
          )}
          {showTile('addons') && (
            <TileButton
              label={t('options.addons')}
              icon={TiDocumentAdd}
              iconSize={24}
              onClick={() => navigate('addons')}
            />
          )}
          {showTile('adjust_time') && (
            <TileButton label={t('options.adjustTime')} icon={FaRegClock} onClick={() => navigate('time')} />
          )}
          {showTile('issues') && (
            <TileButton label={t('options.issues')} icon={FaExclamationTriangle} onClick={() => navigate('/issues')} />
          )}
          {showTile('recipe_calculation') && (
            <TileButton
              label={t('recipeCalculation.title')}
              filled
              icon={FaCalculator}
              onClick={() => navigate('/manage/recipes/calculation')}
            />
          )}
          {showTile('news') && (
            <TileButton label={t('options.news')} icon={FaNewspaper} onClick={() => navigate('news')} />
          )}
          {config.PAYMENT_TYPE === 'SumUp' && showTile('sumup') && (
            <TileButton label={t('options.sumup')} icon={FaCreditCard} onClick={() => navigate('sumup')} />
          )}
          {config.WAITER_MODE && showTile('waiters') && (
            <TileButton label={t('options.waiters')} icon={FaUserTie} onClick={() => navigate('waiters')} />
          )}
          {showTile('about') && (
            <TileButton label={t('options.about')} icon={BsInfoCircleFill} onClick={() => setIsAboutModalOpen(true)} />
          )}
        </div>
      </div>
      <AboutModal isOpen={isAboutModalOpen} onClose={() => setIsAboutModalOpen(false)} aboutInfo={aboutInfo} />
    </>
  );
};

export default OptionWindow;
