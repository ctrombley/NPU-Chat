import { useState, useEffect } from 'react';

const THEMES = ['theme-dark', 'theme-light', 'theme-solarized'] as const;
export type Theme = typeof THEMES[number];

const STORAGE_KEY = 'npu-theme';
const DEFAULT_THEME: Theme = 'theme-dark';

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return (THEMES as readonly string[]).includes(stored ?? '') ? (stored as Theme) : DEFAULT_THEME;
  });

  useEffect(() => {
    const root = document.documentElement;
    THEMES.forEach(t => root.classList.remove(t));
    root.classList.add(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  return [theme, setThemeState];
}
