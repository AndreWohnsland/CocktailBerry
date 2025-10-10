import type { Meta, StoryObj } from '@storybook/react-vite';
import Metric, { MetricProps } from '.';

const meta: Meta<typeof Metric> = {
  title: 'Elements/Metric',
  component: Metric,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    name: { control: 'text' },
    value: { control: { type: 'number' } },
    unit: { control: 'text' },
    fractionDigits: { control: { type: 'number', min: 0, max: 6, step: 1 } },
    threshold: { control: { type: 'number', min: 0, max: 10000, step: 1 } },
  },
  args: {
    name: 'Value',
    value: 42.123,
    unit: '%',
    threshold: Number.POSITIVE_INFINITY,
  } satisfies Partial<MetricProps>,
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const OverHundred: Story = { args: { value: 123.456 } };
export const CustomFractionDigits: Story = { args: { value: 9.87654, fractionDigits: 3 } };
export const ThousandSeparator: Story = { args: { value: 12345.678, unit: 'ms', threshold: 15000 } };
export const NoUnit: Story = { args: { value: 77.7, unit: '' } };
export const DangerThreshold: Story = { args: { value: 95, threshold: 90 } };
export const BelowThreshold: Story = { args: { value: 65, threshold: 90 } };
export const ShowcaseGrid: Story = {
  render: () => (
    <div className='grid grid-cols-2 gap-3 min-w-[500px]'>
      <Metric name='Small' value={4.2} unit='%' />
      <Metric name='Medium' value={42.2} unit='%' />
      <Metric name='LargeInt' value={420} unit='%' />
      <Metric name='Thousands' value={4200.55} unit='%' />
      <Metric name='NoUnit' value={3.14} unit='' />
      <Metric name='Danger' value={97} unit='%' threshold={90} />
    </div>
  ),
};
