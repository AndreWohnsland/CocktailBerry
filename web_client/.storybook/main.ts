import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: ['@chromatic-com/storybook', '@storybook/addon-docs', '@storybook/addon-a11y', '@storybook/addon-vitest'],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  typescript: {
    // react-docgen pulls in @babel/helper-compilation-targets which expects
    // lru-cache@^5 API. Yarn 1 hoists lru-cache@11 to the root and the nested
    // copy under react-docgen never gets the v5 build, so docgen crashes with
    // "_lruCache is not a constructor". Disabling docgen sidesteps the
    // dependency chain entirely; prop docs in MDX still work via explicit
    // ArgTypes definitions.
    reactDocgen: false,
  },
};
export default config;
