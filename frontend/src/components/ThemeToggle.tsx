import React from 'react';
import { Theme } from '../hooks/useTheme';

interface ThemeToggleProps {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
}

const SWATCHES: { theme: Theme; label: string; bg: string; ring: string }[] = [
  { theme: 'theme-dark',      label: 'Dark',       bg: 'bg-slate-800',  ring: 'ring-slate-400' },
  { theme: 'theme-light',     label: 'Light',      bg: 'bg-slate-100',  ring: 'ring-slate-400' },
  { theme: 'theme-solarized', label: 'Solarized',  bg: 'bg-teal-800',   ring: 'ring-teal-400' },
];

const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onThemeChange }) => (
  <div className="flex items-center justify-center gap-2 p-2.5 border-t border-theme-border">
    {SWATCHES.map(({ theme: t, label, bg, ring }) => (
      <button
        key={t}
        onClick={() => onThemeChange(t)}
        aria-label={`${label} theme`}
        title={`${label} theme`}
        className={`w-5 h-5 rounded-full ${bg} border border-theme-border transition-all ${
          theme === t ? `ring-2 ${ring} ring-offset-1 ring-offset-theme-sidebar` : 'opacity-60 hover:opacity-100'
        }`}
      />
    ))}
  </div>
);

export default ThemeToggle;
