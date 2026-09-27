/// <reference types="vitest/config" />
import { existsSync, readFileSync } from 'node:fs';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The demo workflow moves web_client to the repo root, so pyproject sits next to this file there.
const pyprojectPath = ['../pyproject.toml', './pyproject.toml'].find((p) => existsSync(p));
if (!pyprojectPath) throw new Error('pyproject.toml not found, cannot determine web client version');
const version = readFileSync(pyprojectPath, 'utf8').match(/^version = "(.*)"$/m)?.[1];
if (!version) throw new Error(`no version in ${pyprojectPath}`);

// Only a build of the release tag is the published bundle; everything else is marked.
const versionSuffix = (command: 'serve' | 'build') => {
  if (command === 'serve') return '-dev';
  if (process.env.GITHUB_REF_TYPE === 'tag') return '';
  return '-local';
};

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
export default defineConfig(({ command }) => {
  const suffix = versionSuffix(command);
  return {
    plugins: [react(), tailwindcss()],
    define: { __WEB_VERSION__: JSON.stringify(version + suffix) },
  };
});
