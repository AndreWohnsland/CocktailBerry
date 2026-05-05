import type React from 'react';
import { useWaiterLogs } from '../../../api/waiters';
import ErrorComponent from '../../common/ErrorComponent';
import LoadingData from '../../common/LoadingData';
import WaiterStatistics from '../../common/WaiterStatistics';

const StatisticsTab: React.FC = () => {
  const { data: logs, isLoading, error } = useWaiterLogs();

  if (isLoading)
    return (
      <div className='flex justify-center w-full'>
        <LoadingData />
      </div>
    );
  if (error) return <ErrorComponent text={error.message} />;

  return <WaiterStatistics logs={logs ?? []} />;
};

export default StatisticsTab;
