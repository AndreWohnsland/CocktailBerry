import type React from 'react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { useResourceInfo, useResourceStats } from '../../api/options';
import defaultColor from '../../defaults/defaultColor';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import TextHeader from '../common/TextHeader';

interface StatsProps {
  title: string;
  min: number;
  max: number;
  mean: number;
  median: number;
  raw: number[];
}

const MAX_POINTS = 100;

const getThemeColor = (key: string, fallback: string) => {
  const cssVar = getComputedStyle(document.documentElement).getPropertyValue(`--${key}-color`);
  return cssVar?.trim() || fallback;
};

const aggregateData = (raw: number[], maxPoints: number): number[] => {
  if (raw.length <= maxPoints) return raw;
  const binSize = Math.ceil(raw.length / maxPoints);
  const result: number[] = [];
  for (let i = 0; i < raw.length; i += binSize) {
    const bin = raw.slice(i, i + binSize);
    const avg = bin.reduce((sum, v) => sum + v, 0) / bin.length;
    result.push(avg);
  }
  return result;
};

const chipStyle = (value: number) => {
  const baseClass = 'border-2 text-background font-semibold rounded-lg text-center p-2 flex flex-col';
  if (value <= 90) return `${baseClass} border-neutral bg-neutral`;
  return `${baseClass} border-danger bg-danger`;
};

const ResourceStatsChart: React.FC<StatsProps> = ({ title, min, max, mean, median, raw }) => {
  const fmt = (val: number) => `${val.toFixed(1)}%`;
  const primaryColor = getThemeColor('primary', defaultColor.primary);
  const secondaryColor = getThemeColor('secondary', defaultColor.secondary);
  const chartData = aggregateData(raw, MAX_POINTS).map((value, index) => ({ index, value }));
  return (
    <div className='mb-6 w-full'>
      <TextHeader text={title} subheader />
      <div className='grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-2'>
        <div className={chipStyle(min)}>
          <span className='capitalize text-s opacity-80'>Min</span>
          <span className='text-xl font-bold'>{fmt(min)}</span>
        </div>
        <div className={chipStyle(max)}>
          <span className='capitalize text-s opacity-80'>Max</span>
          <span className='text-xl font-bold'>{fmt(max)}</span>
        </div>
        <div className={chipStyle(mean)}>
          <span className='capitalize text-s opacity-80'>Mean</span>
          <span className='text-xl font-bold'>{fmt(mean)}</span>
        </div>
        <div className={chipStyle(median)}>
          <span className='capitalize text-s opacity-80'>Median</span>
          <span className='text-xl font-bold'>{fmt(median)}</span>
        </div>
      </div>
      {raw.length > 0 && (
        <div className='w-full h-64 mt-6 mb-2'>
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <XAxis dataKey='index' hide />
              <YAxis
                domain={['auto', 'auto']}
                tickFormatter={(val: number) => `${val.toFixed(0)}%`}
                stroke={secondaryColor}
                strokeWidth={3}
              />
              <Line type='monotone' dataKey='value' stroke={primaryColor} dot={false} strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

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
