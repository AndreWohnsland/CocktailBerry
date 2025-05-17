import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus, FaSave } from 'react-icons/fa';
import { RxCrossCircled } from 'react-icons/rx';
import { updateOptions, useConfig } from '../../api/options';
import { useConfig as useConfigProvider } from '../../providers/ConfigProvider';
import { ConfigData, PossibleConfigValue, PossibleConfigValueTypes } from '../../types/models';
import { executeAndShow, isInCurrentTab } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TabSelector from './TabSelector';

// some of the config are "old" meaning they are only used in the QT but not React UI
// we will define them here and skip the values for those (e.g. not generate input fields)
const configToIgnore = ['UI_WIDTH', 'UI_HEIGHT', 'UI_PICTURE_SIZE'];
const colorConfigs = [
  'CUSTOM_COLOR_PRIMARY',
  'CUSTOM_COLOR_SECONDARY',
  'CUSTOM_COLOR_NEUTRAL',
  'CUSTOM_COLOR_BACKGROUND',
  'CUSTOM_COLOR_DANGER',
];

const ConfigWindow: React.FC = () => {
  const { data, isLoading, error } = useConfig();
  const [configData, setConfigData] = useState<ConfigData>({});
  const [selectedTab, setSelectedTab] = useState('UI');
  const { refetchConfig, changeTheme } = useConfigProvider();
  const { t } = useTranslation();

  useEffect(() => {
    if (data) {
      // need to extract ConfigDataWithUiInfo to ConfigData (extract key: {value: value} to key: value)
      const extractedData: { [key: string]: PossibleConfigValue } = {};
      Object.keys(data).forEach((key) => {
        if (configToIgnore.includes(key)) {
          return;
        }
        extractedData[key] = data[key].value;
      });
      setConfigData(extractedData);
    }
  }, [data]);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const getBaseConfig = (
    key: string,
  ): { prefix?: string; suffix?: string; immutable: boolean; allowed?: string[]; checkName: string } => {
    const baseConfigRegex = /^([^[\].]+)/;
    const nestedPropertyRegex = /\.([^.]+)$/;

    const baseConfigMatch = baseConfigRegex.exec(key);
    const baseConfigName = baseConfigMatch ? baseConfigMatch[0] : '';

    const nestedPropertyMatch = nestedPropertyRegex.exec(key);
    const nestedProperty = nestedPropertyMatch ? nestedPropertyMatch[1] : '';

    const selectedData = data?.[baseConfigName];
    const nestedData = selectedData?.[nestedProperty] ?? selectedData;
    return {
      prefix: nestedData?.prefix,
      suffix: nestedData?.suffix,
      immutable: selectedData?.immutable ?? false,
      allowed: nestedData?.allowed,
      checkName: nestedData?.check_name ?? 'on',
    };
  };

  const handleInputChange = (key: string, value: any) => {
    // this can be a little tricky, since we need to update nested objects and arrays
    // we can have just the key, key[index], key.attribute, key[index].attribute
    // exampled are: TEAM_BUTTON_NAMES[3] or PUMP_CONFIG[10].pin
    setConfigData((prevData) => {
      const newData = { ...prevData };
      const keyParts = key.match(/([^[\].]+)/g); // Split into parts: list names, indexes, and object attributes

      if (!keyParts) {
        return prevData; // If no valid key structure is found, return unchanged data
      }

      let current = newData;
      for (let i = 0; i < keyParts.length; i++) {
        const part = keyParts[i];

        if (i === keyParts.length - 1) {
          // If it's the last part, update the value
          current[part] = value;
        } else {
          const nextPart = keyParts[i + 1];

          if (/^\d+$/.test(nextPart)) {
            // If the next part is an index, ensure it's an array
            current[part] = current[part] ?? [];
            current = current[part] as { [key: string]: PossibleConfigValue };
          } else {
            // Otherwise, it's an object
            current[part] = current[part] ?? {};
            current = current[part] as { [key: string]: PossibleConfigValue };
          }
        }
      }
      return newData;
    });
  };

  const renderBooleanField = (key: string, value: boolean) => {
    const baseConfig = getBaseConfig(key);
    return (
      <label className='flex items-center'>
        <input
          type='checkbox'
          checked={value}
          onChange={(e) => handleInputChange(key, e.target.checked)}
          className='checkbox-large'
        />
        <span className='ml-2'>{baseConfig.checkName}</span>
      </label>
    );
  };

  const renderSelectionField = (key: string, value: string | number, allowedValues: (string | number)[]) => (
    <select value={value} onChange={(e) => handleInputChange(key, e.target.value)} className='select-base'>
      {allowedValues.map((allowedValue) => (
        <option key={allowedValue} value={allowedValue}>
          {allowedValue}
        </option>
      ))}
    </select>
  );

  const renderNumberField = (key: string, value: number) => {
    const baseConfig = getBaseConfig(key);
    return (
      <>
        {baseConfig.prefix && <span className='text-neutral mx-1'>{baseConfig.prefix}</span>}
        <input
          type='number'
          value={value.toString()}
          onChange={(e) => {
            const numericValue = parseFloat(e.target.value);
            handleInputChange(key, isNaN(numericValue) ? 0 : numericValue);
          }}
          className='input-base'
        />
        {baseConfig.suffix && <span className='text-neutral mx-1'>{baseConfig.suffix}</span>}
      </>
    );
  };

  const renderStringField = (key: string, value: string) => {
    const baseConfig = getBaseConfig(key);
    return (
      <>
        {baseConfig.prefix && <span className='text-neutral mr-1'>{baseConfig.prefix}</span>}
        <input
          type='text'
          value={value}
          onChange={(e) => handleInputChange(key, e.target.value)}
          className='input-base'
        />
        {baseConfig.suffix && <span className='text-neutral ml-1'>{baseConfig.suffix}</span>}
      </>
    );
  };

  const renderObjectField = (key: string, value: { [key: string]: PossibleConfigValueTypes }) => (
    <div className='flex flex-row w-full'>
      {Object.keys(value).map((subKey) => (
        <div key={subKey} className='flex items-center w-full'>
          {renderInputField(`${key}.${subKey}`, value[subKey])}
        </div>
      ))}
    </div>
  );

  const renderColorField = (key: string, value: string) => {
    return (
      <div className='flex flex-row items-center w-full'>
        <input type='color' value={value} onChange={(e) => handleInputChange(key, e.target.value)} className='w-full' />
        <span className='ml-2 w-20 text-neutral'>{value}</span>
      </div>
    );
  };

  const renderListField = (key: string, value: any[]) => {
    const defaultValue = value.length > 0 ? value[0] : '';
    const baseConfig = getBaseConfig(key);
    return (
      <div className='flex flex-col items-center w-full'>
        {value.map((item, index) => (
          <div key={index} className='flex items-center mb-1 w-full'>
            <span className='mr-1 font-bold text-secondary min-w-4'>{index + 1}</span>
            {renderInputField(`${key}[${index}]`, item)}
            {!baseConfig.immutable && (
              <button className='text-danger ml-2' onClick={() => handleRemoveItem(key, index)}>
                <RxCrossCircled size={30} />
              </button>
            )}
          </div>
        ))}
        {!baseConfig.immutable && (
          <button
            onClick={() => handleAddItem(key, defaultValue)}
            className='flex justify-center items-center mb-2 mt-1 p-1 button-neutral w-full'
          >
            <FaPlus size={20} />
            <span className='ml-2'>Add</span>
          </button>
        )}
      </div>
    );
  };

  const renderInputField = (key: string, value: PossibleConfigValue) => {
    const baseConfig = getBaseConfig(key);
    if (Array.isArray(value)) {
      return renderListField(key, value);
    }
    if (typeof value === 'object') {
      return renderObjectField(key, value);
    }

    return (
      <div className='flex flex-row items-center w-full justify-center'>
        {typeof value !== 'boolean' && baseConfig.allowed ? (
          renderSelectionField(key, value, baseConfig.allowed)
        ) : (
          <>
            {typeof value === 'boolean' && renderBooleanField(key, value)}
            {typeof value === 'number' && renderNumberField(key, value)}
            {typeof value === 'string' && colorConfigs.includes(key) && renderColorField(key, value)}
            {typeof value === 'string' && !colorConfigs.includes(key) && renderStringField(key, value)}
          </>
        )}
      </div>
    );
  };

  const handleAddItem = (key: string, defaultValue: PossibleConfigValue) => {
    setConfigData((prevData) => ({
      ...prevData,
      [key]: Array.isArray(prevData[key])
        ? [...prevData[key], getDefaultValue(defaultValue)]
        : [getDefaultValue(defaultValue)],
    }));
  };

  const getDefaultValue = (value: PossibleConfigValue) => {
    if (typeof value === 'boolean') {
      return false;
    } else if (typeof value === 'number') {
      return 0;
    } else if (typeof value === 'string') {
      return '';
    } else if (Array.isArray(value)) {
      return [];
    } else if (typeof value === 'object') {
      return Object.keys(value).reduce((acc, key) => {
        acc[key] = getDefaultValue(value[key]);
        return acc;
      }, {} as any);
    }
    console.log('Unknown type');
    return null;
  };

  const handleRemoveItem = (key: string, index: number) => {
    setConfigData((prevData) => {
      const updatedArray = Array.isArray(prevData[key])
        ? prevData[key].filter((_: any, i: number) => i !== index)
        : prevData[key];
      return {
        ...prevData,
        [key]: updatedArray as PossibleConfigValue,
      };
    });
  };

  const postConfig = () => {
    executeAndShow(() => updateOptions(configData)).then((success) => {
      if (success) {
        changeTheme(configData.MAKER_THEME as string);
        refetchConfig();
      }
    });
  };

  return (
    <>
      <TabSelector selectedTab={selectedTab} onSelectTab={setSelectedTab} />
      <div className='flex flex-col w-full max-w-3xl items-center justify-center mt-8'>
        <div className='flex-grow p-2 w-full'>
          {Object.keys(configData).map(
            (key) =>
              isInCurrentTab(key, selectedTab) && (
                <div key={key} className='mb-4 flex flex-col items-center'>
                  <h3 className='text-secondary text-lg font-bold mb-1'>{key}</h3>
                  {data && <p className='text-neutral mb-2 text-center'>{data[key].description}</p>}
                  {renderInputField(key, configData[key])}
                </div>
              ),
          )}
        </div>
        <div className='flex flex-col items-center justify-center w-full px-2'>
          <button
            onClick={postConfig}
            className='button-primary-filled p-2 w-full mb-2 flex items-center justify-center'
          >
            <FaSave className='mr-2' size={20} />
            {t('save')}
          </button>
        </div>
      </div>
    </>
  );
};

export default ConfigWindow;
