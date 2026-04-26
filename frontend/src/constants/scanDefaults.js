/**
 * Centralized scan configuration constants.
 * Extracted from ScanForm.jsx, ScanPage.jsx, ScheduleManager.jsx, TemplateBuilder.jsx
 */

// Port scanning presets
export const PORT_PRESETS = [
  { label: "Top 100", value: "top-100", est: "~10s" },
  { label: "Top 1000", value: "top-1000", est: "~30s" },
  { label: "Top 5000", value: "top-5000", est: "~2 min" },
  { label: "Full", value: "full", est: "~10 min", warn: true },
  { label: "Custom", value: "custom", est: null },
];

// Nmap scan types
export const SCAN_TYPES = [
  { value: "connect", label: "Connect", desc: "Full TCP (-sT) · no root needed" },
  { value: "syn", label: "SYN", desc: "Stealth half-open (-sS) · needs root/Npcap" },
  { value: "aggressive", label: "Aggressive", desc: "-A · OS + version + scripts + traceroute" },
  { value: "udp", label: "UDP", desc: "-sU · slow · needs root" },
  { value: "syn_udp", label: "SYN+UDP", desc: "Both TCP & UDP · needs root" },
];

// Nmap script presets
export const SCRIPT_PRESETS = [
  { value: "", label: "None" },
  { value: "default", label: "Default" },
  { value: "banner", label: "Banner" },
  { value: "safe", label: "Safe" },
  { value: "vuln", label: "Vuln ⚠" },
  { value: "discovery", label: "Discovery" },
  { value: "http", label: "HTTP" },
  { value: "ssl", label: "SSL/TLS" },
  { value: "smb", label: "SMB" },
  { value: "ftp", label: "FTP" },
  { value: "ssh", label: "SSH" },
  { value: "smtp", label: "SMTP" },
  { value: "dns", label: "DNS" },
];

// Web scanner depth levels
export const WEB_DEPTHS = [
  { value: 1, label: "Basic", desc: "Homepage only · SQLi · XSS · Redirect" },
  { value: 2, label: "Standard", desc: "Crawl site · more payloads · security headers" },
  { value: 3, label: "Deep", desc: "Full crawl · header injection · path traversal" },
];

// Web scan time estimates
export const WEB_EST = {
  1: "~10s",
  2: "~30s",
  3: "~2 min",
};

// Scan classification types
export const SCAN_CLASSIFICATIONS = [
  { value: "passive", label: "🔍 Passive", desc: "OSINT + DNS lookup only. NO packets sent, NO port scanning, NO HTTP probing." },
  { value: "active", label: "⚡ Active", desc: "Port scanning + web probing + service enumeration. INTRUSIVE." },
  { value: "hybrid", label: "🎯 Hybrid", desc: "All modules · deepest analysis. MOST INTRUSIVE." },
];

// Scan modules available per classification
export const MODULES_BY_CLASSIFICATION = {
  passive: ["recon", "cve"],
  active: ["ports", "cve", "web"],
  hybrid: ["recon", "ports", "cve", "web"],
};

// All available modules
export const ALL_MODULES = [
  { key: "recon", icon: "🔍", label: "Recon", desc: "Subdomain enumeration" },
  { key: "ports", icon: "🚪", label: "Port Scan", desc: "Nmap port & service scan" },
  { key: "cve", icon: "🐛", label: "CVE Lookup", desc: "NVD API correlation" },
  { key: "web", icon: "🕸️", label: "Web Vulns", desc: "Probe web vulnerabilities" },
];

// Schedule frequency options
export const FREQUENCIES = [
  { value: "once", label: "Once (now)" },
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

// Days of week for scheduling
export const DAYS = [
  { value: "monday", label: "Monday", short: "Mon" },
  { value: "tuesday", label: "Tuesday", short: "Tue" },
  { value: "wednesday", label: "Wednesday", short: "Wed" },
  { value: "thursday", label: "Thursday", short: "Thu" },
  { value: "friday", label: "Friday", short: "Fri" },
  { value: "saturday", label: "Saturday", short: "Sat" },
  { value: "sunday", label: "Sunday", short: "Sun" },
];

// Report template available sections
export const AVAILABLE_SECTIONS = [
  { id: "executive_summary", name: "Executive Summary", icon: "📊" },
  { id: "technical_details", name: "Technical Details", icon: "⚙️" },
  { id: "vulnerabilities", name: "Vulnerabilities", icon: "🔓" },
  { id: "risk_assessment", name: "Risk Assessment", icon: "⚠️" },
  { id: "remediation", name: "Remediation", icon: "🔧" },
  { id: "compliance", name: "Compliance", icon: "✅" },
];

// Report template presets
export const PRESET_TEMPLATES = [
  { id: "executive", name: "Executive Summary", sections: ["executive_summary"] },
  { id: "technical", name: "Technical Report", sections: ["technical_details", "vulnerabilities"] },
  { id: "compliance", name: "Compliance Report", sections: ["vulnerabilities", "compliance", "remediation"] },
  { id: "full", name: "Full Report", sections: ["executive_summary", "technical_details", "vulnerabilities", "risk_assessment", "remediation", "compliance"] },
];

// Export formats
export const EXPORT_FORMATS = [
  { value: "pdf", label: "PDF" },
  { value: "excel", label: "Excel" },
  { value: "json", label: "JSON" },
  { value: "csv", label: "CSV" },
];

// Risk severity levels
export const SEVERITY_LEVELS = [
  { value: "critical", label: "🔴 Critical", color: "#ff4444" },
  { value: "high", label: "🟠 High", color: "#ff8844" },
  { value: "medium", label: "🟡 Medium", color: "#ffaa44" },
  { value: "low", label: "🟢 Low", color: "#44aa44" },
  { value: "info", label: "🔵 Info", color: "#4488ff" },
];

// Export default for all constants
export default {
  PORT_PRESETS,
  SCAN_TYPES,
  SCRIPT_PRESETS,
  WEB_DEPTHS,
  WEB_EST,
  SCAN_CLASSIFICATIONS,
  MODULES_BY_CLASSIFICATION,
  ALL_MODULES,
  FREQUENCIES,
  DAYS,
  AVAILABLE_SECTIONS,
  PRESET_TEMPLATES,
  EXPORT_FORMATS,
  SEVERITY_LEVELS,
};
