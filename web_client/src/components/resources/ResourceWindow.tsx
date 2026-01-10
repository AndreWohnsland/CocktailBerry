import type React from 'react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useResourceInfo, useResourceStats } from '../../api/options';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import ResourceStatsChart from '../common/ResourceStatsChart';

const ResourceWindow: React.FC = () => {
  const { data, isLoading, error } = useResourceInfo();
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats,
  } = useResourceStats(selectedSession ?? 0);
  const { t } = useTranslation();

  useEffect(() => {
    if (data && data.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedSession(data[0].session_id);
    }
  }, [data]);

  useEffect(() => {
    if (selectedSession !== null) {
      refetchStats();
    }
  }, [selectedSession, refetchStats]);

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const handleSessionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSession(Number(event.target.value));
  };

  if (!data || data.length === 0) {
    return <div>{t('data.noData')}</div>;
  }

  return (
    <div className='flex flex-col w-full max-w-5xl'>
      <div className='flex flex-col items-center justify-center flex-shrink-0 mb-4'>
        <div className='flex flex-row items-center w-full max-w-lg px-2'>
          <p className='text-2xl font-bold text-secondary mr-4 text-center'>{t('resources.startTime')}:</p>
          <select value={selectedSession ?? ''} onChange={handleSessionChange} className='select-base'>
            {data.map((session: { session_id: number; start_time: string }) => (
              <option key={session.session_id} value={session.session_id}>
                {session.start_time} ({session.session_id})
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className='flex-grow p-2 items-center justify-center flex flex-col w-full'>
        {statsLoading && <LoadingData />}
        {statsError && <ErrorComponent text={statsError.message} />}
        {stats && (
          <>
            <ResourceStatsChart
              title={t('resources.ramMetrics')}
              min={stats.min_ram}
              max={stats.max_ram}
              mean={stats.mean_ram}
              median={stats.median_ram}
              raw={stats.raw_ram}
            />
            <ResourceStatsChart
              title={t('resources.cpuMetrics')}
              min={stats.min_cpu}
              max={stats.max_cpu}
              mean={stats.mean_cpu}
              median={stats.median_cpu}
              raw={stats.raw_cpu}
            />
          </>
        )}
      </div>
    </div>
  );
};

export default ResourceWindow;
