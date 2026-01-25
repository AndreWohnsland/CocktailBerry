import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AiOutlineLoading3Quarters } from 'react-icons/ai';
import { BsBootstrapReboot, BsInfoCircleFill } from 'react-icons/bs';
import { FaCocktail, FaExclamationTriangle, FaInfoCircle, FaNewspaper, FaRegClock } from 'react-icons/fa';
import { FaCalculator, FaChartSimple, FaDownload, FaGear, FaScaleUnbalanced, FaUpload, FaWifi } from 'react-icons/fa6';
import { GrUpdate } from 'react-icons/gr';
import { MdOutlineSignalWifiStatusbarConnectedNoInternet4, MdWaterDrop } from 'react-icons/md';
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
import { useConfig } from '../../providers/ConfigProvider';
import { confirmAndExecute, executeAndShow } from '../../utils';
import ProgressModal from '../cocktail/ProgressModal';
import DropDown from '../common/DropDown';
import TileButton from '../common/TileButton';
import AboutModal from './AboutModal';

const OptionWindow = () => {
  const { theme, changeTheme } = useConfig();
  const navigate = useNavigate();
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const { data: aboutInfo } = useAboutInfo();
  const themes = ['default', 'berry', 'bavaria', 'alien', 'tropical', 'purple', 'custom'];
  const { t } = useTranslation();

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
          <TileButton label={t('options.cleaning')} filled icon={MdWaterDrop} iconSize={22} onClick={cleanClick} />
          <TileButton
            label={t('options.calibration')}
            filled
            icon={FaScaleUnbalanced}
            onClick={() => navigate('calibration')}
          />
          <TileButton
            label={t('options.configuration')}
            filled
            icon={FaGear}
            onClick={() => navigate('configuration')}
          />
          <TileButton label={t('options.data')} icon={FaChartSimple} onClick={() => navigate('data')} />
          <TileButton label={t('options.backup')} icon={FaDownload} onClick={() => executeAndShow(getBackupClick)} />
          <TileButton label={t('options.restore')} icon={FaUpload} onClick={() => executeAndShow(uploadBackupClick)} />
          <TileButton
            label={t('options.reboot')}
            icon={BsBootstrapReboot}
            onClick={() => confirmAndExecute(t('options.rebootTheSystem'), rebootSystem)}
          />
          <TileButton
            label={t('options.shutdown')}
            icon={RiShutDownLine}
            onClick={() => confirmAndExecute(t('options.shutdownTheSystem'), shutdownSystem)}
          />
          <TileButton label={t('options.logs')} icon={FaInfoCircle} onClick={() => navigate('logs')} />
          <TileButton
            label={t('options.updateSystem')}
            filled
            icon={GrUpdate}
            onClick={() => confirmAndExecute(t('options.updateTheSystem'), updateSystem)}
          />
          <TileButton
            label={t('options.systemResourceUsage')}
            icon={AiOutlineLoading3Quarters}
            iconSize={22}
            className='md:col-span-2'
            onClick={() => navigate('resources')}
          />
          <TileButton
            label={t('options.updateCocktailBerry')}
            filled
            icon={FaCocktail}
            className='md:col-span-2'
            onClick={() => executeAndShow(updateSoftware)}
          />
          <TileButton label={t('options.wifi')} icon={FaWifi} onClick={() => navigate('wifi')} />
          <TileButton
            label={t('options.internetCheck')}
            icon={MdOutlineSignalWifiStatusbarConnectedNoInternet4}
            onClick={() => executeAndShow(checkInternetConnection)}
          />
          <TileButton
            label={t('options.addons')}
            icon={TiDocumentAdd}
            iconSize={24}
            onClick={() => navigate('addons')}
          />
          <TileButton label={t('options.adjustTime')} icon={FaRegClock} onClick={() => navigate('time')} />
          <TileButton label={t('options.issues')} icon={FaExclamationTriangle} onClick={() => navigate('/issues')} />
          <TileButton
            label={t('recipeCalculation.title')}
            filled
            icon={FaCalculator}
            onClick={() => navigate('/manage/recipes/calculation')}
          />
          <TileButton label={t('options.news')} icon={FaNewspaper} onClick={() => navigate('news')} />
          <TileButton label={t('options.about')} icon={BsInfoCircleFill} onClick={() => setIsAboutModalOpen(true)} />
        </div>
      </div>
      <AboutModal isOpen={isAboutModalOpen} onClose={() => setIsAboutModalOpen(false)} aboutInfo={aboutInfo} />
    </>
  );
};

export default OptionWindow;
