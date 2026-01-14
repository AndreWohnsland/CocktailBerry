import type { Meta, StoryObj } from '@storybook/react-vite';
import NumberInput from '../NumberInput';
import ListDisplay from '.';

const meta: Meta<typeof ListDisplay> = {
  title: 'Elements/ListDisplay',
  component: ListDisplay,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    defaultValue: { control: 'text' },
    children: { control: false },
  },
  args: {
    immutable: false,
    defaultValue: '',
    onAdd: (value) => console.log('Add', value),
    onRemove: (index) => console.log('Remove', index),
  },
};

export default meta;
type Story = StoryObj<typeof ListDisplay>;

export const Default: Story = {
  args: {
    children: [
      <NumberInput key={1} value={123} handleInputChange={(value) => console.log(value)} suffix='ml' />,
      <NumberInput key={2} value={456} handleInputChange={(value) => console.log(value)} suffix='ml' />,
    ],
    immutable: false,
    defaultValue: '',
    onAdd: (value) => console.log('Add', value),
    onRemove: (index) => console.log('Remove', index),
  },
};

export const Immutable: Story = {
  args: {
    children: [
      <NumberInput key={1} value={123} handleInputChange={(value) => console.log(value)} suffix='ml' />,
      <NumberInput key={2} value={456} handleInputChange={(value) => console.log(value)} suffix='ml' />,
    ],
    immutable: true,
    defaultValue: '',
    onAdd: (value) => console.log('Add', value),
    onRemove: (index) => console.log('Remove', index),
  },
};

export const WithManyItems: Story = {
  args: {
    children: Array.from({ length: 10 }, (_, i) => (
      // biome-ignore lint/suspicious/noArrayIndexKey: Testing
      <NumberInput key={i} value={i * 100} handleInputChange={(value) => console.log(value)} suffix='ml' />
    )),
    immutable: false,
    defaultValue: '',
    onAdd: (value) => console.log('Add', value),
    onRemove: (index) => console.log('Remove', index),
  },
};
