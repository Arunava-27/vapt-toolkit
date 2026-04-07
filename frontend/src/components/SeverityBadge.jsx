const cls = {
  Critical: "sev sev-critical",
  High:     "sev sev-high",
  HIGH:     "sev sev-high",
  Medium:   "sev sev-medium",
  MEDIUM:   "sev sev-medium",
  Low:      "sev sev-low",
  LOW:      "sev sev-low",
};

export default function SeverityBadge({ severity }) {
  return <span className={cls[severity] || "sev sev-na"}>{severity || "N/A"}</span>;
}
