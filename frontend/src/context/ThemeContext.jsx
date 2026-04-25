import { createContext, useContext } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  // Dark mode only - no theme switching available
  const value = {
    theme: 'dark',
    effectiveTheme: 'dark'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
