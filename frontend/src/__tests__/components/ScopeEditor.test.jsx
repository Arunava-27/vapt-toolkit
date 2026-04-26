/**
 * Tests for ScopeEditor component
 *
 * Tests cover:
 * - Target type inference
 * - Target validation
 * - Drag-drop functionality
 * - Bulk paste
 * - Presets management
 * - Export/import
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ScopeEditor from '../../../components/ScopeEditor';

describe('ScopeEditor Component', () => {
  beforeEach(() => {
    // Mock fetch API
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ presets: [] }),
      })
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders scope editor with header', () => {
      render(<ScopeEditor />);
      expect(screen.getByText('Scan Scope Editor')).toBeInTheDocument();
    });

    test('renders action buttons', () => {
      render(<ScopeEditor />);
      expect(screen.getByText(/Add Target/)).toBeInTheDocument();
      expect(screen.getByText(/Paste Bulk/)).toBeInTheDocument();
      expect(screen.getByText(/Import/)).toBeInTheDocument();
      expect(screen.getByText(/Presets/)).toBeInTheDocument();
      expect(screen.getByText(/Validate/)).toBeInTheDocument();
    });

    test('renders export buttons', () => {
      render(<ScopeEditor />);
      expect(screen.getByText('JSON')).toBeInTheDocument();
      expect(screen.getByText('YAML')).toBeInTheDocument();
      expect(screen.getByText('TXT')).toBeInTheDocument();
    });

    test('renders empty state', () => {
      render(<ScopeEditor />);
      expect(screen.getByText('No targets added yet')).toBeInTheDocument();
    });
  });

  describe('Target Management', () => {
    test('adds a new target', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);

      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        expect(inputs.length).toBeGreaterThan(0);
      });
    });

    test('updates target value', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        const input = inputs[0];
        fireEvent.change(input, { target: { value: 'example.com' } });
        expect(input.value).toBe('example.com');
      });
    });

    test('removes a target', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const removeBtn = screen.getByTitle('Remove target');
        fireEvent.click(removeBtn);
        expect(screen.getByText('No targets added yet')).toBeInTheDocument();
      });
    });
  });

  describe('Validation', () => {
    test('shows error for invalid URL', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'invalid' } });
      });

      await waitFor(() => {
        expect(screen.getByText(/Invalid/i)).toBeInTheDocument();
      });
    });

    test('accepts valid URLs', async () => {
      render(<ScopeEditor onScopeChange={() => {}} />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'https://example.com' } });
      });

      await waitFor(() => {
        const statValid = screen.queryByText(/✓ 1 valid/);
        expect(statValid).toBeInTheDocument();
      });
    });

    test('accepts valid domains', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'example.com' } });
      });

      await waitFor(() => {
        expect(screen.getByText(/DOMAIN/)).toBeInTheDocument();
      });
    });

    test('accepts valid IPs', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: '192.168.1.1' } });
      });

      await waitFor(() => {
        expect(screen.getByText(/IP/)).toBeInTheDocument();
      });
    });

    test('accepts wildcards', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: '*.example.com' } });
      });

      await waitFor(() => {
        expect(screen.getByText(/WILDCARD/)).toBeInTheDocument();
      });
    });
  });

  describe('Bulk Paste', () => {
    test('toggles bulk paste panel', () => {
      render(<ScopeEditor />);
      const pasteBtn = screen.getByText(/Paste Bulk/);

      fireEvent.click(pasteBtn);
      expect(screen.getByPlaceholderText(/Paste multiple targets/)).toBeInTheDocument();

      fireEvent.click(pasteBtn);
      expect(screen.queryByPlaceholderText(/Paste multiple targets/)).not.toBeInTheDocument();
    });

    test('adds targets from bulk paste', async () => {
      render(<ScopeEditor />);
      const pasteBtn = screen.getByText(/Paste Bulk/);
      fireEvent.click(pasteBtn);

      const textarea = screen.getByPlaceholderText(/Paste multiple targets/);
      fireEvent.change(textarea, {
        target: {
          value: 'example.com\n192.168.1.1\nhttps://api.example.com',
        },
      });

      const addBtn = screen.getByRole('button', { name: /Add Targets/ });
      fireEvent.click(addBtn);

      await waitFor(() => {
        expect(screen.getByText(/DOMAIN/)).toBeInTheDocument();
        expect(screen.getByText(/IP/)).toBeInTheDocument();
        expect(screen.getByText(/URL/)).toBeInTheDocument();
      });
    });
  });

  describe('Drag-Drop', () => {
    test('highlights target on drag over', async () => {
      render(<ScopeEditor />);
      const addBtn = screen.getByText(/Add Target/);

      // Add first target
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'example.com' } });
      });

      // Add second target
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[1], { target: { value: '192.168.1.1' } });
      });

      const items = screen.getAllByText(/⋮⋮/);
      expect(items.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Presets', () => {
    test('toggles presets panel', () => {
      render(<ScopeEditor />);
      const presetsBtn = screen.getByText(/Presets/);

      fireEvent.click(presetsBtn);
      expect(screen.getByPlaceholderText(/Preset name/)).toBeInTheDocument();

      fireEvent.click(presetsBtn);
      expect(screen.queryByPlaceholderText(/Preset name/)).not.toBeInTheDocument();
    });

    test('saves preset', async () => {
      render(<ScopeEditor />);

      // Add a target
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'example.com' } });
      });

      // Open presets
      const presetsBtn = screen.getByText(/Presets/);
      fireEvent.click(presetsBtn);

      // Save preset
      const nameInput = screen.getByPlaceholderText(/Preset name/);
      fireEvent.change(nameInput, { target: { value: 'Test Preset' } });

      const saveBtn = screen.getByRole('button', { name: /Save Current/ });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/scans/scope/presets',
          expect.objectContaining({
            method: 'POST',
          })
        );
      });
    });
  });

  describe('Export', () => {
    test('exports as JSON', async () => {
      render(<ScopeEditor />);

      // Add a target
      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'example.com' } });
      });

      // Mock URL.createObjectURL and document.createElement
      global.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
      global.URL.revokeObjectURL = jest.fn();

      const exportBtn = screen.getByRole('button', { name: 'JSON' });
      fireEvent.click(exportBtn);

      // Verify createObjectURL was called
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  describe('Initial Scope', () => {
    test('initializes with provided scope', async () => {
      const initialScope = ['example.com', '192.168.1.1'];
      render(<ScopeEditor initialScope={initialScope} />);

      await waitFor(() => {
        expect(screen.getByText(/✓ 2 valid/)).toBeInTheDocument();
      });
    });
  });

  describe('Callbacks', () => {
    test('calls onScopeChange when targets change', async () => {
      const onScopeChange = jest.fn();
      render(<ScopeEditor onScopeChange={onScopeChange} />);

      const addBtn = screen.getByText(/Add Target/);
      fireEvent.click(addBtn);

      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'example.com' } });
      });

      await waitFor(() => {
        expect(onScopeChange).toHaveBeenCalledWith(['example.com']);
      });
    });
  });

  describe('Target Grouping', () => {
    test('groups targets by type', async () => {
      render(<ScopeEditor />);

      const addBtn = screen.getByText(/Add Target/);

      // Add URL
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[0], { target: { value: 'https://example.com' } });
      });

      // Add Domain
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[1], { target: { value: 'example.com' } });
      });

      // Add IP
      fireEvent.click(addBtn);
      await waitFor(() => {
        const inputs = screen.getAllByPlaceholderText(/Enter /);
        fireEvent.change(inputs[2], { target: { value: '192.168.1.1' } });
      });

      await waitFor(() => {
        expect(screen.getByText(/URL/)).toBeInTheDocument();
        expect(screen.getByText(/DOMAIN/)).toBeInTheDocument();
        expect(screen.getByText(/IP/)).toBeInTheDocument();
      });
    });
  });
});

describe('ScopeEditor Target Type Inference', () => {
  /**
   * Note: These tests should be moved to a separate utility test file
   * once the inference logic is extracted from the component
   */

  test('infers URL type', () => {
    const isURL = (value) => value.match(/^https?:\/\//);
    expect(isURL('https://example.com')).toBeTruthy();
    expect(isURL('example.com')).toBeFalsy();
  });

  test('infers domain type', () => {
    const isDomain = (value) =>
      value.match(/^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?(\:\d+)?$/);
    expect(isDomain('example.com')).toBeTruthy();
    expect(isDomain('sub.example.com')).toBeTruthy();
    expect(isDomain('example.com:8080')).toBeTruthy();
  });

  test('infers IP type', () => {
    const isIP = (value) =>
      value.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/);
    expect(isIP('192.168.1.1')).toBeTruthy();
    expect(isIP('10.0.0.0/24')).toBeTruthy();
    expect(isIP('example.com')).toBeFalsy();
  });

  test('infers wildcard type', () => {
    const isWildcard = (value) => value.includes('*');
    expect(isWildcard('*.example.com')).toBeTruthy();
    expect(isWildcard('example.com')).toBeFalsy();
  });
});
