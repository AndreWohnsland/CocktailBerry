/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
export default defineConfig({
  plugins: [react(), tailwindcss()],
});
// export default defineConfig(({ mode }) => {
//   if (mode === 'demo') {
//     return {
//       plugins: [react()],
//       base: '/CocktailBerry/',
//     };
//   }
//   return { plugins: [react()] };
// });
