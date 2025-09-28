import type { Meta, StoryObj } from '@storybook/react-vite';

import { fn } from 'storybook/test';

import { FaPlus } from 'react-icons/fa6';
import { IoHandLeft } from 'react-icons/io5';
import Button from '.';

const meta = {
  title: 'Common/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    style: {
      control: {
        type: 'select',
        options: ['primary', 'secondary', 'neutral'],
      },
    },
    textSize: { control: { type: 'select', options: ['sm', 'md', 'lg'] } },
    icon: {
      control: { type: 'select' },
      options: ['None', 'HandLeft', 'FaPlus'],
      mapping: {
        None: undefined,
        HandLeft: IoHandLeft,
        FaPlus: FaPlus,
      },
    },
  },
  args: { onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    style: 'primary',
    label: 'Button',
  },
};

export const PrimaryWithIcon: Story = {
  args: {
    style: 'primary',
    label: 'Button',
    icon: IoHandLeft,
  },
};

export const PrimaryFilled: Story = {
  args: {
    style: 'primary',
    filled: true,
    label: 'Button',
  },
};

export const PrimaryFilledWithIcon: Story = {
  args: {
    style: 'primary',
    filled: true,
    label: 'Button',
    icon: IoHandLeft,
  },
};

export const Secondary: Story = {
  args: {
    style: 'secondary',
    label: 'Button',
  },
};

export const SecondaryFilled: Story = {
  args: {
    style: 'secondary',
    filled: true,
    label: 'Button',
  },
};

export const Neutral: Story = {
  args: {
    style: 'neutral',
    label: 'Button',
  },
};

export const NeutralFilled: Story = {
  args: {
    style: 'neutral',
    filled: true,
    label: 'Button',
  },
};

export const Large: Story = {
  args: {
    textSize: 'lg',
    label: 'Button',
  },
};

export const Medium: Story = {
  args: {
    textSize: 'md',
    label: 'Button',
  },
};

export const Small: Story = {
  args: {
    textSize: 'sm',
    label: 'Button',
  },
};
