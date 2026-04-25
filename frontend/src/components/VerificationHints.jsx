"""React component for displaying manual verification hints."""

import React, { useState, useEffect } from 'react';

const VerificationHints = ({ finding }) => {
  const [hints, setHints] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const fetchHints = async () => {
    if (!finding?.finding_id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(\/api/findings/\/hints\);
      if (!response.ok) {
        throw new Error('Failed to fetch hints');
      }
      const data = await response.json();
      setHints(data.hints);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const renderStep = (step, index) => (
    <div key={index} className="verification-step">
      <p className="step-text">{step}</p>
    </div>
  );

  if (!finding) {
    return null;
  }

  return (
    <div className="verification-hints-container">
      <div className="hints-header">
        <button
          className="hints-toggle"
          onClick={() => {
            setExpanded(!expanded);
            if (!expanded && !hints) {
              fetchHints();
            }
          }}
        >
          <span className="toggle-icon">{expanded ? '▼' : '▶'}</span>
          Manual Verification Hints
        </button>
      </div>

      {expanded && (
        <div className="hints-content">
          {loading && <div className="loading-indicator">Loading hints...</div>}
          
          {error && <div className="error-message">Error: {error}</div>}
          
          {hints && (
            <>
              <div className="hints-section">
                <h4>{hints.title}</h4>
                <p className="hints-description">{hints.description}</p>
              </div>

              <div className="hints-section">
                <h5>Verification Steps</h5>
                <div className="steps-list">
                  {hints.steps.map((step, idx) => renderStep(step, idx))}
                </div>
              </div>

              <div className="hints-section">
                <h5>Tools & Techniques</h5>
                <div className="tools-list">
                  {hints.tools.map((tool, idx) => (
                    <div key={idx} className="tool-item">
                      <span>{tool}</span>
                      <button
                        className="copy-btn"
                        title="Copy to clipboard"
                        onClick={() => copyToClipboard(tool)}
                      >
                        📋
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="hints-section">
                <h5>Expected Signs of Vulnerability</h5>
                <ul className="indicators-list">
                  {hints.expected_signs.map((sign, idx) => (
                    <li key={idx}>{sign}</li>
                  ))}
                </ul>
              </div>

              <div className="hints-section warning">
                <h5>⚠️ False Positive Indicators</h5>
                <ul className="indicators-list">
                  {hints.false_positive_indicators.map((indicator, idx) => (
                    <li key={idx}>{indicator}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}

      <style jsx>{\
        .verification-hints-container {
          margin: 12px 0;
          border: 1px solid #ddd;
          border-radius: 4px;
          overflow: hidden;
        }

        .hints-header {
          background: #f5f5f5;
          border-bottom: 1px solid #ddd;
        }

        .hints-toggle {
          width: 100%;
          padding: 12px;
          background: none;
          border: none;
          text-align: left;
          cursor: pointer;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background 0.2s;
        }

        .hints-toggle:hover {
          background: #efefef;
        }

        .toggle-icon {
          display: inline-block;
          width: 20px;
        }

        .hints-content {
          padding: 16px;
          background: #fafafa;
        }

        .hints-section {
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #eee;
        }

        .hints-section:last-child {
          border-bottom: none;
          margin-bottom: 0;
        }

        .hints-section.warning {
          background: #fff3cd;
          padding: 12px;
          border-radius: 4px;
          border: 1px solid #ffeaa7;
        }

        .hints-section h4 {
          margin: 0 0 8px 0;
          font-size: 16px;
          color: #333;
        }

        .hints-section h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #555;
          font-weight: 600;
        }

        .hints-description {
          margin: 0;
          font-size: 14px;
          color: #666;
          line-height: 1.4;
        }

        .steps-list {
          list-style: decimal;
          padding-left: 16px;
        }

        .verification-step {
          margin-bottom: 8px;
        }

        .step-text {
          margin: 0;
          font-size: 13px;
          color: #555;
          line-height: 1.4;
        }

        .tools-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .tool-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background: white;
          border: 1px solid #ddd;
          border-radius: 3px;
          font-size: 13px;
        }

        .copy-btn {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 14px;
          padding: 4px 8px;
          opacity: 0.6;
          transition: opacity 0.2s;
        }

        .copy-btn:hover {
          opacity: 1;
        }

        .indicators-list {
          margin: 0;
          padding-left: 20px;
          font-size: 13px;
          color: #555;
          line-height: 1.5;
        }

        .indicators-list li {
          margin-bottom: 6px;
        }

        .loading-indicator {
          padding: 12px;
          text-align: center;
          color: #666;
          font-size: 13px;
        }

        .error-message {
          padding: 12px;
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
          border-radius: 4px;
          font-size: 13px;
        }
      \}</style>
    </div>
  );
};

export default VerificationHints;
