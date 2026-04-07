import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import ScanForm from "../components/ScanForm";
import ProgressLog from "../components/ProgressLog";
import ScanStatus from "../components/ScanStatus";
import ResultsDashboard from "../components/ResultsDashboard";

const DEFAULT_CONFIG = {
  target: "", recon: false, ports: false, cve: false, web: false,
  full_scan: false, port_range: "top-1000", version_detect: false, web_depth: 1,
  recon_wordlist: "subdomains-top5000.txt",
};

const ALL_MODULES = ["recon", "ports", "cve", "web"];
const getActivatedModules = (cfg) => cfg.full_scan ? ALL_MODULES : ALL_MODULES.filter((m) => cfg[m]);

export default function ScanPage() {
  const [config, setConfig]               = useState(DEFAULT_CONFIG);
  const [scanning, setScanning]           = useState(false);
  const [canResume, setCanResume]         = useState(false);
  const [log, setLog]                     = useState([]);
  const [results, setResults]             = useState({});
  const [moduleStatus, setModuleStatus]   = useState({});
  const [activatedModules, setActivatedModules] = useState([]);
  const [savedProject, setSavedProject]   = useState(null); // { id, name }

  const moduleStartRef = useRef({});
  const moduleEndRef   = useRef({});
  const [tick, setTick] = useState(0);
  const abortRef       = useRef(null);
  const savedConfigRef = useRef(null);
  const resultsRef     = useRef({});

  useEffect(() => { resultsRef.current = results; }, [results]);
  useEffect(() => {
    if (!scanning) return;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [scanning]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const getElapsed = useCallback((mod) => {
    const start = moduleStartRef.current[mod];
    if (!start) return null;
    const end = moduleEndRef.current[mod] || Date.now();
    return Math.floor((end - start) / 1000);
  }, [tick]);

  const addLog = (message, type = "progress") =>
    setLog((prev) => [...prev, { message, type }]);

  const handleEvent = useCallback((evt) => {
    switch (evt.event) {
      case "start": addLog(`Scan started on ${evt.target}`); break;
      case "module_start":
        moduleStartRef.current[evt.module] = Date.now();
        setModuleStatus((s) => ({ ...s, [evt.module]: "running" }));
        break;
      case "recon":
        moduleEndRef.current.recon = Date.now();
        setModuleStatus((s) => ({ ...s, recon: "done" }));
        addLog(`Recon done — ${evt.data.subdomains.length} subdomain(s)`, "done");
        setResults((r) => ({ ...r, recon: evt.data }));
        break;
      case "ports":
        moduleEndRef.current.ports = Date.now();
        setModuleStatus((s) => ({ ...s, ports: "done" }));
        addLog(`Port scan done — ${evt.data.open_ports.length} open port(s)`, "done");
        setResults((r) => ({ ...r, ports: evt.data }));
        break;
      case "cve":
        moduleEndRef.current.cve = Date.now();
        setModuleStatus((s) => ({ ...s, cve: "done" }));
        addLog(`CVE done — ${evt.data.total_cves} CVE(s)`, "done");
        setResults((r) => ({ ...r, cve: evt.data }));
        break;
      case "web":
        moduleEndRef.current.web = Date.now();
        setModuleStatus((s) => ({ ...s, web: "done" }));
        addLog(`Web scan done — ${evt.data.total} finding(s)`, "done");
        setResults((r) => ({ ...r, web: evt.data }));
        break;
      case "error":
        addLog(`Error: ${evt.message}`, "error");
        setModuleStatus((s) => {
          const running = Object.entries(s).find(([, v]) => v === "running");
          return running ? { ...s, [running[0]]: "error" } : s;
        });
        break;
      case "done":
        addLog("✅ Scan complete — saved to projects!", "done");
        if (evt.project_id) setSavedProject({ id: evt.project_id, name: evt.project_name });
        break;
    }
  }, []);

  const runScan = useCallback(async (scanConfig) => {
    const cfg = scanConfig || config;
    savedConfigRef.current = cfg;
    const mods = getActivatedModules(cfg);
    setActivatedModules(mods);
    setModuleStatus(Object.fromEntries(mods.map((m) => [m, "pending"])));
    moduleStartRef.current = {};
    moduleEndRef.current   = {};
    setScanning(true);
    setCanResume(false);
    setSavedProject(null);
    setLog([]);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cfg),
        signal: controller.signal,
      });
      if (!res.ok) { addLog(`Server error: ${res.status}`, "error"); return; }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          try { handleEvent(JSON.parse(line.slice(5).trim())); } catch { /**/ }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") addLog(`Connection error: ${err.message}`, "error");
    } finally {
      setScanning(false);
    }
  }, [config, handleEvent]);

  const stopScan = () => {
    abortRef.current?.abort();
    setModuleStatus((s) =>
      Object.fromEntries(Object.entries(s).map(([k, v]) => [k, v === "running" ? "stopped" : v]))
    );
    setCanResume(true);
    addLog("⏹ Scan stopped.", "error");
  };

  const resumeScan = () => {
    const cfg = savedConfigRef.current;
    const mods = getActivatedModules(cfg);
    const incomplete = mods.filter((m) => moduleStatus[m] !== "done");
    if (!incomplete.length) return;
    setModuleStatus((s) => {
      const next = { ...s };
      incomplete.forEach((m) => { next[m] = "pending"; });
      return next;
    });
    runScan({
      ...cfg, full_scan: false,
      recon: incomplete.includes("recon"), ports: incomplete.includes("ports"),
      cve: incomplete.includes("cve"),     web: incomplete.includes("web"),
      existing_ports: resultsRef.current?.ports?.open_ports || null,
    });
  };

  const hasResults = Object.keys(results).length > 0;

  return (
    <div className="layout">
      <aside className="sidebar">
        <ScanForm config={config} onChange={setConfig}
          onScan={() => { setResults({}); setSavedProject(null); runScan(); }}
          scanning={scanning} />
      </aside>
      <main className="main">
        {log.length === 0 && !hasResults && (
          <div className="empty">
            <div className="hero">🛡️</div>
            <h2>Ready to scan</h2>
            <p>Enter a target, choose modules, and hit <strong>Run Scan</strong>.</p>
          </div>
        )}

        {savedProject && (
          <div className="save-banner">
            <span>💾 Saved as <strong>{savedProject.name}</strong></span>
            <Link className="save-banner-link" to={`/projects/${savedProject.id}`}>View project →</Link>
            <button className="save-banner-close" onClick={() => setSavedProject(null)}>×</button>
          </div>
        )}

        {(scanning || canResume) && activatedModules.length > 0 && (
          <ScanStatus moduleStatus={moduleStatus} getElapsed={getElapsed}
            activatedModules={activatedModules} onStop={stopScan} onResume={resumeScan}
            scanning={scanning} canResume={canResume} />
        )}

        {log.length > 0 && <ProgressLog entries={log} />}
        <ResultsDashboard results={results} />
      </main>
    </div>
  );
}
