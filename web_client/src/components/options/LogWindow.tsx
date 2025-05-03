import React, { useEffect, useState } from 'react';
import { useLogs } from '../../api/options';
import ErrorComponent from '../common/ErrorComponent';
import { JumpToTopButton } from '../common/JumpToTopButton';
import LoadingData from '../common/LoadingData';

const LogWindow: React.FC = () => {
  const { data, isLoading, error } = useLogs();
  const [selectedLogType, setSelectedLogType] = useState<string>('INFO');

  const handleLogTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLogType(event.target.value);
  };

  useEffect(() => {
    if (data?.data) {
      const logTypes = Object.keys(data.data);
      if (logTypes.includes('production_logs.log')) {
        setSelectedLogType('production_logs.log');
      } else {
        setSelectedLogType(logTypes[0]);
      }
    }
  }, [data]);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const setStyle = (log: string): string => {
    let style = 'px-1 break-all';
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

  const logData = data?.data;

  return (
    <div className='flex flex-col w-full max-w-7xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <h2 className='text-2xl font-bold text-secondary mr-4'>Logs:</h2>
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
      <div className='flex-grow p-2'>
        {logData?.[selectedLogType]?.map((log: string, index: number) => (
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
