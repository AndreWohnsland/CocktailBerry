import type { Meta, StoryObj } from '@storybook/react-vite';
import ErrorComponent from '.';

const meta: Meta<typeof ErrorComponent> = {
  title: 'Feedback/ErrorComponent',
  component: ErrorComponent,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    text: {
      control: 'text',
      description: 'Custom error message to display. Falls back to default translation if not provided.',
    },
  },
  args: {},
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const WithCustomText: Story = {
  args: {
    text: 'Something went wrong while loading your data.',
  },
};

export const NetworkError: Story = {
  args: {
    text: 'Network error: Unable to connect to the server.',
  },
};

export const NotFoundError: Story = {
  args: {
    text: 'Resource not found: The requested item does not exist.',
  },
};

export const TimeoutError: Story = {
  args: {
    text: 'Request timed out. Please try again later.',
  },
};

export const PermissionError: Story = {
  args: {
    text: 'Permission denied: You do not have access to this resource.',
  },
};
