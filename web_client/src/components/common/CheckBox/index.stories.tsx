import type { Meta, StoryObj } from '@storybook/react-vite';

import CheckBox from '.';

const meta: Meta<typeof CheckBox> = {
  title: 'Input/CheckBox',
  component: CheckBox,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
  args: {
    value: false,
    checkName: 'Check me',
    handleInputChange: (value) => console.log(value),
  },
};

export default meta;

type Story = StoryObj<typeof CheckBox>;

export const Default: Story = {
  args: {
    value: false,
    checkName: 'Check me',
    handleInputChange: () => {},
  },
};

export const Checked: Story = {
  args: {
    value: true,
    checkName: 'Already checked',
    handleInputChange: () => {},
  },
};
