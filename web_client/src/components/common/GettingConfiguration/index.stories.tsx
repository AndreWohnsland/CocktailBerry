import type { Meta, StoryObj } from '@storybook/react-vite';
import GettingConfiguration from '.';

const meta: Meta<typeof GettingConfiguration> = {
  title: 'Feedback/GettingConfiguration',
  component: GettingConfiguration,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
  args: {},
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};
