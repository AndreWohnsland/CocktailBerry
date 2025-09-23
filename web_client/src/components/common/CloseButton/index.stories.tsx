import type { Meta, StoryObj } from '@storybook/react-vite';

import CloseButton from '.';

const meta: Meta<typeof CloseButton> = {
  title: 'Elements/CloseButton',
  component: CloseButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  args: {
    onClick: () => console.log('Close button clicked'),
    iconSize: 30,
  },
};

export default meta;

type Story = StoryObj<typeof CloseButton>;

export const Default: Story = {
  args: {
    onClick: () => alert('Close button clicked'),
  },
};
