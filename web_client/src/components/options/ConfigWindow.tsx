import type React from 'react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaSave } from 'react-icons/fa';
import { updateOptions, useConfig } from '../../api/options';
import { useConfig as useConfigProvider } from '../../providers/ConfigProvider';
import type { ConfigData, PossibleConfigValue, PossibleConfigValueTypes } from '../../types/models';
import { executeAndShow, isInCurrentTab } from '../../utils';
import CheckBox from '../common/CheckBox';
import ColorSelect from '../common/ColorSelect';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import ListDisplay from '../common/ListDisplay';
import LoadingData from '../common/LoadingData';
import NumberInput from '../common/NumberInput';
import TextInput from '../common/TextInput';
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

  const handleInputChange = (key: string, value: boolean | string | number) => {
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
      <CheckBox
        value={value}
        checkName={baseConfig.checkName}
        handleInputChange={(newValue) => handleInputChange(key, newValue)}
      />
    );
  };

  const renderSelectionField = (key: string, value: string | number, allowedValues: (string | number)[]) => (
    <DropDown
      value={String(value)}
      allowedValues={allowedValues.map(String)}
      handleInputChange={(newValue) => handleInputChange(key, newValue)}
    />
  );

  const renderNumberField = (key: string, value: number) => {
    const baseConfig = getBaseConfig(key);
    return (
      <NumberInput
        value={value}
        prefix={baseConfig.prefix}
        suffix={baseConfig.suffix}
        handleInputChange={(newValue) => handleInputChange(key, newValue)}
      />
    );
  };

  const renderStringField = (key: string, value: string) => {
    const baseConfig = getBaseConfig(key);
    return (
      <TextInput
        value={value}
        prefix={baseConfig.prefix}
        suffix={baseConfig.suffix}
        handleInputChange={(newValue) => handleInputChange(key, newValue)}
      />
    );
  };

  const renderObjectField = (key: string, value: { [key: string]: PossibleConfigValueTypes }) => {
    // Check if this is a dynamic config (has discriminator_field)
    const baseConfig = getBaseConfig(key);
    const baseConfigName = key.match(/^([^[\].]+)/)?.[0] || '';
    const selectedData = data?.[baseConfigName];
    
    if (selectedData?.discriminator_field && value[selectedData.discriminator_field]) {
      return renderDynamicConfigField(key, value, selectedData);
    }
    
    // Regular object field
    return (
      <div className='flex flex-row w-full'>
        {Object.keys(value).map((subKey) => (
          <div key={subKey} className='flex items-center w-full'>
            {renderInputField(`${key}.${subKey}`, value[subKey])}
          </div>
        ))}
      </div>
    );
  };

  const renderDynamicConfigField = (
    key: string,
    value: { [key: string]: PossibleConfigValueTypes },
    configInfo: any,
  ) => {
    const discriminatorField = configInfo.discriminator_field;
    const currentType = String(value[discriminatorField] || configInfo.type_options[0]);
    const typeSchemas = configInfo.type_schemas || {};
    const currentSchema = typeSchemas[currentType] || {};

    const handleTypeChange = (newType: string) => {
      // When type changes, we need to rebuild the entire object with new schema
      const newSchema = typeSchemas[newType] || {};
      const newValue: any = { [discriminatorField]: newType };
      
      // Initialize with default values based on schema
      Object.keys(newSchema).forEach((fieldKey) => {
        if (fieldKey === discriminatorField) return;
        const fieldSchema = newSchema[fieldKey];
        
        // Set default values based on type
        if (fieldSchema.check_name !== undefined) {
          newValue[fieldKey] = false;
        } else if (fieldSchema.allowed) {
          newValue[fieldKey] = fieldSchema.allowed[0] || '';
        } else if (fieldSchema.immutable !== undefined) {
          newValue[fieldKey] = [];
        } else {
          newValue[fieldKey] = 0;
        }
      });
      
      handleInputChange(key, newValue);
    };

    return (
      <div className='flex flex-col w-full gap-2'>
        {/* Type selector */}
        <div className='flex flex-row items-center w-full'>
          <span className='text-secondary font-bold mr-2'>Type:</span>
          <DropDown
            value={currentType}
            allowedValues={configInfo.type_options}
            handleInputChange={handleTypeChange}
          />
        </div>

        {/* Dynamic fields based on selected type */}
        <div className='flex flex-col w-full gap-2 pl-4'>
          {Object.keys(currentSchema).map((fieldKey) => {
            if (fieldKey === discriminatorField) return null;
            
            const fieldValue = value[fieldKey];
            const fieldSchema = currentSchema[fieldKey];
            
            return (
              <div key={fieldKey} className='flex flex-col w-full'>
                <span className='text-neutral text-sm mb-1'>{fieldKey}:</span>
                {renderDynamicFieldInput(`${key}.${fieldKey}`, fieldValue, fieldSchema)}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderDynamicFieldInput = (key: string, value: any, fieldSchema: any) => {
    // Handle different field types based on schema
    if (fieldSchema.allowed) {
      // ChooseType
      return (
        <DropDown
          value={String(value)}
          allowedValues={fieldSchema.allowed.map(String)}
          handleInputChange={(newValue) => handleInputChange(key, newValue)}
        />
      );
    } else if (fieldSchema.check_name !== undefined) {
      // BoolType
      return (
        <CheckBox
          value={Boolean(value)}
          checkName={fieldSchema.check_name}
          handleInputChange={(newValue) => handleInputChange(key, newValue)}
        />
      );
    } else if (fieldSchema.immutable !== undefined || Array.isArray(value)) {
      // ListType
      return renderListField(key, Array.isArray(value) ? value : []);
    } else if (typeof value === 'number') {
      // IntType or FloatType
      return (
        <NumberInput
          value={value}
          prefix={fieldSchema.prefix}
          suffix={fieldSchema.suffix}
          handleInputChange={(newValue) => handleInputChange(key, newValue)}
        />
      );
    } else {
      // StringType or fallback
      return (
        <TextInput
          value={String(value)}
          prefix={fieldSchema.prefix}
          suffix={fieldSchema.suffix}
          handleInputChange={(newValue) => handleInputChange(key, newValue)}
        />
      );
    }
  };

  const renderColorField = (key: string, value: string) => {
    return <ColorSelect value={value} handleInputChange={(newValue) => handleInputChange(key, newValue)} />;
  };

  const renderListField = (key: string, value: PossibleConfigValue[]) => {
    const defaultValue = value.length > 0 ? value[0] : '';
    const baseConfig = getBaseConfig(key);
    return (
      <ListDisplay
        defaultValue={defaultValue}
        immutable={baseConfig.immutable}
        onAdd={(value) => handleAddItem(key, value)}
        onRemove={(index) => handleRemoveItem(key, index)}
      >
        {value.map((item, index) => renderInputField(`${key}[${index}]`, item))}
      </ListDisplay>
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
        // biome-ignore lint/suspicious/noExplicitAny: config is special, we can have many types here
      }, {} as any);
    }
    console.log('Unknown type');
    return null;
  };

  const handleRemoveItem = (key: string, index: number) => {
    setConfigData((prevData) => {
      const updatedArray = Array.isArray(prevData[key])
        ? // biome-ignore lint/suspicious/noExplicitAny: config is special, we can have many types here
          prevData[key].filter((_: any, i: number) => i !== index)
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
            type='button'
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
