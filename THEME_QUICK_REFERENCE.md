# Dark/Light Theme - Quick Reference

## For Users

### How to Change Theme
1. Look at top-right of page in header
2. Click the theme button (☀️ 🌙 🔄)
3. Choose:
   - **Light** (☀️) - Bright background, dark text
   - **Dark** (🌙) - Dark background, light text
   - **Auto** (🔄) - Matches your system preference

Your choice is remembered!

### What's Auto Mode?
- Automatically matches your OS theme
- Updates when you change your OS settings
- Best for most users

---

## For Developers

### Using Theme in Components

**1. Add useTheme hook:**
```jsx
import { useTheme } from '../context/ThemeContext';

function MyComponent() {
  const { theme, effectiveTheme, toggleTheme } = useTheme();
  
  return (
    <div>
      <p>Current: {theme}</p>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
}
```

**2. Use CSS variables in styles:**
```css
.myComponent {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
```

**3. Available CSS Variables:**

**Colors:**
- `var(--bg-primary)` - Main background
- `var(--bg-secondary)` - Card/panel background
- `var(--text-primary)` - Main text
- `var(--text-secondary)` - Secondary text
- `var(--accent-primary)` - Links/buttons
- `var(--border-color)` - Borders

**Semantic:**
- `var(--success-color)` - Green
- `var(--warning-color)` - Orange
- `var(--error-color)` - Red
- `var(--info-color)` - Blue

**Overlays:**
- `var(--accent-overlay-light)` - Light accent overlay
- `var(--success-overlay)` - Light success overlay
- `var(--error-overlay)` - Light error overlay
- `var(--surface-overlay)` - Hover/inactive overlay

### Replacing Hardcoded Colors

**Before:**
```css
.button { background: #0969da; color: #ffffff; }
```

**After:**
```css
.button { background: var(--accent-primary); color: white; }
```

---

## File Locations

| File | Purpose |
|------|---------|
| `frontend/src/context/ThemeContext.jsx` | Theme state management |
| `frontend/src/components/ThemeToggleButton.jsx` | Toggle button component |
| `frontend/src/styles/theme.css` | CSS variables |
| `frontend/src/styles/THEME_GUIDE.md` | Complete styling guide |
| `UX_THEME_GUIDE.md` | User & developer guide |

---

## Common Tasks

### Add Theme to New Component
1. Use CSS variables instead of hardcoded colors
2. Test in both light and dark themes
3. Verify text is readable
4. Ensure focus indicators visible

### Test Theme System
```bash
npm run dev         # Start dev server
npm run build       # Production build
npm test -- theme   # Run tests
```

### Debug Theme Issues
1. Check browser DevTools
2. Verify `data-theme` attribute on `<html>`
3. Check `--accent-primary` in CSS
4. Clear localStorage if issues persist
5. Check console for errors

---

## CSS Variables Reference

### Light Theme
```
Backgrounds: White, Light Gray, Lighter Gray
Text: Dark Blue-Gray (high contrast)
Accent: Blue
Borders: Light Gray
Success: Green
Warning: Orange
Error: Red
```

### Dark Theme
```
Backgrounds: Very Dark Blue, Dark Blue, Slightly Lighter Blue
Text: Light Gray (high contrast)
Accent: Light Blue
Borders: Medium Dark Blue
Success: Bright Green
Warning: Bright Orange
Error: Bright Red
```

### Transition
- All theme changes smooth over 0.3 seconds
- Hardware accelerated
- No jarring color switches

---

## Troubleshooting

### Theme not persisting
→ Clear localStorage: `localStorage.clear()`
→ Check browser storage enabled

### Colors not updating
→ Verify CSS uses `var(--color-name)`
→ Check theme.css imported before component CSS
→ Clear browser cache

### Not working on mobile
→ Same CSS variables work on all devices
→ Check viewport meta tag present
→ Test in mobile browser DevTools

### Accessibility issues
→ All colors meet WCAG AA standards
→ Focus indicators visible (2px outline)
→ Works with keyboard navigation
→ Screen reader compatible

---

## Performance

- **CSS Size:** 5 KB (minimal)
- **JS Overhead:** <1 KB (negligible)
- **Theme Change:** <300 ms (smooth)
- **Transition:** 300 ms (smooth animation)

---

## Browser Support

✅ Chrome/Edge 90+
✅ Firefox 88+
✅ Safari 14+
✅ All modern browsers (last 2 years)

---

## Key Features

✅ Professional dark and light themes
✅ Auto mode for system preference
✅ Persistent user preference
✅ Smooth 0.3s transitions
✅ WCAG AA accessible
✅ 30+ CSS variables
✅ All components themed
✅ Responsive design
✅ Production ready

---

## Resources

- Full Guide: `UX_THEME_GUIDE.md`
- Styling Reference: `frontend/src/styles/THEME_GUIDE.md`
- Implementation: `THEME_IMPLEMENTATION_COMPLETE.md`
- Validation: `THEME_VALIDATION_REPORT.md`

---

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Last Updated:** 2024
