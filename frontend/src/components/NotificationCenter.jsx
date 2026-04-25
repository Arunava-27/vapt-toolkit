import React, { useState, useEffect, useRef } from 'react';
import '../styles/NotificationCenter.css';

const severityColors = {
  critical: '#d32f2f',
  high: '#f57c00',
  medium: '#fbc02d',
  low: '#388e3c',
  info: '#1976d2',
};

function NotificationCenter({ notifications = [] }) {
  const [visible, setVisible] = useState(false);
  const [filteredNotifications, setFilteredNotifications] = useState([]);
  const [filter, setFilter] = useState('all');
  const centerRef = useRef(null);

  useEffect(() => {
    let filtered = notifications;
    if (filter !== 'all') {
      filtered = notifications.filter(n => n.severity === filter);
    }
    setFilteredNotifications(filtered);
  }, [notifications, filter]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (centerRef.current && !centerRef.current.contains(e.target)) {
        setVisible(false);
      }
    }

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [visible]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const clearAll = () => {
    setFilteredNotifications([]);
  };

  const markAsRead = (id) => {
    // Mark notification as read
  };

  return (
    <div className="notification-center" ref={centerRef}>
      <button
        className="notification-bell"
        onClick={() => setVisible(!visible)}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount}</span>
        )}
      </button>

      {visible && (
        <div className="notification-panel">
          <div className="notification-header">
            <h3>Notifications</h3>
            <button className="close-btn" onClick={() => setVisible(false)}>×</button>
          </div>

          <div className="notification-filters">
            <button
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button
              className={`filter-btn ${filter === 'critical' ? 'active' : ''}`}
              onClick={() => setFilter('critical')}
            >
              Critical
            </button>
            <button
              className={`filter-btn ${filter === 'high' ? 'active' : ''}`}
              onClick={() => setFilter('high')}
            >
              High
            </button>
            <button
              className={`filter-btn ${filter === 'medium' ? 'active' : ''}`}
              onClick={() => setFilter('medium')}
            >
              Medium
            </button>
          </div>

          <div className="notification-list">
            {filteredNotifications.length === 0 ? (
              <div className="empty-state">No notifications</div>
            ) : (
              filteredNotifications.map((notif, idx) => (
                <div key={idx} className="notification-item">
                  <div
                    className="notification-indicator"
                    style={{ backgroundColor: severityColors[notif.severity] }}
                  ></div>
                  <div className="notification-content">
                    <div className="notification-title">{notif.title}</div>
                    <div className="notification-message">{notif.message}</div>
                    <div className="notification-meta">
                      <span className="severity-badge" style={{
                        backgroundColor: severityColors[notif.severity] + '20',
                        color: severityColors[notif.severity],
                      }}>
                        {notif.severity}
                      </span>
                      {notif.finding_type && (
                        <span className="type-badge">{notif.finding_type}</span>
                      )}
                      <span className="timestamp">
                        {new Date(notif.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {filteredNotifications.length > 0 && (
            <div className="notification-footer">
              <button className="clear-btn" onClick={clearAll}>Clear all</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationCenter;
