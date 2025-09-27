import type { Meta, StoryObj } from '@storybook/react-vite';

import TextInput from '.';

const meta: Meta<typeof TextInput> = {
  title: 'Input/TextInput',
  component: TextInput,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
  args: {
    value: '',
    prefix: '',
    suffix: '',
    handleInputChange: (value) => console.log(value),
  },
};

export default meta;
type Story = StoryObj<typeof TextInput>;

export const Default: Story = {
  args: {
    value: '',
    prefix: '',
    suffix: '',
    handleInputChange: () => {},
  },
};

export const WithPlaceholder: Story = {
  args: {
    value: '',
    placeholder: 'Enter text here...',
    handleInputChange: () => {},
  },
};

export const WithPrefixAndSuffix: Story = {
  args: {
    value: 'Text with Prefix and Suffix',
    prefix: '$',
    suffix: 'USD',
    handleInputChange: () => {},
  },
};

export const WithPrefix: Story = {
  args: {
    value: 'Text with Prefix',
    prefix: '@',
    handleInputChange: () => {},
  },
};

export const WithSuffix: Story = {
  args: {
    value: 'Text with Suffix',
    suffix: '.com',
    handleInputChange: () => {},
  },
};

export const PasswordInput: Story = {
  args: {
    value: 'Password',
    type: 'password',
    handleInputChange: () => {},
  },
};
