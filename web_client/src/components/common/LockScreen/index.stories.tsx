import type { Meta, StoryObj } from '@storybook/react-vite';
import LockScreen from '.';

const meta: Meta<typeof LockScreen> = {
  title: 'Feedback/LockScreen',
  component: LockScreen,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Custom title to display. Falls back to default translation if not provided.',
    },
    message: {
      control: 'text',
      description: 'Message to display below the title.',
    },
  },
  args: {},
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    message: 'This area is currently locked.',
  },
};

export const WithCustomTitle: Story = {
  args: {
    title: 'Payment Required',
    message: 'Please complete the payment to continue.',
  },
};

export const AccessRestricted: Story = {
  args: {
    title: 'Access Restricted',
    message: 'You do not have permission to view this content.',
  },
};

export const Maintenance: Story = {
  args: {
    title: 'Under Maintenance',
    message: 'This feature is currently unavailable. Please try again later.',
  },
};
