import type { Meta, StoryObj } from '@storybook/react-vite';
import { fn } from 'storybook/test';

import HandAddMeasure from '.';

// NOTE: the Finish button is intentionally NOT part of this component — in the app it is
// rendered by the surrounding ProgressModal's bottom button slot. These stories exercise the
// measuring rows (scale sim) and the manual check rows; `onFinish` (a fn() spy here) fires via
// auto-finish once every row is resolved — measure the ml rows and tap the check on the manual
// rows to see it trigger.

/**
 * Simulates a scale: each `read` adds a few grams so the progress bar visibly fills,
 * and `tare` resets to zero. Lets reviewers exercise the full measure interaction in
 * Storybook without real hardware.
 */
const makeScaleSim = (stepGrams = 4) => {
  let grams = 0;
  return {
    tare: async () => {
      grams = 0;
    },
    read: async () => {
      grams += stepGrams;
      return grams;
    },
  };
};

const meta: Meta<typeof HandAddMeasure> = {
  title: 'Cocktail/HandAddMeasure',
  component: HandAddMeasure,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: 480, height: 360 }} className='border-2 border-neutral rounded-lg p-4 bg-background'>
        <Story />
      </div>
    ),
  ],
  args: {
    onFinish: fn(),
    pollIntervalMs: 200,
  },
};

export default meta;
type Story = StoryObj<typeof HandAddMeasure>;

export const TwoMeasurable: Story = {
  args: {
    handAdds: [
      { name: 'Lime Juice', amount: 10, unit: 'ml', measurable: true },
      { name: 'Sugar Syrup', amount: 20, unit: 'ml', measurable: true },
    ],
    ...makeScaleSim(),
  },
};

export const WithTextOnlyAdds: Story = {
  args: {
    handAdds: [
      { name: 'Lime Juice', amount: 10, unit: 'ml', measurable: true },
      { name: 'Sirup', amount: 10, unit: 'ml', measurable: true },
      { name: 'Mint', amount: 6, unit: 'pieces', measurable: false },
      { name: 'Bitters', amount: 3, unit: 'dash', measurable: false },
    ],
    ...makeScaleSim(),
  },
};

export const ManualOnly: Story = {
  args: {
    handAdds: [
      { name: 'Mint', amount: 6, unit: 'pieces', measurable: false },
      { name: 'Bitters', amount: 3, unit: 'dash', measurable: false },
    ],
  },
};
