/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'bauhaus': ['Bauhaus', 'sans-serif'],
      },
      colors: {
        'chat-bg': 'rgb(var(--color-chat-bg) / <alpha-value>)',
        'sidebar-bg': 'rgb(var(--color-sidebar-bg) / <alpha-value>)',
        'message-sent': 'rgb(var(--color-message-sent) / <alpha-value>)',
        'message-received': 'rgb(var(--color-message-received) / <alpha-value>)',
        'accent': 'rgb(var(--color-accent) / <alpha-value>)',
        'accent-hover': 'rgb(var(--color-accent-hover) / <alpha-value>)',
        'tn': {
          'bg-dark': '#16161e',
          'bg': '#1a1b26',
          'bg-highlight': '#292e42',
          'border': '#414868',
          'fg': '#c0caf5',
          'fg-dark': '#a9b1d6',
          'comment': '#565f89',
          'blue': '#7aa2f7',
          'cyan': '#7dcfff',
          'green': '#9ece6a',
          'magenta': '#bb9af7',
          'red': '#f7768e',
          'yellow': '#e0af68',
          'orange': '#ff9e64',
          'selection': '#33467c',
        },
      },
      animation: {
        'pulse': 'pulse 1s',
        'spin': 'spin 0.8s linear infinite',
      },
    },
  },
  plugins: [],
}
