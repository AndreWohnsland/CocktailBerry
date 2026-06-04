import type { Meta, StoryObj } from '@storybook/react-vite';
import PaymentWaiting from '.';

const meta: Meta<typeof PaymentWaiting> = {
  title: 'Payment/PaymentWaiting',
  component: PaymentWaiting,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      // fixed-size flex box so the component's `grow` fills it like inside ProgressModal
      <div style={{ width: 480, height: 360 }} className='flex border-2 border-neutral rounded-lg p-4 bg-background'>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
