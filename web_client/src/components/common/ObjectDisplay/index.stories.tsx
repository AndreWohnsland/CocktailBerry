import type { Meta, StoryObj } from '@storybook/react-vite';
import CheckBox from '../CheckBox';
import NumberInput from '../NumberInput';
import TextInput from '../TextInput';
import ObjectDisplay from '.';

const meta: Meta<typeof ObjectDisplay> = {
  title: 'Elements/ObjectDisplay',
  component: ObjectDisplay,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    children: { control: false },
  },
};

export default meta;
type Story = StoryObj<typeof ObjectDisplay>;

const noop = () => {};

export const TwoItems: Story = {
  args: {
    children: [
      <NumberInput key='pin' value={14} handleInputChange={noop} suffix='pin' />,
      <NumberInput key='volume' value={250} handleInputChange={noop} suffix='ml' />,
    ],
  },
};

export const ThreeItems: Story = {
  args: {
    children: [
      <TextInput key='name' value='Pump 1' handleInputChange={noop} />,
      <NumberInput key='pin' value={14} handleInputChange={noop} suffix='pin' />,
      <NumberInput key='volume' value={250} handleInputChange={noop} suffix='ml' />,
    ],
  },
};

export const FourItems: Story = {
  args: {
    children: [
      <TextInput key='name' value='Pump 1' handleInputChange={noop} />,
      <NumberInput key='pin' value={14} handleInputChange={noop} suffix='pin' />,
      <NumberInput key='volume' value={250} handleInputChange={noop} suffix='ml' />,
      <CheckBox key='enabled' value={true} checkName='on' handleInputChange={noop} />,
    ],
  },
};

export const FiveItems: Story = {
  args: {
    children: [
      <TextInput key='name' value='Pump 1' handleInputChange={noop} />,
      <NumberInput key='pin' value={14} handleInputChange={noop} suffix='pin' />,
      <NumberInput key='volume' value={250} handleInputChange={noop} suffix='ml' />,
      <NumberInput key='speed' value={100} handleInputChange={noop} suffix='%' />,
      <CheckBox key='enabled' value={true} checkName='on' handleInputChange={noop} />,
    ],
  },
};

export const SevenItems: Story = {
  args: {
    children: [
      <TextInput key='name' value='Pump 1' handleInputChange={noop} />,
      <NumberInput key='pin' value={14} handleInputChange={noop} suffix='pin' />,
      <NumberInput key='volume' value={250} handleInputChange={noop} suffix='ml' />,
      <NumberInput key='speed' value={100} handleInputChange={noop} suffix='%' />,
      <NumberInput key='delay' value={50} handleInputChange={noop} suffix='ms' />,
      <TextInput key='type' value='peristaltic' handleInputChange={noop} />,
      <CheckBox key='enabled' value={true} checkName='on' handleInputChange={noop} />,
    ],
  },
};
