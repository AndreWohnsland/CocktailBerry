import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';
import HandAddAssistModal from './HandAddAssistModal';

const meta: Meta<typeof HandAddAssistModal> = {
  title: 'Cocktail/HandAddAssistModal',
  component: HandAddAssistModal,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  args: {
    isOpen: true,
    introMessage: 'Payment confirmed. Finish the remaining hand-adds.',
    onFinish: fn(),
    items: [
      {
        item_id: 'handadd-0',
        name: 'Lime Juice',
        display_amount: 10,
        display_unit: 'ml',
        measurable: true,
        target_weight_grams: 10,
      },
      {
        item_id: 'handadd-1',
        name: 'Mint Leaves',
        display_amount: 6,
        display_unit: 'leaves',
        measurable: false,
      },
    ],
  },
};

export default meta;
type Story = StoryObj<typeof HandAddAssistModal>;

export const Default: Story = {};
