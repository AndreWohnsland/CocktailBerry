import type React from 'react';
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import defaultColor from '../../../defaults/defaultColor';
import Metric from '../Metric';
import TextHeader from '../TextHeader';

export interface ResourceStatsChartProps {
  title: string;
  min: number;
  max: number;
  mean: number;
  raw: number[];
  unit?: string;
  threshold?: number;}

const MAX_POINTS = 100;

// Helper to read themed color from CSS variables with fallback
const getThemeColor = (key: string, fallback: string) => {
  if (globalThis.window === undefined || document === undefined) return fallback;
  const cssVar = getComputedStyle(document.documentElement).getPropertyValue(`--${key}-color`);
  return cssVar?.trim() || fallback;
};

// Aggregate raw data into at most maxPoints using averaging bins
const aggregateData = (raw: number[], maxPoints: number): number[] => {
  if (!raw) return [];
  if (raw.length <= maxPoints) return raw;
  const binSize = Math.ceil(raw.length / maxPoints);
  const result: number[] = [];
  for (let i = 0; i < raw.length; i += binSize) {
    const bin = raw.slice(i, i + binSize);
    if (bin.length === 0) continue;
    const avg = bin.reduce((sum, v) => sum + v, 0) / bin.length;
    result.push(avg);
  }
  return result;
};

const ResourceStatsChart: React.FC<ResourceStatsChartProps> = ({
  title,
  min,
  max,
  mean,
  raw,
  unit = '%',
  threshold = 90,
}) => {
  const primaryColor = getThemeColor('primary', defaultColor.primary);
  const secondaryColor = getThemeColor('secondary', defaultColor.secondary);
  const chartData = aggregateData(raw, MAX_POINTS).map((value, index) => ({ index, value }));
  return (
    <div className='mb-6 w-full'>
      <TextHeader text={title} subheader />
      <div className='grid grid-cols-3 gap-2'>
        <Metric name='Min' value={min} unit={unit} threshold={threshold} />
        <Metric name='Max' value={max} unit={unit} threshold={threshold} />
        <Metric name='Mean' value={mean} unit={unit} threshold={threshold} />
      </div>
      {raw.length > 0 && (
        <div className='w-full h-64 mt-6 mb-2'>
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <XAxis dataKey='index' hide />
              <YAxis
                domain={['auto', 'auto']}
                tickFormatter={(val: number) => `${val.toFixed(0)}${unit}`}
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

export default ResourceStatsChart;
