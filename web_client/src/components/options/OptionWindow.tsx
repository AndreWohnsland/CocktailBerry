import React from 'react';
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

const options = [
  { label: 'Cleaning', size: 1, action: cleanMachine },
  { label: 'Calibration', size: 1, action: async () => Promise.resolve(console.log('Calibration action')) },
  { label: 'Configuration', size: 1, action: async () => Promise.resolve(console.log('Configuration action')) },
  { label: 'Data', size: 1, action: async () => Promise.resolve(console.log('Data action')) },
  { label: 'Backup', size: 1, action: Promise.resolve(console.log('Backup action')) },
  { label: 'Restore', size: 1, action: Promise.resolve(console.log('Restore action')) },
  { label: 'Reboot', size: 1, action: rebootSystem },
  { label: 'Shutdown', size: 1, action: shutdownSystem },
  { label: 'Logs', size: 1, action: async () => Promise.resolve(console.log('Log action')) },
  { label: 'Update System', size: 1, action: updateSystem },
  { label: 'Update CocktailBerry Software', size: 2, action: updateSoftware },
  { label: 'WiFi', size: 1, action: updateWifiData },
  { label: 'Internet Check', size: 1, action: checkInternetConnection },
  { label: 'Addons', size: 1, action: getAddonData },
  { label: 'Write RFID', size: 1, action: getRfidWriter },
];

const OptionWindow = () => {
  const { onThemeChange } = useTheme();
  const themes = ['default', 'berry', 'bavaria', 'alien', 'custom'];

  const handleClick = async (action: () => Promise<any>) => {
    try {
      const result = await action();
      console.log(result);
    } catch (error) {
      console.error('Error executing action:', error);
    }
  };

  return (
    <>
      <div className='flex flex-col items-center max-w-5xl w-full p-2 pt-0'>
        <div className='dropdown-container flex flex-row items-center mb-4'>
          <p className='mr-2'>Theme:</p>
          <select className='theme-dropdown select-base w-full p-2' onChange={(e) => onThemeChange(e.target.value)}>
            {themes.map((theme) => (
              <option key={theme} value={theme}>
                {theme.charAt(0).toUpperCase() + theme.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div className='grid gap-1 w-full grid-cols-1 md:grid-cols-2'>
          {options.map((option, index) => (
            <button
              key={index}
              className={`button-primary p-4 ${option.size === 2 ? 'col-span-1 md:col-span-2' : ''}`}
              onClick={() => handleClick(option.action)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
};

export default OptionWindow;
