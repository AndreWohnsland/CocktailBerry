import { useTheme } from '../../ThemeProvider';
import {
  cleanMachine,
  rebootSystem,
  shutdownSystem,
  updateSystem,
  updateSoftware,
  updateWifiData,
  checkInternetConnection,
  getAddonData,
  getRfidWriter,
} from '../../api/options';
import { ToastContainer } from 'react-toastify';
import { confirmAndExecute, executeAndShow } from '../../utils';
import { useNavigate } from 'react-router-dom';
import ProgressModal from '../cocktail/ProgressModal';
import { useState } from 'react';

const OptionWindow = () => {
  const { theme, onThemeChange } = useTheme();
  const navigate = useNavigate();
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const themes = ['default', 'berry', 'bavaria', 'alien', 'custom'];

  const cleanClick = async () => {
    const started = await executeAndShow(cleanMachine);
    if (!started) return;
    setIsProgressModalOpen(true);
  };

  return (
    <>
      <ToastContainer position='top-center' />
      <ProgressModal
        isOpen={isProgressModalOpen}
        onRequestClose={() => setIsProgressModalOpen(false)}
        progress={0}
        displayName={'Cleaning the Machine'}
      />
      <div className='flex flex-col items-center max-w-5xl w-full p-2 pt-0'>
        <div className='dropdown-container flex flex-row items-center mb-4'>
          <p className='mr-2'>Theme:</p>
          <select
            className='theme-dropdown select-base w-full p-2'
            value={theme}
            onChange={(e) => onThemeChange(e.target.value)}
          >
            {themes.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div className='grid gap-1 w-full grid-cols-1 md:grid-cols-2'>
          <button className='button-primary-filled p-4' onClick={cleanClick}>
            Cleaning
          </button>
          <button className='button-primary p-4' onClick={() => navigate('/calibration')}>
            Calibration
          </button>
          <button className='button-primary-filled p-4' onClick={() => navigate('/options/configuration')}>
            Configuration
          </button>
          <button className='button-primary p-4' onClick={() => navigate('/data')}>
            Data
          </button>
          <button className='button-primary p-4' onClick={async () => Promise.resolve(console.log('Backup action'))}>
            Backup
          </button>
          <button className='button-primary p-4' onClick={async () => Promise.resolve(console.log('Restore action'))}>
            Restore
          </button>
          <button className='button-primary p-4' onClick={() => confirmAndExecute('reboot', rebootSystem)}>
            Reboot
          </button>
          <button className='button-primary p-4' onClick={() => confirmAndExecute('shutdown', shutdownSystem)}>
            Shutdown
          </button>
          <button className='button-primary p-4' onClick={() => navigate('/logs')}>
            Logs
          </button>
          <button className='button-primary-filled p-4' onClick={updateSystem}>
            Update System
          </button>
          <button
            className='button-primary-filled p-4 col-span-1 md:col-span-2'
            onClick={() => executeAndShow(updateSoftware)}
          >
            Update CocktailBerry Software
          </button>
          <button className='button-primary p-4' onClick={updateWifiData}>
            WiFi
          </button>
          <button className='button-primary p-4' onClick={() => executeAndShow(checkInternetConnection)}>
            Internet Check
          </button>
          <button className='button-primary p-4' onClick={getAddonData}>
            Addons
          </button>
          <button className='button-primary p-4' onClick={getRfidWriter}>
            Write RFID
          </button>
        </div>
      </div>
    </>
  );
};

export default OptionWindow;
