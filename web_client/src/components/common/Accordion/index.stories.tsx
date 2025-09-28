import type { Meta, StoryObj } from '@storybook/react-vite';

import Accordion from '.';

const meta: Meta<typeof Accordion> = {
  title: 'Common/Accordion',
  component: Accordion,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    children: { control: 'text' },
  },
  args: {
    title: 'Accordion Title',
    children: 'This is the accordion content. You can place any React nodes here.',
  },
};

export default meta;
type Story = StoryObj<typeof Accordion>;

export const Default: Story = {
  args: {
    title: 'Accordion Title',
    children: 'This is the accordion content. You can place any React nodes here.',
  },
};

export const LongContent: Story = {
  args: {
    title: 'Accordion With Long Content',
    children:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. ' +
      'Cras elementum ultrices diam. Maecenas ligula massa, varius a, semper congue, euismod non, mi.',
  },
};

export const CustomTitleNode: Story = {
  args: {
    title: (
      <span>
        <strong>Custom</strong> Title Node
      </span>
    ),
    children: 'The title prop accepts any React node, allowing custom markup.',
  },
};

export const MultipleAccordions: Story = {
  render: () => (
    <div className='w-80 space-y-2'>
      <Accordion title='First Section'>First section content</Accordion>
      <Accordion title='Second Section'>Second section content</Accordion>
      <Accordion title='Third Section'>Third section content</Accordion>
    </div>
  ),
  args: { ...meta.args },
};
