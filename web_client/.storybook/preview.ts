import type { Preview } from '@storybook/react-vite';

// Import global Tailwind + custom styles so Storybook stories have the same styling
// as the main application. Without this, utility classes & the custom .button-* classes
// defined via @apply in src/index.css will not be present.
import '../src/index.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: 'todo',
    },
  },
};

export default preview;
