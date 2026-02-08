import type { Meta, StoryObj } from '@storybook/react-vite';
import ResourceStatsChart, { type ResourceStatsChartProps } from '.';

const baseRaw = Array.from({ length: 100 }, (_, i) => 40 + Math.sin(i / 5) * 10 + (i % 7));

const meta: Meta<typeof ResourceStatsChart> = {
  title: 'Composite/ResourceStatsChart',
  component: ResourceStatsChart,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className='w-full min-w-[700px] max-w-5xl p-4 bg-background/40 rounded-lg shadow-md'>
        <Story />
      </div>
    ),
  ],
  argTypes: {
    unit: {
      control: { type: 'text' },
      description: 'Unit appended to values',
    },
    threshold: {
      control: { type: 'number', min: 0, max: 100, step: 1 },
      description: 'Chip danger threshold',
    },
    raw: {
      control: false,
      table: {
        type: { summary: 'number[]' },
        category: 'Data',
      },
      description: 'Raw metric samples (number[]) displayed as a line after aggregation.',
    },
  },
  args: {
    title: 'RAM Metrics',
    min: 42.1,
    max: 88.3,
    mean: 65.4,
    raw: baseRaw,
    unit: '%',
    threshold: 90,
  } satisfies Partial<ResourceStatsChartProps>,
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const CustomUnit: Story = {
  args: {
    title: 'Temperature Metrics',
    unit: '°C',
    min: 22.3,
    max: 61.2,
    mean: 41,
    raw: baseRaw.map((v) => (v / 100) * 60),
    threshold: 55,
  },
};

export const CustomThreshold: Story = {
  args: {
    threshold: 70,
    max: 92.4,
    mean: 71.5,
    raw: baseRaw.map((v) => v + 10),
  },
};

export const LargeDataset: Story = {
  args: {
    raw: Array.from({ length: 500 }, (_, i) => 50 + Math.sin(i / 15) * 20 + (i % 11)),
    min: 32.2,
    max: 98.7,
    mean: 67.8,
  },
};

export const EmptyData: Story = {
  args: {
    raw: [],
    min: 0,
    max: 0,
    mean: 0,
    title: 'No Data',
  },
};

export const LargeValues: Story = {
  args: {
    title: 'Throughput Metrics',
    unit: ' req/s',
    raw: Array.from({ length: 120 }, (_, i) => 800 + Math.sin(i / 6) * 300 + (i % 20) * 25),
    min: 820,
    max: 4250,
    mean: 2120,
    threshold: 3500,
  },
};
