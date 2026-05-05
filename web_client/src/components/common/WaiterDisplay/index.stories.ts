import type { Meta, StoryObj } from '@storybook/react-vite';
import React from 'react';
import type { CurrentWaiterState, OptionTiles, Role } from '../../../types/models';
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

const allTilesAllowed: OptionTiles = {
  cleaning: false,
  configuration: false,
  calibration: false,
  scale_calibration: false,
  backup: false,
  restore: false,
  data: false,
  logs: false,
  wifi: false,
  addons: false,
  internet_check: false,
  update_system: false,
  update_software: false,
  system_resource_usage: false,
  about: false,
  news: false,
  sumup: false,
  waiters: false,
  events: false,
  reboot: false,
  shutdown: false,
  rfid: false,
  adjust_time: false,
  issues: false,
  recipe_calculation: false,
};

const makerRole: Role = {
  id: 1,
  name: 'Maker',
  permissions: { maker: true, ingredients: false, recipes: false, bottles: false, options: false },
  tile_permissions: allTilesAllowed,
};

const registeredWaiter: CurrentWaiterState = {
  nfc_id: 'ABC123',
  waiter: {
    nfc_id: 'ABC123',
    name: 'Alice',
    role_id: makerRole.id,
    role: makerRole,
    permissions: makerRole.permissions,
    tile_permissions: makerRole.tile_permissions,
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
