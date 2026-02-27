import type { Meta, StoryObj } from '@storybook/react-vite';

import { fn } from 'storybook/test';

import { FaPlus } from 'react-icons/fa6';
import { IoHandLeft } from 'react-icons/io5';
import TileButton from '.';

const meta = {
  title: 'Elements/TileButton',
  component: TileButton,
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
    // Expose icon selection via Storybook's mapping feature. The arg value (string) is mapped to
    // the actual IconType component before being passed to the story render function.
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
} satisfies Meta<typeof TileButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    style: 'primary',
    label: 'TileButton',
  },
};

export const PrimaryWithIcon: Story = {
  args: {
    style: 'primary',
    label: 'TileButton',
    icon: IoHandLeft,
  },
};

export const PrimaryFilled: Story = {
  args: {
    style: 'primary',
    filled: true,
    label: 'TileButton',
  },
};

export const Secondary: Story = {
  args: {
    style: 'secondary',
    label: 'TileButton',
  },
};

export const SecondaryFilled: Story = {
  args: {
    style: 'secondary',
    filled: true,
    label: 'TileButton',
  },
};

export const Neutral: Story = {
  args: {
    style: 'neutral',
    label: 'TileButton',
  },
};

export const NeutralFilled: Story = {
  args: {
    style: 'neutral',
    filled: true,
    label: 'TileButton',
  },
};

export const Large: Story = {
  args: {
    textSize: 'lg',
    label: 'TileButton',
  },
};

export const Medium: Story = {
  args: {
    textSize: 'md',
    label: 'TileButton',
  },
};

export const Small: Story = {
  args: {
    textSize: 'sm',
    label: 'TileButton',
  },
};

export const Passive: Story = {
  args: {
    label: 'Passive TileButton',
    passive: true,
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled TileButton',
    disabled: true,
    filled: true,
  },
};
