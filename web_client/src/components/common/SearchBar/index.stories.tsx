import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';

import SearchBar from '.';

const meta = {
  title: 'Common/SearchBar',
  component: SearchBar,
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    search: { control: 'text' },
    setSearch: { action: 'setSearch' },
    afterInput: { control: 'object' },
    initiallyOpen: { control: 'boolean' },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof SearchBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultInitialClosed: Story = {
  args: { search: '', setSearch: () => {}, afterInput: undefined, initiallyOpen: false },
  render: (args) => {
    return (
      <div className='w-[420px]'>
        <SearchBar search={args.search} setSearch={args.setSearch} initiallyOpen={args.initiallyOpen} />
      </div>
    );
  },
};

export const InitiallyOpen: Story = {
  args: { search: '', setSearch: () => {}, afterInput: undefined, initiallyOpen: true },
  render: (args) => {
    const [search, setSearch] = useState<string | null>('');
    return (
      <div className='w-[420px]'>
        <SearchBar search={search} setSearch={setSearch} initiallyOpen={args.initiallyOpen} />
      </div>
    );
  },
};

export const WithInitialSearch: Story = {
  args: { search: 'mojito', setSearch: () => {}, afterInput: undefined, initiallyOpen: true },
  render: (args) => {
    const [search, setSearch] = useState<string | null>('mojito');
    return (
      <div className='w-[420px]'>
        <SearchBar search={search} setSearch={setSearch} initiallyOpen={args.initiallyOpen} />
      </div>
    );
  },
};

export const WithAfterInput: Story = {
  args: { search: '', setSearch: () => {}, afterInput: undefined, initiallyOpen: true },
  render: (args) => {
    const [search, setSearch] = useState<string | null>('');
    return (
      <div className='w-[520px]'>
        <SearchBar
          search={search}
          setSearch={setSearch}
          afterInput={<button className='button-secondary p-2'>Filter</button>}
          initiallyOpen={args.initiallyOpen}
        />
      </div>
    );
  },
};
