import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';
import { FaCheck, FaTrashAlt } from 'react-icons/fa';

import ItemCard from '.';
import Button from '../Button';

const meta: Meta<typeof ItemCard> = {
  title: 'Elements/ItemCard',
  component: ItemCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: 500 }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof ItemCard>;

export const Default: Story = {
  args: {
    title: 'My Addon',
    description: 'An addon that does something useful.',
    actions: <Button style='danger' filled icon={FaTrashAlt} label='Delete' onClick={fn()} className='px-4' />,
  },
};

export const Highlighted: Story = {
  args: {
    title: 'Active Reader',
    subtitle: 'Currently in use',
    highlighted: true,
    actions: <Button style='danger' filled icon={FaTrashAlt} label='Delete' onClick={fn()} className='px-4' />,
  },
};

export const WithMultipleActions: Story = {
  args: {
    title: 'SumUp Reader',
    actions: (
      <>
        <Button filled icon={FaCheck} label='Use' onClick={fn()} className='px-4' />
        <Button style='danger' filled icon={FaTrashAlt} label='Delete' onClick={fn()} className='px-4' />
      </>
    ),
  },
};

export const WithChildren: Story = {
  args: {
    title: 'Complex Addon',
    subtitle: 'v1.2.0',
    description: 'This addon has additional content below.',
  },
  render: (args) => (
    <ItemCard {...args}>
      <div className='mt-4'>
        <Button filled label='Update to v1.3.0' className='w-full' onClick={fn()} />
      </div>
    </ItemCard>
  ),
};

export const TitleOnly: Story = {
  args: {
    title: 'Simple Item',
  },
};
