import { useState } from 'react';

const AVAILABLE_SECTIONS = [
  { id: 'header', name: 'Header', icon: '📋' },
  { id: 'summary', name: 'Summary', icon: '📊' },
  { id: 'findings', name: 'Findings Grid', icon: '🔍' },
  { id: 'remediation', name: 'Remediation', icon: '🛠️' },
  { id: 'footer', name: 'Footer', icon: '📄' },
];

export function useTemplateBuilder() {
  const [sections, setSections] = useState([]);
  const [templateName, setTemplateName] = useState('');
  const [draggedSection, setDraggedSection] = useState(null);
  const [showCustomization, setShowCustomization] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDragStart = (section) => {
    setDraggedSection(section);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (draggedSection) {
      const newSection = {
        id: `${draggedSection.id}_${Date.now()}`,
        type: draggedSection.id,
        name: draggedSection.name,
        settings: {},
      };
      setSections([...sections, newSection]);
      setDraggedSection(null);
    }
  };

  const removeSection = (sectionId) => {
    setSections(sections.filter((s) => s.id !== sectionId));
  };

  const moveSectionUp = (index) => {
    if (index > 0) {
      const newSections = [...sections];
      [newSections[index - 1], newSections[index]] = [
        newSections[index],
        newSections[index - 1],
      ];
      setSections(newSections);
    }
  };

  const moveSectionDown = (index) => {
    if (index < sections.length - 1) {
      const newSections = [...sections];
      [newSections[index], newSections[index + 1]] = [
        newSections[index + 1],
        newSections[index],
      ];
      setSections(newSections);
    }
  };

  const updateSectionSetting = (sectionId, key, value) => {
    setSections(
      sections.map((s) =>
        s.id === sectionId
          ? { ...s, settings: { ...s.settings, [key]: value } }
          : s
      )
    );
  };

  const generatePreview = () => {
    let html = '<html><head><style>';
    html += `
      body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
      h1 { color: #2196F3; border-bottom: 3px solid #2196F3; }
      h2 { color: #2196F3; margin-top: 20px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { padding: 10px; text-align: left; border: 1px solid #ddd; }
      th { background: #2196F3; color: white; }
    `;
    html += '</style></head><body>';

    sections.forEach((section) => {
      switch (section.type) {
        case 'header':
          html += `<h1>${section.settings.title || 'Report Title'}</h1>`;
          break;
        case 'summary':
          html += '<h2>Summary</h2><p>Project: Sample Project<br/>Target: example.com</p>';
          break;
        case 'findings':
          html += `<h2>Findings</h2>
            <table>
              <tr><th>Issue</th><th>Severity</th><th>Status</th></tr>
              <tr><td>XSS Vulnerability</td><td>High</td><td>Open</td></tr>
              <tr><td>Weak Password</td><td>Medium</td><td>Open</td></tr>
            </table>`;
          break;
        case 'remediation':
          html += '<h2>Remediation</h2><ol><li>Fix XSS issues</li><li>Enforce strong passwords</li></ol>';
          break;
        case 'footer':
          html += "<hr><p style='font-size: 12px; color: #666;'>This report is confidential.</p>";
          break;
        default:
          break;
      }
    });

    html += '</body></html>';
    setPreview(html);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      alert('Please enter a template name');
      return;
    }

    if (sections.length === 0) {
      alert('Please add at least one section');
      return;
    }

    try {
      setLoading(true);
      generatePreview();

      const templateConfig = {
        sections: sections.map((s) => ({
          type: s.type,
          settings: s.settings,
        })),
      };

      const response = await fetch('/api/templates/report/preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: templateName,
          config: templateConfig,
        }),
      });

      if (response.ok) {
        alert('Template saved successfully!');
        setTemplateName('');
        setSections([]);
        setPreview('');
      } else {
        alert('Failed to save template');
      }
    } catch (error) {
      console.error('Error saving template:', error);
      alert('Error saving template');
    } finally {
      setLoading(false);
    }
  };

  return {
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
  };
}
