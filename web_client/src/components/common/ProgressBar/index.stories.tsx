import type { Meta, StoryObj } from '@storybook/react-vite';
import ProgressBar from '.';

const meta: Meta<typeof ProgressBar> = {
  title: 'Elements/ProgressBar',
  component: ProgressBar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    fillPercent: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
      description: 'Percentage (0-100) of the bar to fill',
    },
  },
  args: {
    fillPercent: 50,
    className: 'w-80 h-10',
  },
};

export default meta;

type Story = StoryObj<typeof ProgressBar>;

export const Default: Story = {
  args: {
    fillPercent: 50,
  },
};

export const SmallHeight: Story = {
  args: {
    className: 'w-80 h-6',
  },
};

export const LargeHeight: Story = {
  args: {
    className: 'w-80 h-20',
  },
};

export const FillValues: Story = {
  render: () => (
    <div className='space-y-1'>
      {[0, 5, 10, 25, 50, 75, 90, 100].map((p) => (
        <div key={p} className='flex items-center space-x-4'>
          <div className='w-80 h-12'>
            <ProgressBar fillPercent={p} className='w-full h-full' />
          </div>
          <span className='text-sm'>{p}%</span>
        </div>
      ))}
    </div>
  ),
  args: { ...meta.args },
};
