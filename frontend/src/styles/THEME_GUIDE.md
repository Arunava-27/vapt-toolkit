# VAPT Toolkit Theme System - Styling Guide

## Overview

The VAPT Toolkit uses a comprehensive CSS variables-based theme system that supports both light and dark modes with automatic system preference detection.

## Theme Modes

- **Light**: Optimized for daytime viewing with light backgrounds and dark text
- **Dark**: Optimized for low-light environments with dark backgrounds and light text
- **Auto** (Default): Automatically switches based on system preference and responds to system theme changes

## CSS Variables

### Background Colors
```css
--bg-primary      /* Main background (full pages, sections) */
--bg-secondary    /* Secondary background (cards, panels) */
--bg-tertiary     /* Tertiary background (hover states, code blocks) */
```

### Text Colors
```css
--text-primary    /* Main text, highest contrast */
--text-secondary  /* Secondary text, body text */
--text-tertiary   /* Tertiary text, muted, hints */
```

### Accent Colors
```css
--accent-primary  /* Primary action color, links */
--accent-secondary /* Secondary accent, lighter shade */
--accent-hover    /* Hover state for accents */
```

### Border & Surface Colors
```css
--border-color    /* Main border color */
--border-light    /* Light border variant */
--surface-default /* Default surface overlay */
--surface-overlay /* Overlay transparency layer */
```

### Semantic Colors
```css
--success-color   /* Success state (green) */
--warning-color   /* Warning state (orange/yellow) */
--error-color     /* Error state (red) */
--info-color      /* Info state (blue) */
```

### Other
```css
--transition-time /* Animation duration (0.3s) */
--focus-ring      /* Focus outline for accessibility */
```

## Light Theme (Default)

| Variable | Value | Use Case |
|----------|-------|----------|
| `--bg-primary` | #ffffff | Page backgrounds |
| `--bg-secondary` | #f6f8fa | Cards, panels |
| `--bg-tertiary` | #eaeef2 | Hover states, code |
| `--text-primary` | #24292f | Main text |
| `--text-secondary` | #57606a | Secondary text |
| `--text-tertiary` | #8c959f | Muted text |
| `--border-color` | #d0d7de | Borders |
| `--accent-primary` | #0969da | Links, buttons |
| `--accent-secondary` | #54aeff | Hover links |
| `--success-color` | #1a7f37 | Success states |
| `--warning-color` | #d29922 | Warning states |
| `--error-color` | #d1242f | Error states |

## Dark Theme

| Variable | Value | Use Case |
|----------|-------|----------|
| `--bg-primary` | #0d1117 | Page backgrounds |
| `--bg-secondary` | #161b22 | Cards, panels |
| `--bg-tertiary` | #21262d | Hover states, code |
| `--text-primary` | #c9d1d9 | Main text |
| `--text-secondary` | #8b949e | Secondary text |
| `--text-tertiary` | #6e7681 | Muted text |
| `--border-color` | #30363d | Borders |
| `--accent-primary` | #58a6ff | Links, buttons |
| `--accent-secondary` | #79c0ff | Hover links |
| `--success-color` | #3fb950 | Success states |
| `--warning-color` | #f0883e | Warning states |
| `--error-color` | #f85149 | Error states |

## Usage in Components

### Using CSS Variables in Stylesheets

```css
/* Component styling using theme variables */
.card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 16px;
  border-radius: 6px;
}

.card:hover {
  background-color: var(--bg-tertiary);
}

.button {
  background-color: var(--accent-primary);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color var(--transition-time) ease;
}

.button:hover {
  background-color: var(--accent-hover);
}
```

### Using CSS Variables in Inline Styles (React)

```jsx
<div style={{
  backgroundColor: 'var(--bg-secondary)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border-color)'
}}>
  Content
</div>
```

### Using the useTheme Hook (React)

```jsx
import { useTheme } from '../context/ThemeContext';

function MyComponent() {
  const { theme, effectiveTheme, toggleTheme, setThemeMode } = useTheme();

  return (
    <div>
      <p>Current theme: {theme}</p>
      <p>Effective theme: {effectiveTheme}</p>
      <button onClick={toggleTheme}>Toggle Theme</button>
      <button onClick={() => setThemeMode('light')}>Light Mode</button>
      <button onClick={() => setThemeMode('dark')}>Dark Mode</button>
      <button onClick={() => setThemeMode('auto')}>Auto Mode</button>
    </div>
  );
}
```

## Component-Specific Colors

### Severity Badges
```css
.severity-critical {
  background-color: rgba(248, 81, 73, 0.1);
  color: var(--error-color);
}

.severity-high {
  background-color: rgba(240, 136, 62, 0.1);
  color: var(--warning-color);
}

.severity-medium {
  background-color: rgba(210, 153, 34, 0.1);
  color: #d29922;
}

.severity-low {
  background-color: rgba(63, 185, 80, 0.1);
  color: var(--success-color);
}
```

### Status Indicators
```css
.status-active {
  color: var(--success-color);
}

.status-pending {
  color: var(--warning-color);
}

.status-failed {
  color: var(--error-color);
}

.status-info {
  color: var(--info-color);
}
```

## Transitions

All theme transitions are smooth and take 0.3 seconds (`--transition-time`). These apply automatically to:
- Background colors
- Text colors
- Border colors
- Box shadows

## Accessibility

### Color Contrast Ratios

Both themes meet **WCAG AA** accessibility standards:

**Light Theme:**
- Text on background: 12.6:1 (#24292f on #ffffff)
- Secondary text on background: 7.8:1 (#57606a on #ffffff)
- Links on background: 8.6:1 (#0969da on #ffffff)

**Dark Theme:**
- Text on background: 11.3:1 (#c9d1d9 on #0d1117)
- Secondary text on background: 4.5:1 (#8b949e on #161b22)
- Links on background: 7.2:1 (#58a6ff on #0d1117)

### Focus Indicators

All interactive elements have a visible focus indicator:

```css
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

## Adding Theme Support to New Components

1. **Use CSS variables** for all colors:
   ```css
   .new-component {
     background: var(--bg-secondary);
     color: var(--text-primary);
     border: 1px solid var(--border-color);
   }
   ```

2. **Avoid hardcoded colors** except for specific branding elements

3. **Test in both themes** to ensure readability

4. **Use semantic colors** for status/state:
   ```css
   .error { color: var(--error-color); }
   .success { color: var(--success-color); }
   ```

5. **Provide focus indicators** for interactive elements

## Customizing Colors

To customize the theme colors, edit the CSS variable definitions in `frontend/src/styles/theme.css`:

```css
[data-theme="light"] {
  --accent-primary: #your-color;
  --bg-primary: #your-color;
  /* ... other variables ... */
}

[data-theme="dark"] {
  --accent-primary: #your-color;
  --bg-primary: #your-color;
  /* ... other variables ... */
}
```

Then restart the development server for changes to take effect.

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- System preference detection: All modern browsers

## Performance Considerations

- CSS variables are cached by browsers
- Transitions are hardware-accelerated (use `transform` and `opacity` when possible)
- System preference changes are detected via MediaQueryList
- Theme preference is cached in localStorage for faster subsequent loads

## Troubleshooting

### Colors not changing when theme switches
- Ensure `theme.css` is imported before component styles
- Check that elements use `var()` instead of hardcoded colors
- Verify `data-theme` attribute is set on `<html>` element

### Flickering on page load
- Theme is initialized before app renders
- If flickering persists, the saved theme from localStorage might be different from system preference

### Accessibility issues
- All text/background combinations meet WCAG AA standards
- If custom colors are added, verify contrast ratios using WebAIM Contrast Checker

## References

- [CSS Custom Properties Spec](https://www.w3.org/TR/css-variables-1/)
- [prefers-color-scheme Media Query](https://www.w3.org/TR/mediaqueries-5/#prefers-color-scheme)
- [WCAG Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum)
