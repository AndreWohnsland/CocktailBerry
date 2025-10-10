import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { IconType } from 'react-icons';
import { FaCocktail, FaUndo } from 'react-icons/fa';
import { FaCoins, FaLemon } from 'react-icons/fa6';
import { resetDataInsights, useConsumeData } from '../../api/options';
import { confirmAndExecute } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';

const ConsumeBarChart: React.FC<{
  title: string;
  data: Record<string, number>;
  unit?: string;
  icon?: IconType;
}> = ({ title, data, unit, icon }) => {
  const sortedEntries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const maxValue = Math.max(...Object.values(data));
  const sumValues = Object.values(data).reduce((acc, curr) => acc + curr, 0);
  const displayUnit = unit ?? '';

  return (
    <div className='mb-6 w-full'>
      <TextHeader text={`${title} (${sumValues}${displayUnit})`} icon={icon} space={4} />
      <div className='space-y-2'>
        {sortedEntries.map(([key, value]) => (
          <div
            key={key}
            className={
              'border-2 border-neutral bg-neutral text-background font-bold rounded-full text-center overflow-hidden flex items-center justify-center'
            }
            style={{ position: 'relative', zIndex: 1 }}
          >
            <div
              className='bg-primary rounded-full'
              style={{ width: `${(value / maxValue) * 100}%`, height: '100%', position: 'absolute', left: 0, top: 0 }}
            ></div>
            <span style={{ position: 'relative', zIndex: 2 }}>{`${key} (${value}${displayUnit})`}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const ConsumeWindow: React.FC = () => {
  const { data, isLoading, error, refetch } = useConsumeData();
  const [selectedDataType, setSelectedDataType] = useState<string>('AT RESET');
  const { t } = useTranslation();

  useEffect(() => {
    if (data) {
      setSelectedDataType('AT RESET');
    }
  }, [data]);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const handleDataTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDataType(event.target.value);
  };

  const resetData = () => {
    confirmAndExecute(t('data.resetTheData'), resetDataInsights).then((success) => {
      if (success) {
        refetch();
        setSelectedDataType('AT RESET');
      }
    });
  };

  const createSelectionUserText = (value: string) => {
    if (value === 'AT RESET') {
      return t('data.atReset');
    } else if (value === 'ALL') {
      return t('data.allTime');
    } else if (/^\d{8}$/.test(value)) {
      // Format YYYYMMDD to YYYY.MM.DD
      const year = value.slice(0, 4);
      const month = value.slice(4, 6);
      const day = value.slice(6, 8);
      return t('data.dateFormat', { year, month, day });
    } else {
      return value;
    }
  };

  const consumeData = data?.data;

  if (!consumeData) {
    return <div>{t('data.noData')}</div>;
  }

  const selectedData = consumeData[selectedDataType];

  return (
    <div className='flex flex-col w-full max-w-5xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0 mb-2'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <p className='text-2xl font-bold text-secondary mr-4 text-center'>{t('data.data')}:</p>
          <select value={selectedDataType} onChange={handleDataTypeChange} className='select-base'>
            {consumeData &&
              Object.keys(consumeData).map((dataType) => (
                <option key={dataType} value={dataType}>
                  {createSelectionUserText(dataType)}
                </option>
              ))}
          </select>
        </div>
      </div>

      <div className='flex-grow p-2 items-center justify-center flex flex-col w-full'>
        {consumeData && (
          <>
            <ConsumeBarChart title={t('data.recipes')} data={selectedData.recipes} unit='x' icon={FaCocktail} />
            <ConsumeBarChart title={t('data.ingredients')} data={selectedData.ingredients} icon={FaLemon} />
            {selectedData.cost && <ConsumeBarChart title={t('data.cost')} data={selectedData.cost} icon={FaCoins} />}
            {consumeData['AT RESET'].recipes && Object.keys(consumeData['AT RESET'].recipes).length > 0 && (
              <button
                className='button-danger p-2 w-full flex items-center justify-center max-w-lg'
                onClick={resetData}
              >
                <FaUndo className='mr-4' size={20} />
                {t('data.reset')}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ConsumeWindow;
