import React, { useEffect, useState } from 'react';
import { useLogs } from '../../api/options';
import { JumpToTopButton } from '../common/JumpToTopButton';

const LogWindow: React.FC = () => {
  const { data, isLoading, isError } = useLogs();
  const [selectedLogType, setSelectedLogType] = useState<string>('INFO');

  const handleLogTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLogType(event.target.value);
  };

  useEffect(() => {
    if (data) {
      setSelectedLogType(Object.keys(data.data)[0]);
    }
  }, [data]);

  const setStyle = (log: string): string => {
    let style = 'px-1';
    if (selectedLogType === 'debuglog.log') {
      return style + ' mb-6';
    }
    if (log.toLowerCase().includes('warning')) {
      style = style + ' text-danger';
    } else if (log.toLowerCase().includes('error')) {
      style = style + ' text-background bg-danger rounded-sm my-1';
    }
    return style;
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return <div>Error loading logs</div>;
  }

  const logData = data?.data;

  return (
    <div className='flex flex-col w-full max-w-7xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0'>
        <div className='flex flex-row items-center'>
          <h2 className='text-2xl font-bold text-secondary mr-4'>Log Data:</h2>
          <select value={selectedLogType} onChange={handleLogTypeChange} className='mt-2 p-2 select-base'>
            {logData &&
              Object.keys(logData).map((logType) => (
                <option key={logType} value={logType}>
                  {logType}
                </option>
              ))}
          </select>
        </div>
      </div>
      <div className='flex-grow p-4'>
        {logData &&
          logData[selectedLogType]?.map((log: string, index: number) => (
            <div key={index} className={setStyle(log)}>
              {log}
            </div>
          ))}
      </div>
      <JumpToTopButton />
    </div>
  );
};

export default LogWindow;
