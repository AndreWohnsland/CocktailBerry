import type React from 'react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLog } from '../../api/options';
import type { LogKey, LogLevel } from '../../types/models';
import DropDown from '../common/DropDown';
import ErrorComponent from '../common/ErrorComponent';
import { JumpToTopButton } from '../common/JumpToTopButton';
import LoadingData from '../common/LoadingData';

const lineStyle = (line: string, logKey: LogKey): string => {
  const base = 'px-1 break-all';
  if (logKey === 'debug') return `${base} mb-6`;
  if (line.startsWith('WARNING')) return `${base} text-danger`;
  if (line.startsWith('ERROR') || line.startsWith('CRITICAL'))
    return `${base} text-on-danger bg-danger rounded-sm my-1`;
  return base;
};

const LogWindow: React.FC = () => {
  const { t } = useTranslation();
  const [logKey, setLogKey] = useState<LogKey>('production');
  const [minLevel, setMinLevel] = useState<LogLevel>('DEBUG');
  const { data, isLoading, error } = useLog(logKey, minLevel);

  const logOptions: Record<LogKey, string> = {
    production: t('options.logFileProduction'),
    service: t('options.logFileService'),
    debug: t('options.logFileDebug'),
    resources: t('options.logFileResources'),
  };
  const levelOptions: Record<LogLevel, string> = {
    DEBUG: t('options.logLevelAll'),
    INFO: t('options.logLevelInfo'),
    WARNING: t('options.logLevelWarning'),
    ERROR: t('options.logLevelError'),
  };

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  return (
    <div className='flex grow flex-col w-full max-w-7xl'>
      <div className='flex flex-col items-center justify-center shrink-0 mb-2'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <p className='text-2xl font-bold text-secondary mr-4'>{t('options.logs')}:</p>
          <DropDown
            value={logKey}
            allowedValues={logOptions}
            handleInputChange={(value) => setLogKey(value as LogKey)}
            className='mt-2 p-2'
          />
          {logKey !== 'debug' && (
            <DropDown
              value={minLevel}
              allowedValues={levelOptions}
              handleInputChange={(value) => setMinLevel(value as LogLevel)}
              className='mt-2 ml-2 p-2'
            />
          )}
        </div>
      </div>
      <div className='grow p-2 flex flex-col justify-center'>
        {data?.map((line, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: ordered from backend
          <div key={index} className={lineStyle(line, logKey)}>
            {line}
          </div>
        ))}
      </div>
      <JumpToTopButton />
    </div>
  );
};

export default LogWindow;
