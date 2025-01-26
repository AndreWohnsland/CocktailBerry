import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
