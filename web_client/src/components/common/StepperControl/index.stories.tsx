import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';

import StepperControl from '.';

const meta: Meta<typeof StepperControl> = {
  title: 'Input/StepperControl',
  component: StepperControl,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof StepperControl>;

export const Default: Story = {
  args: {
    value: 50,
    onIncrement: fn(),
    onDecrement: fn(),
  },
};

export const WithUnit: Story = {
  args: {
    value: 100,
    unit: 'ml',
    onIncrement: fn(),
    onDecrement: fn(),
  },
};

export const SmallSize: Story = {
  args: {
    value: 3,
    size: 'sm',
    onIncrement: fn(),
    onDecrement: fn(),
  },
};

export const LargeSize: Story = {
  args: {
    value: 250,
    unit: 'ml',
    size: 'lg',
    onIncrement: fn(),
    onDecrement: fn(),
  },
};
