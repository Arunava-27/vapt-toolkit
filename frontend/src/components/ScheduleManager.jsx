import { useState, useEffect } from "react";

const FREQUENCIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const DAYS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

function timeToDisplay(time) {
  const [h, m] = time.split(":");
  return `${h.padStart(2, "0")}:${m.padStart(2, "0")}`;
}

function formatNextRun(nextRun) {
  if (!nextRun) return "—";
  const date = new Date(nextRun);
  const now = new Date();
  const diff = date - now;
  
  if (diff < 0) return "Past";
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (days > 0) return `in ${days}d ${hours}h`;
  if (hours > 0) return `in ${hours}h ${mins}m`;
  return `in ${mins}m`;
}

export default function ScheduleManager({ projectId, onClose }) {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [running, setRunning] = useState({});
  
  const [form, setForm] = useState({
    frequency: "daily",
    time: "09:00",
    day_of_week: 0,
    enabled: true,
  });

  const fetchSchedules = () => {
    setLoading(true);
    fetch("/api/schedules")
      .then((r) => r.json())
      .then((data) => {
        const filtered = projectId
          ? data.filter((s) => s.project_id === projectId)
          : data;
        setSchedules(filtered);
        setError(null);
      })
      .catch((e) => setError("Failed to load schedules"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchSchedules, [projectId]);

  const handleSave = async () => {
    try {
      const method = editingId ? "PUT" : "POST";
      const url = editingId
        ? `/api/schedule/${editingId}`
        : "/api/schedule/create";
      
      const payload = {
        ...form,
        project_id: projectId,
      };
      
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to save schedule");
      }
      
      setShowForm(false);
      setEditingId(null);
      setForm({ frequency: "daily", time: "09:00", day_of_week: 0, enabled: true });
      fetchSchedules();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleEdit = (schedule) => {
    setForm({
      frequency: schedule.frequency,
      time: schedule.time,
      day_of_week: schedule.day_of_week || 0,
      enabled: schedule.enabled,
    });
    setEditingId(schedule.id);
    setShowForm(true);
  };

  const handleDelete = async (scheduleId) => {
    if (!confirm("Delete this schedule?")) return;
    try {
      const res = await fetch(`/api/schedule/${scheduleId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      fetchSchedules();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleRunNow = async (scheduleId) => {
    setRunning((r) => ({ ...r, [scheduleId]: true }));
    try {
      const res = await fetch(`/api/schedule/${scheduleId}/run-now`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to run scan");
      alert("Scan queued!");
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning((r) => ({ ...r, [scheduleId]: false }));
    }
  };

  const handleToggle = async (schedule) => {
    try {
      const res = await fetch(`/api/schedule/${schedule.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          frequency: schedule.frequency,
          time: schedule.time,
          day_of_week: schedule.day_of_week,
          enabled: !schedule.enabled,
        }),
      });
      if (!res.ok) throw new Error("Toggle failed");
      fetchSchedules();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div style={{ padding: "1rem", borderRadius: 8, background: "var(--bg2)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h3 style={{ margin: 0 }}>📅 Scheduled Scans</h3>
        <button className="btn-secondary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Schedule"}
        </button>
      </div>

      {error && (
        <div style={{
          padding: "0.75rem", marginBottom: "1rem", borderRadius: 4,
          background: "var(--red)", color: "white", fontSize: "0.9rem"
        }}>
          {error}
        </div>
      )}

      {showForm && (
        <div style={{
          padding: "1rem", marginBottom: "1rem", borderRadius: 6,
          background: "var(--bg1)", border: "1px solid var(--border)",
        }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.9rem", fontWeight: 600, display: "block", marginBottom: "0.3rem" }}>
                Frequency
              </label>
              <select
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                style={{
                  width: "100%", padding: "0.5rem", borderRadius: 4,
                  border: "1px solid var(--border)", background: "var(--bg2)",
                  color: "var(--text)", fontSize: "0.9rem",
                }}
              >
                {FREQUENCIES.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.9rem", fontWeight: 600, display: "block", marginBottom: "0.3rem" }}>
                Time (UTC)
              </label>
              <input
                type="time"
                value={form.time}
                onChange={(e) => setForm({ ...form, time: e.target.value })}
                style={{
                  width: "100%", padding: "0.5rem", borderRadius: 4,
                  border: "1px solid var(--border)", background: "var(--bg2)",
                  color: "var(--text)", fontSize: "0.9rem",
                }}
              />
            </div>
          </div>

          {form.frequency === "weekly" && (
            <div style={{ marginBottom: "0.75rem" }}>
              <label style={{ fontSize: "0.9rem", fontWeight: 600, display: "block", marginBottom: "0.3rem" }}>
                Day of Week
              </label>
              <select
                value={form.day_of_week}
                onChange={(e) => setForm({ ...form, day_of_week: parseInt(e.target.value) })}
                style={{
                  width: "100%", padding: "0.5rem", borderRadius: 4,
                  border: "1px solid var(--border)", background: "var(--bg2)",
                  color: "var(--text)", fontSize: "0.9rem",
                }}
              >
                {DAYS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
            <button
              className="btn-secondary"
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
              }}
            >
              Cancel
            </button>
            <button className="btn-scan" onClick={handleSave}>
              {editingId ? "Update" : "Create"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ padding: "1rem", textAlign: "center", color: "var(--text-dim)" }}>
          Loading...
        </div>
      ) : schedules.length === 0 ? (
        <div style={{ padding: "1rem", textAlign: "center", color: "var(--text-dim)" }}>
          No schedules yet
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {schedules.map((s) => (
            <div
              key={s.id}
              style={{
                padding: "0.75rem", borderRadius: 6,
                background: s.enabled ? "var(--bg1)" : "var(--bg1) opacity(0.5)",
                border: `1px solid ${s.enabled ? "var(--accent)" : "var(--border)"}`,
                display: "flex", justifyContent: "space-between", alignItems: "center",
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.25rem" }}>
                  {s.frequency.charAt(0).toUpperCase() + s.frequency.slice(1)} @ {timeToDisplay(s.time)}
                  {s.frequency === "weekly" && ` (${DAYS.find((d) => d.value === s.day_of_week)?.label})`}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-dim)" }}>
                  Next: {formatNextRun(s.next_run)} · {s.enabled ? "✓ Active" : "○ Inactive"}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  className="btn-secondary"
                  onClick={() => handleToggle(s)}
                  style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}
                >
                  {s.enabled ? "Disable" : "Enable"}
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => handleRunNow(s.id)}
                  disabled={running[s.id]}
                  style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}
                >
                  {running[s.id] ? "..." : "Run Now"}
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => handleEdit(s)}
                  style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem" }}
                >
                  Edit
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => handleDelete(s.id)}
                  style={{ fontSize: "0.8rem", padding: "0.4rem 0.8rem", color: "var(--red)" }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
