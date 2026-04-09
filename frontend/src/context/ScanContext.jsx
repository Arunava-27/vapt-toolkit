import { createContext, useContext, useState, useRef, useEffect, useCallback } from "react";

const ScanContext = createContext(null);

const ALL_MODULES = ["recon", "ports", "cve", "web"];
const getActivatedModules = (cfg) =>
  cfg.full_scan ? ALL_MODULES : ALL_MODULES.filter((m) => cfg[m]);

export function ScanProvider({ children }) {
  const [scanId,           setScanId]           = useState(null);
  const [scanning,         setScanning]         = useState(false);
  const [canResume,        setCanResume]        = useState(false);
  const [log,              setLog]              = useState([]);
  const [results,          setResults]          = useState({});
  const [moduleStatus,     setModuleStatus]     = useState({});
  const [activatedModules, setActivatedModules] = useState([]);
  const [savedProject,     setSavedProject]     = useState(null);
  const [lastConfig,       setLastConfig]       = useState(null);
  const [tick,             setTick]             = useState(0);

  const moduleStartRef = useRef({});
  const moduleEndRef   = useRef({});
  const resultsRef     = useRef({});
  const readerRef      = useRef(null);
  const scanIdRef      = useRef(null);   // updated immediately, not via useEffect
  const stoppedRef     = useRef(false);  // suppresses cancel error logs

  useEffect(() => { resultsRef.current = results; }, [results]);

  // Tick for elapsed timer
  useEffect(() => {
    if (!scanning) return;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [scanning]);

  // ── Event handler ────────────────────────────────────────────────────────
  const handleEvent = useCallback((evt) => {
    const addLog = (msg, type = "progress") =>
      setLog((prev) => [...prev, { message: msg, type }]);

    switch (evt.event) {
      case "progress":
        addLog(`  ↳ ${evt.message}`, "info");
        break;
      case "start":
        addLog(`🚀 Scan started on ${evt.target}`);
        break;
      case "module_start":
        moduleStartRef.current[evt.module] = Date.now();
        setModuleStatus((s) => ({ ...s, [evt.module]: "running" }));
        break;
      case "module_error":
        moduleEndRef.current[evt.module] = Date.now();
        setModuleStatus((s) => ({ ...s, [evt.module]: "error" }));
        addLog(`⚠ ${evt.module} error: ${evt.message}`, "error");
        break;
      case "recon":
        moduleEndRef.current.recon = Date.now();
        setModuleStatus((s) => ({ ...s, recon: "done" }));
        addLog(`✅ Recon done — ${evt.data.subdomains?.length ?? 0} subdomain(s)`, "done");
        setResults((r) => ({ ...r, recon: evt.data }));
        break;
      case "ports":
        moduleEndRef.current.ports = Date.now();
        setModuleStatus((s) => ({ ...s, ports: "done" }));
        addLog(`✅ Port scan done — ${evt.data.open_ports?.length ?? 0} open port(s)`, "done");
        setResults((r) => ({ ...r, ports: evt.data }));
        break;
      case "cve":
        moduleEndRef.current.cve = Date.now();
        setModuleStatus((s) => ({ ...s, cve: "done" }));
        addLog(`✅ CVE done — ${evt.data.total_cves} CVE(s)`, "done");
        setResults((r) => ({ ...r, cve: evt.data }));
        break;
      case "web":
        moduleEndRef.current.web = Date.now();
        setModuleStatus((s) => ({ ...s, web: "done" }));
        addLog(`✅ Web scan done — ${evt.data.total} finding(s)`, "done");
        setResults((r) => ({ ...r, web: evt.data }));
        break;
      case "error":
        addLog(`❌ Error: ${evt.message}`, "error");
        setModuleStatus((s) => {
          const running = Object.entries(s).find(([, v]) => v === "running");
          return running ? { ...s, [running[0]]: "error" } : s;
        });
        break;
      case "stopped":
        addLog("⏹ Scan stopped by server.", "error");
        break;
      case "done":
        addLog("💾 Scan complete — saved to projects!", "done");
        if (evt.project_id) setSavedProject({ id: evt.project_id, name: evt.project_name });
        localStorage.removeItem("vapt-active-scan");
        break;
    }
  }, []);

  // ── Stream reader ────────────────────────────────────────────────────────
  const _connectStream = useCallback(async (sid) => {
    try {
      const res = await fetch(`/api/scan/${sid}/stream`);
      if (!res.ok) { setScanning(false); return; }
      readerRef.current = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await readerRef.current.read();
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
      // Suppress errors caused by intentional reader.cancel() or AbortError
      if (!stoppedRef.current && err.name !== "AbortError") {
        setLog((prev) => [...prev, { message: `Connection error: ${err.message}`, type: "error" }]);
      }
    } finally {
      stoppedRef.current = false;
      setScanning(false);
    }
  }, [handleEvent]);

  // ── Reconnect on mount if a scan was active ──────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem("vapt-active-scan");
    if (!stored) return;
    fetch(`/api/scan/${stored}/status`)
      .then((r) => r.json())
      .then((data) => {
        if (data.status === "running") {
          scanIdRef.current = stored;   // update ref immediately
          setScanId(stored);
          setScanning(true);
          setLog([{ message: "🔄 Reconnecting to active scan…", type: "progress" }]);
          _connectStream(stored);
        } else {
          localStorage.removeItem("vapt-active-scan");
        }
      })
      .catch(() => localStorage.removeItem("vapt-active-scan"));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── startScan ────────────────────────────────────────────────────────────
  const startScan = useCallback(async (cfg) => {
    setLastConfig(cfg);
    const mods = getActivatedModules(cfg);
    setActivatedModules(mods);
    setModuleStatus(Object.fromEntries(mods.map((m) => [m, "pending"])));
    moduleStartRef.current = {};
    moduleEndRef.current   = {};
    setResults({});
    setLog([]);
    setSavedProject(null);
    setCanResume(false);
    setScanning(true);

    try {
      const res = await fetch("/api/scan", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(cfg),
      });
      if (!res.ok) {
        setLog([{ message: `Server error: ${res.status}`, type: "error" }]);
        setScanning(false);
        return;
      }
      const { scan_id } = await res.json();
      scanIdRef.current = scan_id;   // update ref immediately
      setScanId(scan_id);
      localStorage.setItem("vapt-active-scan", scan_id);
      await _connectStream(scan_id);
    } catch (err) {
      setLog([{ message: `Failed to start scan: ${err.message}`, type: "error" }]);
      setScanning(false);
    }
  }, [_connectStream]);

  // ── stopScan ─────────────────────────────────────────────────────────────
  const stopScan = useCallback(async () => {
    stoppedRef.current = true;   // silence stream cancel errors
    const sid = scanIdRef.current;

    // Cancel the stream reader first so _connectStream's finally doesn't race
    if (readerRef.current) {
      try { await readerRef.current.cancel(); } catch { /**/ }
      readerRef.current = null;
    }

    // Tell the backend to cancel its asyncio task
    if (sid) {
      try { await fetch(`/api/scan/${sid}`, { method: "DELETE" }); } catch { /**/ }
    }

    setModuleStatus((s) =>
      Object.fromEntries(Object.entries(s).map(([k, v]) => [k, v === "running" ? "stopped" : v]))
    );
    setScanning(false);
    setCanResume(true);
    setLog((prev) => [...prev, { message: "⏹ Scan stopped.", type: "error" }]);
    localStorage.removeItem("vapt-active-scan");
  }, []);

  // ── resumeScan ───────────────────────────────────────────────────────────
  const resumeScan = useCallback(() => {
    if (!lastConfig) return;
    const mods       = getActivatedModules(lastConfig);
    const incomplete = mods.filter((m) => moduleStatus[m] !== "done");
    if (!incomplete.length) return;
    startScan({
      ...lastConfig,
      full_scan: false,
      recon:  incomplete.includes("recon"),
      ports:  incomplete.includes("ports"),
      cve:    incomplete.includes("cve"),
      web:    incomplete.includes("web"),
      existing_ports: resultsRef.current?.ports?.open_ports || null,
    });
  }, [lastConfig, moduleStatus, startScan]);

  // ── getElapsed ───────────────────────────────────────────────────────────
  const getElapsed = useCallback((mod) => {
    const start = moduleStartRef.current[mod];
    if (!start) return null;
    const end = moduleEndRef.current[mod] || Date.now();
    return Math.floor((end - start) / 1000);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  return (
    <ScanContext.Provider value={{
      scanId, scanning, canResume, log, results, moduleStatus,
      activatedModules, savedProject, setSavedProject,
      startScan, stopScan, resumeScan, getElapsed,
    }}>
      {children}
    </ScanContext.Provider>
  );
}

export const useScan = () => useContext(ScanContext);
