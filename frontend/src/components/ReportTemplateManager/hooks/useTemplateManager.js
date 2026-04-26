import { useState, useEffect } from 'react';

export function useTemplateManager() {
  const [templates, setTemplates] = useState([]);
  const [prebuiltTemplates, setPrebuiltTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: '', content: '' });
  const [loading, setLoading] = useState(false);
  const [projectId, setProjectId] = useState('');

  useEffect(() => {
    fetchTemplates();
    fetchPrebuiltTemplates();
  }, [projectId]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const url = projectId
        ? `/api/templates/report?projectId=${projectId}`
        : '/api/templates/report';
      const response = await fetch(url);
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPrebuiltTemplates = async () => {
    try {
      const response = await fetch('/api/templates/report/prebuilt');
      const data = await response.json();
      setPrebuiltTemplates(data.templates || []);
    } catch (error) {
      console.error('Error fetching prebuilt templates:', error);
    }
  };

  const handleSelectTemplate = async (template) => {
    setSelectedTemplate(template);
    await fetchPreview(template.id);
  };

  const fetchPreview = async (templateId) => {
    try {
      setLoading(true);
      const url = projectId
        ? `/api/templates/report/${templateId}/preview?projectId=${projectId}`
        : `/api/templates/report/${templateId}/preview`;
      const response = await fetch(url);
      const data = await response.json();
      setPreview(data.preview);
    } catch (error) {
      console.error('Error fetching preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplate.name.trim() || !newTemplate.content.trim()) {
      alert('Name and content are required');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch('/api/templates/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newTemplate.name,
          content: newTemplate.content,
          project_id: projectId || null,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates([...templates, { id: data.id, name: data.name }]);
        setNewTemplate({ name: '', content: '' });
        setIsCreating(false);
        alert('Template created successfully');
      } else {
        alert('Failed to create template');
      }
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Error creating template');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/templates/report/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setTemplates(templates.filter((t) => t.id !== templateId));
        setSelectedTemplate(null);
        setPreview(null);
        alert('Template deleted successfully');
      } else {
        alert('Failed to delete template');
      }
    } catch (error) {
      console.error('Error deleting template:', error);
      alert('Error deleting template');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate || !projectId) {
      alert('Please select a project and template');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `/api/templates/report/${selectedTemplate.id}/apply`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_id: projectId,
            scan_index: -1,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        downloadReport(data.report, selectedTemplate.name);
      } else {
        alert('Failed to generate report');
      }
    } catch (error) {
      console.error('Error applying template:', error);
      alert('Error generating report');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = (html, templateName) => {
    const element = document.createElement('a');
    const file = new Blob([html], { type: 'text/html' });
    element.href = URL.createObjectURL(file);
    element.download = `${templateName}-${new Date().toISOString().split('T')[0]}.html`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return {
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
  };
}
