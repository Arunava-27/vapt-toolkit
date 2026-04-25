import { useTheme } from '../context/ThemeContext';
import './ThemeToggleButton.css';

export default function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();

  const getIcon = () => {
    if (theme === 'light') return '☀️';
    if (theme === 'dark') return '🌙';
    return '🔄';
  };

  const getLabel = () => {
    if (theme === 'light') return 'Light';
    if (theme === 'dark') return 'Dark';
    return 'Auto';
  };

  return (
    <button
      className="theme-toggle-btn"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'Dark' : theme === 'dark' ? 'Auto' : 'Light'} theme`}
      aria-label={`Theme: ${getLabel()}. Click to toggle`}
    >
      <span className="theme-icon">{getIcon()}</span>
      <span className="theme-label">{getLabel()}</span>
    </button>
  );
}
