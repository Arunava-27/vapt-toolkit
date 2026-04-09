/**
 * ScanCharts.jsx
 * Recharts-based charts for CVE, Port and Web scan results.
 * Rendered inside ResultsDashboard, above the detailed tables.
 */
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";

// ── Palette ──────────────────────────────────────────────────────────────────
const SEV_COLORS = {
  CRITICAL: "#f85149",
  HIGH:     "#f0883e",
  MEDIUM:   "#d29922",
  LOW:      "#3fb950",
  NONE:     "#8b949e",
};

const PROTO_COLORS = { tcp: "#58a6ff", udp: "#bf91f3", sctp: "#3fb950" };
const BAR_COLORS = ["#58a6ff","#3fb950","#bf91f3","#f0883e","#f85149","#79c0ff","#d29922"];

const CHART_STYLE = {
  background: "transparent",
  fontSize: "11px",
};
const TOOLTIP_STYLE = {
  background: "#161b22",
  border: "1px solid #30363d",
  borderRadius: 6,
  color: "#c9d1d9",
  fontSize: 12,
};

// ── Tiny shared empty state ───────────────────────────────────────────────────
function NoData({ msg = "No data" }) {
  return <p style={{ color: "#8b949e", fontSize: ".8rem", padding: "1rem 0" }}>{msg}</p>;
}

// ── Custom legend that fits dark theme ────────────────────────────────────────
function DarkLegend({ payload }) {
  if (!payload?.length) return null;
  return (
    <ul style={{ display: "flex", flexWrap: "wrap", gap: ".5rem .9rem", listStyle: "none", padding: 0, marginTop: 4 }}>
      {payload.map((e, i) => (
        <li key={i} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "#c9d1d9" }}>
          <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: e.color }} />
          {e.value} {e.payload?.value !== undefined ? `(${e.payload.value})` : ""}
        </li>
      ))}
    </ul>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CVE Charts
// ─────────────────────────────────────────────────────────────────────────────
export function CVECharts({ data }) {
  if (!data) return null;
  const correlations = data.correlations || [];
  if (!correlations.length) return null;

  // Severity distribution
  const sevMap = {};
  correlations.forEach((c) => {
    const s = (c.severity || "NONE").toUpperCase();
    sevMap[s] = (sevMap[s] || 0) + 1;
  });
  const sevData = Object.entries(sevMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => {
      const order = ["CRITICAL","HIGH","MEDIUM","LOW","NONE"];
      return order.indexOf(a.name) - order.indexOf(b.name);
    });

  // CVSS score buckets
  const buckets = { "0–3": 0, "3–5": 0, "5–7": 0, "7–9": 0, "9–10": 0 };
  correlations.forEach((c) => {
    const s = parseFloat(c.score) || 0;
    if      (s < 3)  buckets["0–3"]++;
    else if (s < 5)  buckets["3–5"]++;
    else if (s < 7)  buckets["5–7"]++;
    else if (s < 9)  buckets["7–9"]++;
    else             buckets["9–10"]++;
  });
  const scoreData = Object.entries(buckets).map(([name, value]) => ({ name, value }));

  return (
    <div className="charts-row">
      {/* Severity pie */}
      <div className="chart-card">
        <h4 className="chart-title">CVE Severity</h4>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart style={CHART_STYLE}>
            <Pie data={sevData} dataKey="value" cx="50%" cy="45%"
                 innerRadius={45} outerRadius={75} paddingAngle={2}>
              {sevData.map((e) => (
                <Cell key={e.name} fill={SEV_COLORS[e.name] || "#8b949e"} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend content={<DarkLegend />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* CVSS score histogram */}
      <div className="chart-card">
        <h4 className="chart-title">CVSS Score Distribution</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={scoreData} style={CHART_STYLE}
                    margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
            <XAxis dataKey="name" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#1f6feb22" }} />
            <Bar dataKey="value" name="CVEs" radius={[4,4,0,0]}>
              {scoreData.map((e, i) => {
                const score = parseFloat(e.name.split("–")[1]) || 0;
                const color = score >= 9 ? SEV_COLORS.CRITICAL
                            : score >= 7 ? SEV_COLORS.HIGH
                            : score >= 5 ? SEV_COLORS.MEDIUM
                            : score >= 3 ? SEV_COLORS.LOW
                            : SEV_COLORS.NONE;
                return <Cell key={i} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Port Charts
// ─────────────────────────────────────────────────────────────────────────────
export function PortCharts({ data }) {
  if (!data) return null;
  const ports = data.open_ports || [];
  if (!ports.length) return null;

  // Top services bar
  const svcMap = {};
  ports.forEach((p) => {
    const name = p.service || "unknown";
    svcMap[name] = (svcMap[name] || 0) + 1;
  });
  const svcData = Object.entries(svcMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  // Protocol split
  const protoMap = {};
  ports.forEach((p) => {
    const pr = (p.protocol || "tcp").toLowerCase();
    protoMap[pr] = (protoMap[pr] || 0) + 1;
  });
  const protoData = Object.entries(protoMap).map(([name, value]) => ({ name: name.toUpperCase(), value }));

  return (
    <div className="charts-row">
      {/* Services bar */}
      <div className="chart-card chart-card-wide">
        <h4 className="chart-title">Top Services</h4>
        {svcData.length === 0 ? <NoData msg="No service info" /> : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={svcData} layout="vertical" style={CHART_STYLE}
                      margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" horizontal={false} />
              <XAxis type="number" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={72}
                     tick={{ fill: "#c9d1d9", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#1f6feb22" }} />
              <Bar dataKey="value" name="Ports" radius={[0,4,4,0]}>
                {svcData.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Protocol pie */}
      <div className="chart-card">
        <h4 className="chart-title">Protocol Split</h4>
        {protoData.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart style={CHART_STYLE}>
              <Pie data={protoData} dataKey="value" cx="50%" cy="45%"
                   innerRadius={40} outerRadius={70} paddingAngle={3}>
                {protoData.map((e) => (
                  <Cell key={e.name} fill={PROTO_COLORS[e.name.toLowerCase()] || "#58a6ff"} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend content={<DarkLegend />} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Web Charts
// ─────────────────────────────────────────────────────────────────────────────
export function WebCharts({ data }) {
  if (!data) return null;
  const findings = data.findings || [];
  if (!findings.length) return null;

  // Finding types bar
  const typeMap = {};
  findings.forEach((f) => {
    const t = f.type || "Unknown";
    typeMap[t] = (typeMap[t] || 0) + 1;
  });
  const typeData = Object.entries(typeMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  // Severity pie
  const sevMap = {};
  findings.forEach((f) => {
    const s = (f.severity || "INFO").toUpperCase();
    sevMap[s] = (sevMap[s] || 0) + 1;
  });
  const sevData = Object.entries(sevMap).map(([name, value]) => ({ name, value }));

  return (
    <div className="charts-row">
      {/* Types bar */}
      <div className="chart-card chart-card-wide">
        <h4 className="chart-title">Finding Types</h4>
        <ResponsiveContainer width="100%" height={Math.max(160, typeData.length * 28)}>
          <BarChart data={typeData} layout="vertical" style={CHART_STYLE}
                    margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363d" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <YAxis type="category" dataKey="name" width={110}
                   tick={{ fill: "#c9d1d9", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "#1f6feb22" }} />
            <Bar dataKey="value" name="Count" radius={[0,4,4,0]}>
              {typeData.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Severity pie */}
      <div className="chart-card">
        <h4 className="chart-title">Web Finding Severity</h4>
        {sevData.length === 0 ? <NoData /> : (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart style={CHART_STYLE}>
              <Pie data={sevData} dataKey="value" cx="50%" cy="45%"
                   innerRadius={40} outerRadius={70} paddingAngle={3}>
                {sevData.map((e) => (
                  <Cell key={e.name} fill={SEV_COLORS[e.name] || "#58a6ff"} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend content={<DarkLegend />} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
