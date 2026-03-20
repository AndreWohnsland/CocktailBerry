import type { Meta, StoryObj } from '@storybook/react-vite';
import React from 'react';
import type { CurrentWaiterState } from '../../../types/models';
import WaiterDisplay from '.';

const meta = {
  title: 'Elements/WaiterDisplay',
  component: WaiterDisplay,
  decorators: [
    (Story) =>
      React.createElement(
        'div',
        {
          style: {
            width: 250,
            display: 'inline-block',
          },
        },
        Story(),
      ),
  ],
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    waiter: {
      control: { type: 'object' },
    },
    initialOpen: {
      control: { type: 'boolean' },
    },
  },
} satisfies Meta<typeof WaiterDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

const registeredWaiter: CurrentWaiterState = {
  nfc_id: 'ABC123',
  waiter: {
    nfc_id: 'ABC123',
    name: 'Alice',
    permissions: { maker: true, ingredients: false, recipes: false, bottles: false, options: false },
  },
};

const unregisteredWaiter: CurrentWaiterState = {
  nfc_id: 'XYZ789',
  waiter: null,
};

export const RegisteredWaiter: Story = {
  args: {
    waiter: registeredWaiter,
  },
};

export const RegisteredWaiterExpanded: Story = {
  args: {
    waiter: registeredWaiter,
    initialOpen: true,
  },
};

export const UnregisteredWaiter: Story = {
  args: {
    waiter: unregisteredWaiter,
  },
};

export const NoWaiter: Story = {
  args: {
    waiter: null,
  },
};
