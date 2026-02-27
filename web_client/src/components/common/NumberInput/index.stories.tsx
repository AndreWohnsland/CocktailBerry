import type { Meta, StoryObj } from '@storybook/react-vite';

import NumberInput from '.';

const meta: Meta<typeof NumberInput> = {
  title: 'Input/NumberInput',
  component: NumberInput,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
  args: {
    value: 0,
    prefix: '',
    suffix: '',
    handleInputChange: (value) => console.log(value),
  },
};

export default meta;
type Story = StoryObj<typeof NumberInput>;

export const Default: Story = {
  args: {
    value: 0,
    handleInputChange: () => {},
    prefix: '',
    suffix: '',
  },
};

export const WithPrefixAndSuffix: Story = {
  args: {
    value: 1233,
    prefix: '$',
    suffix: 'USD',
    handleInputChange: () => {},
  },
};

export const WithPrefix: Story = {
  args: {
    value: 1233,
    prefix: 'Amount:',
    handleInputChange: () => {},
  },
};

export const WithSuffix: Story = {
  args: {
    value: 1233,
    suffix: 'ml',
    handleInputChange: () => {},
  },
};

export const Large: Story = {
  args: {
    value: 500,
    large: true,
    handleInputChange: () => {},
  },
};

export const FillParent: Story = {
  args: {
    value: 250,
    fillParent: true,
    readOnly: true,
    className: 'h-full',
  },
  decorators: [
    (Story) => (
      <div style={{ width: 300, height: 100, border: '4px dashed gray' }}>
        <Story />
      </div>
    ),
  ],
};
