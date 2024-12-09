import React, { useEffect, useState } from 'react';
import { useConsumeData } from '../../api/options';

const ConsumeBarChart: React.FC<{
  title: string;
  data: Record<string, number>;
  unit?: string;
}> = ({ title, data, unit }) => {
  const sortedEntries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const maxValue = Math.max(...Object.values(data));
  const sumValues = Object.values(data).reduce((acc, curr) => acc + curr, 0);
  const displayUnit = unit ? unit : '';

  return (
    <div className='mb-6'>
      <h3 className='text-2xl font-bold text-secondary mb-4 text-center'>{`${title} (${sumValues}${displayUnit})`}</h3>
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
  const { data, isLoading, isError } = useConsumeData();
  const [selectedDataType, setSelectedDataType] = useState<string>('AT RESET');

  const handleDataTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDataType(event.target.value);
  };

  useEffect(() => {
    if (data) {
      setSelectedDataType('AT RESET');
    }
  }, [data]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return <div>Error loading consumption data</div>;
  }

  const consumeData = data?.data;

  if (!consumeData) {
    return <div>No data</div>;
  }

  const selectedData = consumeData[selectedDataType];

  return (
    <div className='flex flex-col w-full max-w-5xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0'>
        <div className='flex flex-row items-center w-full px-2'>
          <h2 className='text-2xl font-bold text-secondary mr-4 text-center'>Data:</h2>
          <select value={selectedDataType} onChange={handleDataTypeChange} className='select-base'>
            {consumeData &&
              Object.keys(consumeData).map((dataType) => (
                <option key={dataType} value={dataType}>
                  {dataType}
                </option>
              ))}
          </select>
        </div>
      </div>

      <div className='flex-grow p-2'>
        {consumeData && (
          <>
            <ConsumeBarChart title='Recipes' data={selectedData.recipes} unit='x' />
            <ConsumeBarChart title='Ingredients' data={selectedData.ingredients} />
            {selectedData.cost && <ConsumeBarChart title='Cost' data={selectedData.cost} />}
          </>
        )}
      </div>
    </div>
  );
};

export default ConsumeWindow;
