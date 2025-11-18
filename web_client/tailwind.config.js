/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  safelist: [
    {
      pattern: /^(bg|text|border|ring|shadow)-(primary|secondary|neutral|background|danger)$/,
    },
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary-color)',
        secondary: 'var(--secondary-color)',
        neutral: 'var(--neutral-color)',
        background: 'var(--background-color)',
        danger: 'var(--danger-color)',
      },
      screens: {
        'h-xs': { raw: '(min-height: 400px)' },
        'h-sm': { raw: '(min-height: 640px)' },
        'h-md': { raw: '(min-height: 768px)' },
        'h-lg': { raw: '(min-height: 1024px)' },
      },
    },
  },
  plugins: [],
};
