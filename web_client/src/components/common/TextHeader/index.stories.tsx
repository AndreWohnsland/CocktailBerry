import type { Meta, StoryObj } from '@storybook/react-vite';

import { FaCocktail } from 'react-icons/fa';
import { FaLemon } from 'react-icons/fa6';
import TextHeader from '.';

const meta = {
  title: 'Common/TextHeader',
  component: TextHeader,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    icon: {
      control: { type: 'select' },
      options: ['None', 'FaLemon', 'FaCocktail'],
      mapping: {
        None: undefined,
        FaLemon: FaLemon,
        FaCocktail: FaCocktail,
      },
    },
  },
  args: {
    text: 'Header Text',
    subheader: false,
    icon: FaCocktail,
    space: 0,
  },
} satisfies Meta<typeof TextHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const HeaderDefault: Story = {
  args: {
    text: 'Header With Logo',
    subheader: false,
  },
};

export const HeaderNoIcon: Story = {
  args: {
    text: 'Header No Logo',
    subheader: false,
    icon: undefined,
  },
};

export const HeaderDefaultSpacing: Story = {
  args: {
    text: 'Header With Default Spacing',
    subheader: false,
    space: undefined,
  },

  render: (args) => (
    <div>
      <TextHeader {...args} />
      <p>This paragraph is below the header with custom spacing.</p>
    </div>
  ),
};

export const Subheader: Story = {
  args: {
    text: 'Subheader With Logo',
    subheader: true,
  },
};

export const SubheaderDefaultSpacing: Story = {
  args: {
    text: 'Subheader With Default Spacing',
    subheader: true,
    space: undefined,
  },

  render: (args) => (
    <div>
      <TextHeader {...args} />
      <p>This paragraph is below the header with custom spacing.</p>
    </div>
  ),
};
