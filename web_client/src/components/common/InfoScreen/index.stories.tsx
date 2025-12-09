import type { Meta, StoryObj } from '@storybook/react-vite';
import { FaCog, FaExclamationTriangle, FaSpinner } from 'react-icons/fa';
import { MdLock } from 'react-icons/md';
import InfoScreen from '.';
import Button from '../Button';

const meta: Meta<typeof InfoScreen> = {
  title: 'Feedback/InfoScreen',
  component: InfoScreen,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    icon: {
      control: false,
      description: 'Icon element to display at the top.',
    },
    title: {
      control: 'text',
      description: 'Main title text (required).',
    },
    description: {
      control: 'text',
      description: 'Optional description text displayed below the title.',
    },
    hint: {
      control: 'text',
      description: 'Optional hint text displayed below the description in neutral color.',
    },
    button: {
      control: false,
      description: 'Optional button element to display at the bottom.',
    },
  },
  args: {
    title: 'Info Screen Title',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    icon: <FaCog className='text-neutral' size={100} />,
    title: 'Info Screen Title',
    description: 'This is a description text.',
    hint: 'This is a hint text.',
  },
};

export const TitleOnly: Story = {
  args: {
    icon: <FaSpinner className='animate-spin text-neutral' size={100} />,
    title: 'Loading...',
  },
};

export const WithDescription: Story = {
  args: {
    icon: <MdLock className='text-primary' size={100} />,
    title: 'Area Locked',
    description: 'This area is currently restricted.',
  },
};

export const WithHint: Story = {
  args: {
    icon: <FaExclamationTriangle className='text-danger' size={100} />,
    title: 'Error',
    description: 'Something went wrong.',
    hint: 'If this persists, please contact support.',
  },
};

export const WithButton: Story = {
  args: {
    icon: <FaExclamationTriangle className='text-danger' size={100} />,
    title: 'Connection Lost',
    description: 'Unable to connect to the server.',
    hint: 'Check your network connection.',
    button: <Button label='Retry' onClick={() => alert('Retry clicked!')} />,
  },
};

export const LoadingExample: Story = {
  args: {
    icon: <FaSpinner className='animate-spin text-neutral' size={100} />,
    title: 'Loading Data',
    description: 'Please wait while we fetch your data.',
  },
};

export const ErrorExample: Story = {
  args: {
    icon: <FaExclamationTriangle className='text-danger' size={100} />,
    title: 'Error',
    description: 'Could not load data.',
    hint: 'If this persists, please check your connection.',
  },
};

export const LockScreenExample: Story = {
  args: {
    icon: <MdLock className='text-primary' size={100} />,
    title: 'Access Restricted',
    description: 'You need to authenticate to access this area.',
  },
};

export const ConfigurationExample: Story = {
  args: {
    icon: <FaCog className='animate-spin text-neutral' size={100} />,
    title: 'Getting Configuration',
    description: 'Fetching your settings from the server.',
    hint: 'If this persists, please check your connection.',
  },
};
