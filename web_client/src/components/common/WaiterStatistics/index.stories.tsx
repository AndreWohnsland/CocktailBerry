import type { Meta, StoryObj } from '@storybook/react-vite';
import type { WaiterLogEntry } from '../../../types/models';
import WaiterStatistics from '.';

const meta: Meta<typeof WaiterStatistics> = {
  title: 'Elements/WaiterStatistics',
  component: WaiterStatistics,
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
type Story = StoryObj<typeof WaiterStatistics>;

const multiWaiterMultiDateLogs: WaiterLogEntry[] = [
  // Alice - 2026-02-28
  {
    id: 1,
    timestamp: '2026-02-28 18:05',
    waiter_name: 'Alice',
    recipe_name: 'Cuba Libre',
    volume: 300,
    is_virgin: false,
  },
  {
    id: 2,
    timestamp: '2026-02-28 18:22',
    waiter_name: 'Alice',
    recipe_name: 'Tequila Sunrise',
    volume: 250,
    is_virgin: false,
  },
  {
    id: 3,
    timestamp: '2026-02-28 19:10',
    waiter_name: 'Alice',
    recipe_name: 'Cuba Libre',
    volume: 300,
    is_virgin: true,
  },
  // Alice - 2026-03-01
  { id: 4, timestamp: '2026-03-01 20:00', waiter_name: 'Alice', recipe_name: 'Mojito', volume: 350, is_virgin: false },
  {
    id: 5,
    timestamp: '2026-03-01 20:45',
    waiter_name: 'Alice',
    recipe_name: 'Piña Colada',
    volume: 400,
    is_virgin: false,
  },
  // Bob - 2026-02-28
  { id: 6, timestamp: '2026-02-28 18:30', waiter_name: 'Bob', recipe_name: 'Mojito', volume: 350, is_virgin: false },
  { id: 7, timestamp: '2026-02-28 19:00', waiter_name: 'Bob', recipe_name: 'Mojito', volume: 350, is_virgin: true },
  // Bob - 2026-03-01
  {
    id: 8,
    timestamp: '2026-03-01 20:15',
    waiter_name: 'Bob',
    recipe_name: 'Cuba Libre',
    volume: 300,
    is_virgin: false,
  },
  {
    id: 9,
    timestamp: '2026-03-01 20:30',
    waiter_name: 'Bob',
    recipe_name: 'Tequila Sunrise',
    volume: 250,
    is_virgin: false,
  },
  {
    id: 10,
    timestamp: '2026-03-01 21:00',
    waiter_name: 'Bob',
    recipe_name: 'Piña Colada',
    volume: 400,
    is_virgin: false,
  },
  { id: 11, timestamp: '2026-03-01 21:20', waiter_name: 'Bob', recipe_name: 'Mojito', volume: 350, is_virgin: true },
  // Charlie - 2026-03-01
  {
    id: 12,
    timestamp: '2026-03-01 20:10',
    waiter_name: 'Charlie',
    recipe_name: 'Cuba Libre',
    volume: 300,
    is_virgin: false,
  },
];

export const MultiWaiterMultiDate: Story = {
  args: {
    logs: multiWaiterMultiDateLogs,
  },
};

const singleWaiterLogs: WaiterLogEntry[] = [
  {
    id: 1,
    timestamp: '2026-03-01 19:00',
    waiter_name: 'Alice',
    recipe_name: 'Cuba Libre',
    volume: 300,
    is_virgin: false,
  },
  { id: 2, timestamp: '2026-03-01 19:15', waiter_name: 'Alice', recipe_name: 'Mojito', volume: 350, is_virgin: true },
  {
    id: 3,
    timestamp: '2026-03-01 19:40',
    waiter_name: 'Alice',
    recipe_name: 'Tequila Sunrise',
    volume: 250,
    is_virgin: false,
  },
];

export const SingleWaiter: Story = {
  args: {
    logs: singleWaiterLogs,
  },
};

export const Empty: Story = {
  args: {
    logs: [],
  },
};
