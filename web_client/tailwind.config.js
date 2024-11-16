/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary-color)',
        secondary: 'var(--secondary-color)',
        neutral: 'var(--neutral-color)',
        background: 'var(--background-color)',
        danger: 'var(--danger-color)',
        text: 'var(--text-color)',
      },
    },
  },
  plugins: [],
};
