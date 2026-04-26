# Component Refactoring - Import Reference Guide

## How to Import the New Modular Components

### 1. TemplateBuilder
```javascript
// From anywhere in the app:
import TemplateBuilder from '../components/TemplateBuilder';

// Or with relative path (example from pages directory):
import TemplateBuilder from '../components/TemplateBuilder';

// Individual sub-components (if needed):
import { AvailableSections } from '../components/TemplateBuilder/AvailableSections';
import { Canvas } from '../components/TemplateBuilder/Canvas';
import { PreviewPanel } from '../components/TemplateBuilder/PreviewPanel';
import { SectionCustomizer } from '../components/TemplateBuilder/SectionCustomizer';

// Hook (if you need to use it elsewhere):
import { useTemplateBuilder } from '../components/TemplateBuilder/hooks/useTemplateBuilder';
```

### 2. ScopeEditor
```javascript
// From anywhere in the app:
import ScopeEditor from '../components/ScopeEditor';

// Or with relative path (example from pages directory):
import ScopeEditor from '../components/ScopeEditor';

// Individual sub-components (if needed):
import { TargetInput } from '../components/ScopeEditor/TargetInput';
import { TargetList } from '../components/ScopeEditor/TargetList';
import { BulkPastePanel } from '../components/ScopeEditor/BulkPastePanel';
import { PresetsPanel } from '../components/ScopeEditor/PresetsPanel';
import { ExportControls } from '../components/ScopeEditor/ExportControls';

// Hook (if you need to use it elsewhere):
import { useScopeManagement } from '../components/ScopeEditor/hooks/useScopeManagement';
```

### 3. ReportTemplateManager
```javascript
// From anywhere in the app:
import ReportTemplateManager from '../components/ReportTemplateManager';

// Or with relative path (example from pages directory):
import ReportTemplateManager from '../components/ReportTemplateManager';

// Individual sub-components (if needed):
import { TemplateList } from '../components/ReportTemplateManager/TemplateList';
import { TemplateCreator } from '../components/ReportTemplateManager/TemplateCreator';
import { PreviewPanel } from '../components/ReportTemplateManager/PreviewPanel';

// Hook (if you need to use it elsewhere):
import { useTemplateManager } from '../components/ReportTemplateManager/hooks/useTemplateManager';
```

## Component Props and APIs

### TemplateBuilder
```javascript
<TemplateBuilder />
// No required props
// Component manages all state internally via useTemplateBuilder hook
```

### ScopeEditor
```javascript
<ScopeEditor 
  onScopeChange={(validTargets) => { /* callback when scope changes */ }}
  initialScope={["example.com", "192.168.1.1"]}
/>
// Props:
// - onScopeChange: (targets: string[]) => void
// - initialScope: string[] (optional)
```

### ReportTemplateManager
```javascript
<ReportTemplateManager />
// No required props
// Component manages all state internally via useTemplateManager hook
```

## Hook Usage Examples

### useTemplateBuilder
```javascript
import { useTemplateBuilder } from '../components/TemplateBuilder/hooks/useTemplateBuilder';

function MyComponent() {
  const {
    sections,
    templateName,
    setTemplateName,
    draggedSection,
    showCustomization,
    setShowCustomization,
    preview,
    loading,
    AVAILABLE_SECTIONS,
    handleDragStart,
    handleDragOver,
    handleDrop,
    removeSection,
    moveSectionUp,
    moveSectionDown,
    updateSectionSetting,
    generatePreview,
    handleSaveTemplate,
  } = useTemplateBuilder();

  // Use hook values and handlers...
}
```

### useScopeManagement
```javascript
import { useScopeManagement } from '../components/ScopeEditor/hooks/useScopeManagement';

function MyComponent() {
  const state = useScopeManagement(
    (validTargets) => console.log('Scope changed:', validTargets),
    ['example.com'] // initial scope
  );

  // state contains all targets, handlers, and UI state
}
```

### useTemplateManager
```javascript
import { useTemplateManager } from '../components/ReportTemplateManager/hooks/useTemplateManager';

function MyComponent() {
  const {
    templates,
    prebuiltTemplates,
    selectedTemplate,
    preview,
    isCreating,
    newTemplate,
    loading,
    projectId,
    setProjectId,
    setSelectedTemplate,
    setIsCreating,
    setNewTemplate,
    handleSelectTemplate,
    handleCreateTemplate,
    handleDeleteTemplate,
    handleApplyTemplate,
  } = useTemplateManager();

  // Use hook values and handlers...
}
```

## File Structure for Reference

```
frontend/src/components/
├── TemplateBuilder/
│   ├── index.jsx                    [Default export for main component]
│   ├── AvailableSections.jsx       [Named export]
│   ├── Canvas.jsx                  [Named export]
│   ├── PreviewPanel.jsx            [Named export]
│   ├── SectionCustomizer.jsx       [Named export]
│   └── hooks/
│       └── useTemplateBuilder.js   [Custom hook]
│
├── ScopeEditor/
│   ├── index.jsx                   [Default export for main component]
│   ├── TargetInput.jsx             [Named export]
│   ├── TargetList.jsx              [Named export]
│   ├── BulkPastePanel.jsx          [Named export]
│   ├── PresetsPanel.jsx            [Named export]
│   ├── ExportControls.jsx          [Named export]
│   └── hooks/
│       └── useScopeManagement.js   [Custom hook]
│
├── ReportTemplateManager/
│   ├── index.jsx                   [Default export for main component]
│   ├── TemplateList.jsx            [Named export]
│   ├── TemplateCreator.jsx         [Named export]
│   ├── PreviewPanel.jsx            [Named export]
│   └── hooks/
│       └── useTemplateManager.js   [Custom hook]
│
└── _archive_monolithic/            [Old monolithic files - can be deleted]
    ├── TemplateBuilder.jsx
    ├── ScopeEditor.jsx
    └── ReportTemplateManager.jsx
```

## Styling Notes

- All components use inline styles (objects)
- ScopeEditor uses `frontend/src/styles/ScopeEditor.css` for class-based styling
- No CSS Modules implemented (can be added in future)
- Styles are preserved from original implementations

## Migration Guide

If you need to migrate existing code that uses these components:

1. **If not using them yet**: Great! You can import them as shown above.

2. **If already using old monolithic versions**: 
   - Update imports from `components/TemplateBuilder` to `components/TemplateBuilder`
   - The default export of `index.jsx` maintains the same API
   - No prop changes needed

3. **If using sub-components directly**:
   - Import using the new paths shown above
   - Sub-components have same props/functionality as before

## Testing Notes

- Test file for ScopeEditor: `frontend/src/__tests__/components/ScopeEditor.test.jsx`
- Updated to import from: `../../../components/ScopeEditor`
- All hooks can be tested independently using hooks testing libraries

## Performance Optimization Opportunities

1. Wrap sub-components with `React.memo()` to prevent unnecessary re-renders
2. Consider implementing virtualization for large lists (TargetList)
3. Lazy load heavy components if needed (PreviewPanel for TemplateBuilder)
4. Consider context API for deeply nested prop passing in future

## Circular Import Prevention

✓ No circular imports detected
✓ All imports follow parent → child hierarchy
✓ Hooks don't import components, only used by components
✓ Sub-components don't import parent container

---

**Last Updated**: 2026-04-26
**Status**: ✓ Ready for Production
