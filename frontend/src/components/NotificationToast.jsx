import React, { useState, useEffect } from 'react';
import '../styles/NotificationToast.css';

const severityColors = {
  critical: '#d32f2f',
  high: '#f57c00',
  medium: '#fbc02d',
  low: '#388e3c',
  info: '#1976d2',
};

function NotificationToast({ notification, onClose, autoCloseDuration = 5000 }) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, autoCloseDuration);

    return () => clearTimeout(timer);
  }, [autoCloseDuration, onClose]);

  if (!isVisible) return null;

  return (
    <div
      className={`notification-toast notification-toast-${notification.severity}`}
      style={{ borderLeftColor: severityColors[notification.severity] }}
    >
      <div className="toast-icon">
        {notification.severity === 'critical' && (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
        )}
        {notification.severity === 'high' && (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
        )}
        {notification.severity === 'medium' && (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
        )}
        {(notification.severity === 'low' || notification.severity === 'info') && (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
        )}
      </div>

      <div className="toast-content">
        <div className="toast-title">{notification.title}</div>
        {notification.message && (
          <div className="toast-message">{notification.message}</div>
        )}
        {notification.finding_type && (
          <div className="toast-meta">
            Type: <span className="finding-type">{notification.finding_type}</span>
          </div>
        )}
      </div>

      <button className="toast-close" onClick={() => {
        setIsVisible(false);
        onClose();
      }}>
        ×
      </button>

      <div className="toast-progress">
        <div
          className="toast-progress-bar"
          style={{
            animation: `slideOut ${autoCloseDuration}ms linear forwards`,
          }}
        ></div>
      </div>
    </div>
  );
}

export default NotificationToast;
