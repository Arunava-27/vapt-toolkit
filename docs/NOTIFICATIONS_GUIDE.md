# Notification System - Real-Time Alerts & Notifications

## Overview

The VAPT Toolkit now includes a comprehensive real-time notification system that alerts users about critical findings through multiple channels:

- **Desktop Notifications**: Browser notifications via SSE
- **Email Alerts**: SMTP-based email notifications
- **Slack Webhooks**: Post findings to Slack channels
- **Microsoft Teams**: Send findings to Teams channels

## Features

### 1. Multiple Notification Channels
- **Desktop (Browser)**: Real-time toast notifications and notification center
- **Email**: SMTP-configured email alerts with rich HTML formatting
- **Slack**: Formatted messages with color-coding by severity
- **Teams**: Microsoft Teams adaptive cards

### 2. Severity Filtering
Configure which severity levels trigger notifications:
- **Critical**: Only critical findings
- **High**: High and above
- **Medium**: Medium and above
- **Low**: Low and above
- **All**: All findings

### 3. Finding Type Filtering
Filter notifications by specific finding types:
- All Finding Types
- CVE Findings Only
- Open Ports Only
- Web Vulnerabilities Only

### 4. Real-Time Updates
All notifications are delivered in real-time during active scans with:
- Toast notifications (auto-dismissing)
- Notification center panel with filters
- Email queuing for configured recipients

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# SMTP Configuration for Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Microsoft Teams Webhook
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/YOUR/WEBHOOK/URL
```

### SMTP Setup

#### Gmail
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password in `SMTP_PASSWORD`

#### Other Email Providers
- Outlook: `smtp.outlook.com:587`
- SendGrid: `smtp.sendgrid.net:587`
- AWS SES: `email-smtp.[region].amazonaws.com:587`

### Slack Integration

1. Go to your Slack workspace settings
2. Create a new Webhook at: https://api.slack.com/messaging/webhooks
3. Copy the webhook URL to `SLACK_WEBHOOK_URL`

### Microsoft Teams Integration

1. Go to your Teams channel
2. Click "..." → "Connectors"
3. Search for "Incoming Webhook"
4. Create new webhook and copy URL to `TEAMS_WEBHOOK_URL`

## Usage

### API Endpoints

#### Configure Scan Notifications
```http
POST /api/scan/{scan_id}/notification/config
Content-Type: application/json

{
  "severity_filter": "high",
  "channels": ["desktop", "email", "slack"],
  "email": "user@example.com",
  "finding_types": "all"
}
```

#### Get Current Notification Config
```http
GET /api/scan/{scan_id}/notification/config
```

#### Test Email Notification
```http
POST /api/notification/test-email
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Test Slack Notification
```http
POST /api/notification/test-slack
```

#### Test Teams Notification
```http
POST /api/notification/test-teams
```

#### Check Notification System Status
```http
GET /api/notification/config
```

Response:
```json
{
  "smtp_configured": true,
  "slack_configured": true,
  "teams_configured": false,
  "smtp_host": "smtp.gmail.com"
}
```

### Frontend Components

#### NotificationCenter
Displays all notifications with filtering options.

```jsx
import NotificationCenter from './components/NotificationCenter';

<NotificationCenter notifications={notifications} />
```

#### NotificationSettings
Modal for configuring notification preferences per scan.

```jsx
import NotificationSettings from './components/NotificationSettings';

<NotificationSettings scanId={scanId} onClose={() => {}} />
```

#### NotificationToast
Auto-dismissing toast notifications for real-time alerts.

```jsx
import NotificationToast from './components/NotificationToast';

<NotificationToast 
  notification={notification}
  onClose={() => {}}
  autoCloseDuration={5000}
/>
```

## Notification Types

### Open Port Findings
- Severity: High (for SSH, RDP, Telnet, FTP), Medium (others)
- Finding Type: `open_port`
- Details: Port number, protocol, service, version

### CVE Findings
- Severity: Critical/High (only these are notified)
- Finding Type: `cve`
- Details: CVE ID, severity, description, CVSS score

### Web Vulnerabilities
- Severity: Critical/High (only these are notified)
- Finding Type: `web_vulnerability`
- Details: Vulnerability type, description, affected URL

## Example Notifications

### Desktop Notification
```
Title: Open Port Detected: 22
Severity: high
Message: SSH service detected on port 22/tcp
Finding Type: open_port
```

### Email Notification
```
Subject: [HIGH] VAPT Finding: CVE Found: CVE-2024-1234
Body: HTML formatted with findings details, target, CVSS score
```

### Slack Notification
```
Title: CVE Found: CVE-2024-1234
Severity: HIGH
Fields: CVE ID, Severity, Description, Target, CVSS Score
```

## Troubleshooting

### Email Not Sending
1. Check `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
2. Verify SMTP port is accessible (usually 587 for TLS)
3. Test with `/api/notification/test-email` endpoint
4. Check server logs for SMTP errors

### Slack Not Posting
1. Verify webhook URL is correct
2. Test with `/api/notification/test-slack` endpoint
3. Check Slack channel permissions
4. Ensure webhook is still active (webhooks expire)

### Teams Not Posting
1. Verify webhook URL is correct
2. Test with `/api/notification/test-teams` endpoint
3. Check Teams connector is still active
4. Ensure message format matches Teams requirements

### Notifications Not Appearing
1. Verify notification channels are enabled in scan config
2. Check severity filter matches finding severity
3. Check finding type filter matches finding type
4. Verify browser notifications are enabled
5. Check scan is still active (notifications stop when scan ends)

## Performance Considerations

- Desktop notifications are sent immediately via SSE
- Email notifications are sent synchronously (non-blocking via executor)
- Slack/Teams notifications are sent asynchronously
- Only findings matching severity/type filters generate notifications
- Notifications are only sent during active scans

## Security Considerations

- SMTP passwords should be stored in environment variables
- Webhook URLs should be stored securely
- Email addresses should be validated before sending
- Consider rate limiting for notification channels
- Webhook URLs should use HTTPS only

## Future Enhancements

- Database persistence for notifications
- Webhook retry logic with exponential backoff
- Notification templates customization
- PagerDuty integration
- OpsGenie integration
- Notification history/archival
- Batch notifications (digest mode)
- User-specific notification preferences
