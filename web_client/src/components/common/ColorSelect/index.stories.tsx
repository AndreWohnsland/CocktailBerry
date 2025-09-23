import type { Meta, StoryObj } from '@storybook/react-vite';

import ColorSelect from '.';

const meta: Meta<typeof ColorSelect> = {
  title: 'Input/ColorSelect',
  component: ColorSelect,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: 'color',
    },
  },
  args: {
    value: '#000000',
    handleInputChange: (value) => console.log(value),
  },
};

export default meta;
type Story = StoryObj<typeof ColorSelect>;

export const Default: Story = {
  args: {
    value: '#000000',
    handleInputChange: () => {},
  },
};

export const WithDifferentColor: Story = {
  args: {
    value: '#ff5733',
    handleInputChange: () => {},
  },
};
