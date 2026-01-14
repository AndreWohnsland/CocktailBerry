import type { Meta, StoryObj } from '@storybook/react-vite';
import React from 'react';

import UserDisplay from '.';
import type { PaymentUserData } from '../../../types/models';

const meta = {
  title: 'Elements/UserDisplay',
  component: UserDisplay,
  // Provide a small container so the component is shown in a compact box
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
    user: {
      control: { type: 'object' },
    },
  },
} satisfies Meta<typeof UserDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleUser: PaymentUserData = {
  nfc_id: '123456789',
  balance: 25.5,
  is_adult: true,
};

export const WithUser: Story = {
  args: {
    user: sampleUser,
  },
};

export const NoUser: Story = {
  args: {
    user: null,
  },
};
