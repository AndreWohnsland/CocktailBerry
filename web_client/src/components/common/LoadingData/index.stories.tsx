import type { Meta, StoryObj } from '@storybook/react-vite';
import LoadingData from '.';

const meta: Meta<typeof LoadingData> = {
  title: 'Feedback/LoadingData',
  component: LoadingData,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    showDescription: {
      control: 'boolean',
      description: 'Whether to show the description text below the loading message.',
    },
  },
  args: {
    showDescription: true,
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    showDescription: true,
  },
};

export const WithoutDescription: Story = {
  args: {
    showDescription: false,
  },
};
