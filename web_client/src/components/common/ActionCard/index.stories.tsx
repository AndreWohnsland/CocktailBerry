import type { Meta, StoryObj } from '@storybook/react-vite';

import ActionCard from '.';

const meta: Meta<typeof ActionCard> = {
  title: 'Elements/ActionCard',
  component: ActionCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {},
  args: {
    header: 'Action Card Header',
    sections: ['Section 1', 'Section 2'],
    actionText: 'Click Me',
    onActionClick: () => alert('Action Clicked'),
  },
};

export default meta;

type Story = StoryObj<typeof ActionCard>;

export const Default: Story = {
  args: {
    header: 'Action Card Header',
    sections: ['Section 1', 'Section 2'],
    actionText: 'Click Me',
    onActionClick: () => alert('Action Clicked'),
  },
};

export const WithoutAction: Story = {
  args: {
    header: 'Info Only',
    sections: ['This card has no action button.'],
    actionText: undefined,
    onActionClick: undefined,
  },
};

export const DangerAction: Story = {
  args: {
    header: 'Danger Action',
    sections: ['This action is dangerous.'],
    actionText: 'Delete',
    onActionClick: () => alert('Dangerous Action Clicked'),
    actionStyle: 'danger',
  },
};

export const MultipleSections: Story = {
  args: {
    header: 'Multiple Sections',
    sections: ['First section', 'Second section', 'Third section'],
    actionText: 'Proceed',
    onActionClick: () => alert('Proceed Clicked'),
  },
};

export const NoHeader: Story = {
  args: {
    header: undefined,
    sections: ['This card has no header.'],
    actionText: 'Click Me',
    onActionClick: () => alert('Action Clicked'),
  },
};

export const LongText: Story = {
  args: {
    header: 'Long Text Example',
    sections: [
      'This is a longer section of text to demonstrate how the ActionCard component handles more content. It should wrap properly and maintain readability across different screen sizes.',
      'Here is another paragraph to further illustrate the text handling capabilities of the component. The design should ensure that everything remains visually appealing and easy to read.',
    ],
    actionText: 'Learn More',
    onActionClick: () => alert('Learn More Clicked'),
  },
};
