import type { Preview, Decorator } from '@storybook/react-vite';

// Import global Tailwind + custom styles so Storybook stories have the same styling
// as the main application. Without this, utility classes & the custom .button-* classes
// defined via @apply in src/index.css will not be present.
import '../src/index.css';
// Apply background/text color overrides for Storybook Docs pages so they
// use the same Tailwind-driven CSS variables as the app.
import './docs.css';

// Available themes from themes.css
const themes = ['default', 'berry', 'bavaria', 'alien', 'tropical', 'purple', 'custom'];

// Decorator to apply theme classes to the document
const withTheme: Decorator = (Story, context) => {
  const theme = context.globals.theme || 'default';

  // Apply theme class to both html and body, matching the app behavior
  document.documentElement.className = theme;
  document.body.className = theme;

  return Story();
};

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

  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Global theme for components',
      defaultValue: 'default',
      toolbar: {
        icon: 'paintbrush',
        items: themes.map((theme) => ({
          value: theme,
          title: theme.charAt(0).toUpperCase() + theme.slice(1),
        })),
        showName: true,
        dynamicTitle: true,
      },
    },
  },

  decorators: [withTheme],
};

export default preview;
