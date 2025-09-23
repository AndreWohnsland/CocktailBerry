import type { Meta, StoryObj } from '@storybook/react-vite';

import DropDown from '.';

const meta: Meta<typeof DropDown> = {
  title: 'Input/DropDown',
  component: DropDown,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  args: {
    value: '',
    allowedValues: ['Option 1', 'Option 2', 'Option 3'],
    handleInputChange: (value) => console.log(value),
  },
};

export default meta;
type Story = StoryObj<typeof DropDown>;

export const Default: Story = {
  args: {
    value: 'Option 1',
    allowedValues: ['Option 1', 'Option 2', 'Option 3'],
    handleInputChange: () => {},
  },
};

export const EmptyOptions: Story = {
  args: {
    value: '',
    allowedValues: [],
    handleInputChange: () => {},
  },
};

export const SingleOption: Story = {
  args: {
    value: 'Only Option',
    allowedValues: ['Only Option'],
    handleInputChange: () => {},
  },
};
