import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';

import ModalActions from '.';

const meta: Meta<typeof ModalActions> = {
  title: 'Elements/ModalActions',
  component: ModalActions,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ display: 'flex', justifyContent: 'space-between', width: 500 }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof ModalActions>;

export const EditExisting: Story = {
  args: {
    isNew: false,
    onDelete: fn(),
    onSave: fn(),
    deleteLabel: 'Delete',
    saveLabel: 'Apply',
    createLabel: 'Create',
  },
};

export const CreateNew: Story = {
  args: {
    isNew: true,
    deleteDisabled: true,
    onDelete: fn(),
    onSave: fn(),
    deleteLabel: 'Delete',
    saveLabel: 'Apply',
    createLabel: 'Create',
  },
};

export const SaveDisabled: Story = {
  args: {
    isNew: false,
    saveDisabled: true,
    onDelete: fn(),
    onSave: fn(),
    deleteLabel: 'Delete',
    saveLabel: 'Apply',
    createLabel: 'Create',
  },
};

export const BothDisabled: Story = {
  args: {
    isNew: true,
    deleteDisabled: true,
    saveDisabled: true,
    onDelete: fn(),
    onSave: fn(),
    deleteLabel: 'Delete',
    saveLabel: 'Apply',
    createLabel: 'Create',
  },
};
