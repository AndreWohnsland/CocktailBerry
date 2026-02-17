import type React from 'react';
import { useEffect, useState } from 'react';
import { useLogs } from '../../api/options';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import { JumpToTopButton } from '../common/JumpToTopButton';
import LoadingData from '../common/LoadingData';

const LogWindow: React.FC = () => {
  const { data, isLoading, error } = useLogs();
  const [selectedLogType, setSelectedLogType] = useState<string>('INFO');

  const handleLogTypeChange = (value: string) => {
    setSelectedLogType(value);
  };

  useEffect(() => {
    if (data?.data) {
      const logTypes = Object.keys(data.data);
      if (logTypes.includes('production_logs.log')) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
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
      return `${style} mb-6`;
    }
    if (log.toLowerCase().includes('warning')) {
      style = `${style} text-danger`;
    } else if (log.toLowerCase().includes('error')) {
      style = `${style} text-background bg-danger rounded-sm my-1`;
    }
    return style;
  };

  const logData = data?.data;

  return (
    <div className='flex flex-col w-full max-w-7xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0 mb-2'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <p className='text-2xl font-bold text-secondary mr-4'>Logs:</p>
          <DropDown
            value={selectedLogType}
            allowedValues={logData ? Object.keys(logData) : []}
            handleInputChange={handleLogTypeChange}
            className='mt-2 p-2'
          />
        </div>
      </div>
      <div className='flex-grow p-2'>
        {logData?.[selectedLogType]?.map((log: string, index: number) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: ordered from backend
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
