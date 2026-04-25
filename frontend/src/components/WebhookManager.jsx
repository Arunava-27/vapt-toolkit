import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../styles/WebhookManager.css';

const WebhookManager = ({ projectId }) => {
  const [webhooks, setWebhooks] = useState([]);
  const [logs, setLogs] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState(null);
  const [formData, setFormData] = useState({
    url: '',
    events: ['scan_completed'],
    secret: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const eventOptions = [
    { value: 'scan_started', label: 'Scan Started' },
    { value: 'scan_completed', label: 'Scan Completed' },
    { value: 'finding_discovered', label: 'Finding Discovered' },
    { value: 'scan_failed', label: 'Scan Failed' },
    { value: 'report_generated', label: 'Report Generated' },
    { value: 'vulnerability_fixed', label: 'Vulnerability Fixed' },
    { value: '*', label: 'All Events' }
  ];

  useEffect(() => {
    loadWebhooks();
  }, [projectId]);

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/webhooks', {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      setWebhooks(response.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load webhooks');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadWebhookLogs = async (webhookId) => {
    try {
      const response = await api.get(`/api/webhooks/${webhookId}/logs`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      setLogs(prev => ({ ...prev, [webhookId]: response.data }));
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  const handleRegisterWebhook = async (e) => {
    e.preventDefault();
    
    if (!formData.url || formData.events.length === 0 || !formData.secret) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      await api.post('/api/webhooks', formData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      
      setSuccess('Webhook registered successfully!');
      setFormData({ url: '', events: ['scan_completed'], secret: '' });
      setShowForm(false);
      
      setTimeout(() => setSuccess(null), 3000);
      loadWebhooks();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWebhook = async (webhookId) => {
    if (!window.confirm('Are you sure you want to delete this webhook?')) {
      return;
    }

    try {
      setLoading(true);
      await api.delete(`/api/webhooks/${webhookId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      
      setSuccess('Webhook deleted successfully!');
      setTimeout(() => setSuccess(null), 3000);
      loadWebhooks();
    } catch (err) {
      setError('Failed to delete webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleWebhook = async (webhookId, enabled) => {
    try {
      const endpoint = enabled ? 'disable' : 'enable';
      await api.post(`/api/webhooks/${webhookId}/${endpoint}`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      
      loadWebhooks();
    } catch (err) {
      setError('Failed to update webhook');
    }
  };

  const handleTestWebhook = async (webhookId) => {
    try {
      setLoading(true);
      await api.post('/api/webhooks/test', {
        webhook_id: webhookId,
        event_type: 'test_event'
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('api_key')}` }
      });
      
      setSuccess('Test event sent! Check webhook logs for details.');
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(() => loadWebhookLogs(webhookId), 1000);
    } catch (err) {
      setError('Failed to send test event');
    } finally {
      setLoading(false);
    }
  };

  const handleEventChange = (e) => {
    const value = e.target.value;
    
    if (value === '*') {
      setFormData(prev => ({ ...prev, events: ['*'] }));
    } else {
      setFormData(prev => {
        const newEvents = prev.events.includes(value)
          ? prev.events.filter(ev => ev !== value)
          : [...prev.events.filter(ev => ev !== '*'), value];
        return { ...prev, events: newEvents };
      });
    }
  };

  return (
    <div className="webhook-manager">
      <h2>Webhook Management</h2>
      
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      
      <div className="webhook-header">
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : 'Register New Webhook'}
        </button>
      </div>

      {showForm && (
        <div className="webhook-form">
          <h3>Register Webhook</h3>
          <form onSubmit={handleRegisterWebhook}>
            <div className="form-group">
              <label>Webhook URL</label>
              <input
                type="url"
                placeholder="https://example.com/webhook"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                required
              />
              <small>The endpoint that will receive webhook events</small>
            </div>

            <div className="form-group">
              <label>Events to Subscribe</label>
              <div className="event-checkboxes">
                {eventOptions.map(opt => (
                  <label key={opt.value} className="checkbox-label">
                    <input
                      type="checkbox"
                      value={opt.value}
                      checked={formData.events.includes(opt.value)}
                      onChange={handleEventChange}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Secret Key</label>
              <input
                type="password"
                placeholder="Enter a secret for signing webhooks"
                value={formData.secret}
                onChange={(e) => setFormData(prev => ({ ...prev, secret: e.target.value }))}
                required
              />
              <small>Used to sign webhook payloads. Store securely!</small>
            </div>

            <button type="submit" className="btn btn-success" disabled={loading}>
              {loading ? 'Registering...' : 'Register Webhook'}
            </button>
          </form>
        </div>
      )}

      <div className="webhooks-list">
        <h3>Registered Webhooks ({webhooks.length})</h3>
        
        {webhooks.length === 0 ? (
          <p className="empty-state">No webhooks registered yet</p>
        ) : (
          <div className="webhooks">
            {webhooks.map(webhook => (
              <div key={webhook.id} className="webhook-card">
                <div className="webhook-header-info">
                  <div className="webhook-details">
                    <h4>{webhook.url}</h4>
                    <div className="webhook-meta">
                      <span className="status" title={webhook.enabled ? 'Enabled' : 'Disabled'}>
                        {webhook.enabled ? '✓ Enabled' : '✗ Disabled'}
                      </span>
                      <span className="created">Created: {new Date(webhook.created_at).toLocaleDateString()}</span>
                      {webhook.last_triggered && (
                        <span className="last-triggered">Last triggered: {new Date(webhook.last_triggered).toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="webhook-events">
                  <strong>Events:</strong>
                  <div className="event-badges">
                    {webhook.events.map(event => (
                      <span key={event} className="badge badge-info">{event}</span>
                    ))}
                  </div>
                </div>

                <div className="webhook-actions">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      setSelectedWebhook(selectedWebhook === webhook.id ? null : webhook.id);
                      if (selectedWebhook !== webhook.id) {
                        loadWebhookLogs(webhook.id);
                      }
                    }}
                  >
                    {selectedWebhook === webhook.id ? 'Hide Logs' : 'View Logs'}
                  </button>

                  <button
                    className="btn btn-sm btn-warning"
                    onClick={() => handleTestWebhook(webhook.id)}
                    disabled={loading}
                  >
                    Send Test Event
                  </button>

                  <button
                    className={`btn btn-sm ${webhook.enabled ? 'btn-danger' : 'btn-success'}`}
                    onClick={() => handleToggleWebhook(webhook.id, webhook.enabled)}
                  >
                    {webhook.enabled ? 'Disable' : 'Enable'}
                  </button>

                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleDeleteWebhook(webhook.id)}
                    disabled={loading}
                  >
                    Delete
                  </button>
                </div>

                {selectedWebhook === webhook.id && (
                  <div className="webhook-logs">
                    <h5>Delivery Logs</h5>
                    {logs[webhook.id]?.logs?.length > 0 ? (
                      <div className="logs-table">
                        <table>
                          <thead>
                            <tr>
                              <th>Time</th>
                              <th>Event</th>
                              <th>Status</th>
                              <th>Attempts</th>
                              <th>Response</th>
                            </tr>
                          </thead>
                          <tbody>
                            {logs[webhook.id].logs.map(log => (
                              <tr key={log.id}>
                                <td>{new Date(log.created_at).toLocaleString()}</td>
                                <td>{log.event}</td>
                                <td className={`status ${log.status < 300 ? 'success' : 'error'}`}>
                                  {log.status}
                                </td>
                                <td>{log.attempts}</td>
                                <td className="response" title={log.response}>{log.response?.substring(0, 50)}...</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="empty-state">No delivery logs yet</p>
                    )}
                    
                    {logs[webhook.id]?.stats && (
                      <div className="logs-stats">
                        <h6>Statistics</h6>
                        <div className="stats-grid">
                          <div className="stat">
                            <span className="label">Total Deliveries:</span>
                            <span className="value">{logs[webhook.id].stats.total_deliveries}</span>
                          </div>
                          <div className="stat">
                            <span className="label">Successful:</span>
                            <span className="value success">{logs[webhook.id].stats.successful}</span>
                          </div>
                          <div className="stat">
                            <span className="label">Failed:</span>
                            <span className="value error">{logs[webhook.id].stats.failed}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WebhookManager;
