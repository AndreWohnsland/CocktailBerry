import type { Meta, StoryObj } from '@storybook/react-vite';

import { fn } from 'storybook/test';

import TabSelector from '.';

const meta = {
  title: 'Elements/TabSelector',
  component: TabSelector,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    tabs: { control: 'object' },
    selectedTab: { control: 'text' },
    className: { control: 'text' },
  },
  args: { onSelectTab: fn() },
} satisfies Meta<typeof TabSelector>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    tabs: ['UI', 'MAKER', 'HARDWARE', 'SOFTWARE', 'PAYMENT', 'OTHER'],
    selectedTab: 'UI',
  },
};

export const WithSelectedTab: Story = {
  args: {
    tabs: ['UI', 'MAKER', 'HARDWARE', 'SOFTWARE', 'PAYMENT', 'OTHER'],
    selectedTab: 'HARDWARE',
  },
};

export const SubTabs: Story = {
  args: {
    tabs: ['CocktailBerry', 'SumUp'],
    selectedTab: 'CocktailBerry',
  },
};

export const WithCustomClass: Story = {
  args: {
    tabs: ['Tab A', 'Tab B', 'Tab C'],
    selectedTab: 'Tab A',
    className: 'bg-background',
  },
};
