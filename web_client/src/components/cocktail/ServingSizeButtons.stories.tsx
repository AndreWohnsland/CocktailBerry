import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';

import ServingSizeButtons from './ServingSizeButtons';

const meta: Meta<typeof ServingSizeButtons> = {
  title: 'Elements/ServingSizeButtons',
  component: ServingSizeButtons,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: 500 }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof ServingSizeButtons>;

export const Default: Story = {
  args: {
    servingSizes: [200, 250, 300],
    onSelect: fn(),
  },
};

export const WithPriceLabel: Story = {
  args: {
    servingSizes: [200, 250, 300],
    onSelect: fn(),
    getLabel: (amount: number) => `${amount}: ${(amount * 0.05).toFixed(1)}€`,
  },
};

export const SingleSize: Story = {
  args: {
    servingSizes: [250],
    onSelect: fn(),
  },
};

export const Disabled: Story = {
  args: {
    servingSizes: [200, 250, 300],
    onSelect: fn(),
    disabled: true,
  },
};
