import React, { useState, useEffect } from 'react';
import '../styles/NotificationSettings.css';

function NotificationSettings({ scanId, onClose }) {
  const [config, setConfig] = useState({
    severity_filter: 'high',
    channels: ['desktop'],
    email: '',
    finding_types: 'all',
  });
  const [notificationStatus, setNotificationStatus] = useState({
    smtp_configured: false,
    slack_configured: false,
    teams_configured: false,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Fetch current config and system status
    Promise.all([
      fetch(`/api/scan/${scanId}/notification/config`)
        .then(r => r.json())
        .catch(() => ({})),
      fetch('/api/notification/config')
        .then(r => r.json())
        .catch(() => ({}))
    ]).then(([configData, statusData]) => {
      if (configData && Object.keys(configData).length > 0) {
        setConfig(configData);
      }
      if (statusData) {
        setNotificationStatus(statusData);
      }
    });
  }, [scanId]);

  const handleSeverityChange = (e) => {
    setConfig({ ...config, severity_filter: e.target.value });
  };

  const handleChannelToggle = (channel) => {
    const channels = config.channels.includes(channel)
      ? config.channels.filter(c => c !== channel)
      : [...config.channels, channel];
    setConfig({ ...config, channels });
  };

  const handleEmailChange = (e) => {
    setConfig({ ...config, email: e.target.value });
  };

  const handleFindingTypeChange = (e) => {
    setConfig({ ...config, finding_types: e.target.value });
  };

  const handleSave = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`/api/scan/${scanId}/notification/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (res.ok) {
        setMessage('Settings saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Failed to save settings');
      }
    } catch (err) {
      setMessage('Error saving settings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const testNotification = async (channel) => {
    try {
      const res = await fetch(`/api/notification/test-${channel}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: channel === 'email' ? JSON.stringify({ email: config.email }) : '{}',
      });
      const data = await res.json();
      setMessage(data.message || `${channel} notification sent!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage(`Failed to send ${channel} notification`);
    }
  };

  return (
    <div className="notification-settings-modal">
      <div className="modal-overlay" onClick={onClose}></div>
      <div className="modal-content">
        <div className="modal-header">
          <h2>Notification Settings</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Severity Filter */}
          <div className="settings-section">
            <label>Severity Filter</label>
            <select value={config.severity_filter} onChange={handleSeverityChange}>
              <option value="all">All Severities</option>
              <option value="critical">Critical and above</option>
              <option value="high">High and above</option>
              <option value="medium">Medium and above</option>
              <option value="low">Low and above</option>
            </select>
            <p className="help-text">Only send notifications for findings at or above this severity level</p>
          </div>

          {/* Finding Types */}
          <div className="settings-section">
            <label>Finding Types</label>
            <select value={config.finding_types} onChange={handleFindingTypeChange}>
              <option value="all">All Finding Types</option>
              <option value="cve">CVE Findings Only</option>
              <option value="open_port">Open Ports Only</option>
              <option value="web_vulnerability">Web Vulnerabilities Only</option>
            </select>
            <p className="help-text">Filter by specific type of findings</p>
          </div>

          {/* Notification Channels */}
          <div className="settings-section">
            <label>Notification Channels</label>
            <div className="channels-grid">
              <div className="channel-option">
                <input
                  type="checkbox"
                  id="desktop"
                  checked={config.channels.includes('desktop')}
                  onChange={() => handleChannelToggle('desktop')}
                />
                <label htmlFor="desktop">Desktop (Browser)</label>
                <span className="status-indicator ready">Ready</span>
              </div>

              <div className="channel-option">
                <input
                  type="checkbox"
                  id="email"
                  checked={config.channels.includes('email')}
                  onChange={() => handleChannelToggle('email')}
                  disabled={!notificationStatus.smtp_configured}
                />
                <label htmlFor="email">Email</label>
                {notificationStatus.smtp_configured ? (
                  <span className="status-indicator ready">Configured</span>
                ) : (
                  <span className="status-indicator disabled">Not configured</span>
                )}
              </div>

              <div className="channel-option">
                <input
                  type="checkbox"
                  id="slack"
                  checked={config.channels.includes('slack')}
                  onChange={() => handleChannelToggle('slack')}
                  disabled={!notificationStatus.slack_configured}
                />
                <label htmlFor="slack">Slack</label>
                {notificationStatus.slack_configured ? (
                  <span className="status-indicator ready">Configured</span>
                ) : (
                  <span className="status-indicator disabled">Not configured</span>
                )}
              </div>

              <div className="channel-option">
                <input
                  type="checkbox"
                  id="teams"
                  checked={config.channels.includes('teams')}
                  onChange={() => handleChannelToggle('teams')}
                  disabled={!notificationStatus.teams_configured}
                />
                <label htmlFor="teams">Teams</label>
                {notificationStatus.teams_configured ? (
                  <span className="status-indicator ready">Configured</span>
                ) : (
                  <span className="status-indicator disabled">Not configured</span>
                )}
              </div>
            </div>
          </div>

          {/* Email Configuration */}
          {config.channels.includes('email') && (
            <div className="settings-section">
              <label>Email Address</label>
              <input
                type="email"
                value={config.email}
                onChange={handleEmailChange}
                placeholder="your@email.com"
              />
              <p className="help-text">Enter the email address to receive notifications</p>
            </div>
          )}

          {/* Test Notifications */}
          <div className="settings-section">
            <label>Test Notifications</label>
            <div className="test-buttons">
              <button
                className="test-btn"
                onClick={() => testNotification('email')}
                disabled={!config.channels.includes('email') || !config.email}
              >
                Test Email
              </button>
              <button
                className="test-btn"
                onClick={() => testNotification('slack')}
                disabled={!config.channels.includes('slack')}
              >
                Test Slack
              </button>
              <button
                className="test-btn"
                onClick={() => testNotification('teams')}
                disabled={!config.channels.includes('teams')}
              >
                Test Teams
              </button>
            </div>
          </div>

          {/* Status Message */}
          {message && (
            <div className={`message ${message.includes('Error') || message.includes('Failed') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            className="btn-cancel"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="btn-save"
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotificationSettings;
