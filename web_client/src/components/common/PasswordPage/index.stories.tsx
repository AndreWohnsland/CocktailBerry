import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';
import PasswordPage from '.';

const meta: Meta<typeof PasswordPage> = {
  title: 'Feedback/PasswordPage',
  component: PasswordPage,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    passwordName: {
      control: 'text',
      description: 'Name of the protected resource requiring password authentication.',
    },
    setAuthenticated: {
      description: 'Callback function called with the password when authentication succeeds.',
    },
    authMethod: {
      description: 'Async function to validate the password. Should return a promise.',
    },
  },
  args: {
    passwordName: 'Admin Panel',
    setAuthenticated: fn(),
    authMethod: fn().mockResolvedValue({ message: 'Authenticated successfully' }),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    passwordName: 'Admin Panel',
  },
};

export const MakerPassword: Story = {
  args: {
    passwordName: 'Maker Mode',
  },
};

export const SettingsPassword: Story = {
  args: {
    passwordName: 'Settings',
  },
};

export const CleaningPassword: Story = {
  args: {
    passwordName: 'Cleaning Mode',
  },
};

export const WithFailingAuth: Story = {
  args: {
    passwordName: 'Secure Area',
    authMethod: fn().mockRejectedValue(new Error('Invalid password')),
  },
};
