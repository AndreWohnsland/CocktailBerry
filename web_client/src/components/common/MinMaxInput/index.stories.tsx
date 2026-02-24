import { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';

import MinMaxInput from '.';

const meta: Meta<typeof MinMaxInput> = {
  title: 'Input/MinMaxInput',
  component: MinMaxInput,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: 400 }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof MinMaxInput>;

export const Default: Story = {
  args: {
    max: 500,
    delta: 50,
  },
  render: (args) => {
    const [value, setValue] = useState(250);
    return <MinMaxInput {...args} value={value} onChange={setValue} />;
  },
};

export const SmallDelta: Story = {
  args: {
    max: 100,
    delta: 10,
  },
  render: (args) => {
    const [value, setValue] = useState(50);
    return <MinMaxInput {...args} value={value} onChange={setValue} />;
  },
};

export const CustomMin: Story = {
  args: {
    min: 100,
    max: 1000,
    delta: 100,
  },
  render: (args) => {
    const [value, setValue] = useState(500);
    return <MinMaxInput {...args} value={value} onChange={setValue} />;
  },
};
