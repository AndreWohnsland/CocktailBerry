import React from 'react';

export interface MetricProps {
  name: string;
  value: number;
  unit?: string;
  fractionDigits?: number;
  threshold?: number;
}

const chipStyle = (value: number, threshold: number) => {
  const color = value <= threshold ? 'neutral' : 'danger';
  return `border-2 text-background font-semibold rounded-lg text-center p-2 flex flex-col border-${color} bg-${color}`;
};

const resolveFractionDigits = (value: number, fractionDigits?: number) => {
  if (fractionDigits !== undefined) return fractionDigits;
  return value >= 100 ? 0 : 1;
};

const formatMetricValue = (value: number, unit = '', fractionDigits?: number) => {
  const fd = resolveFractionDigits(value, fractionDigits);
  return `${value.toLocaleString(undefined, { minimumFractionDigits: fd, maximumFractionDigits: fd })}${unit}`;
};

const Metric: React.FC<MetricProps> = ({
  name,
  value,
  unit = '',
  fractionDigits,
  threshold = Number.POSITIVE_INFINITY,
}) => {
  return (
    <div className={chipStyle(value, threshold)}>
      <span className='capitalize text-s opacity-80'>{name}</span>
      <span className='text-xl font-bold'>{formatMetricValue(value, unit, fractionDigits)}</span>
    </div>
  );
};

export default Metric;
