import { useState, useEffect, useRef } from "react";

function fmt(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

export default function WordlistPicker({ value, onChange, disabled }) {
  const [wordlists, setWordlists]     = useState({ available: [], downloadable: [] });
  const [loading, setLoading]         = useState(true);
  const [dlState, setDlState]         = useState({});  // { [name]: { pct, bytes, done, error } }
  const [uploadState, setUploadState] = useState(null);
  const [deleting, setDeleting]       = useState(null);
  const [error, setError]             = useState(null);
  const fileRef = useRef(null);

  const fetchList = () => {
    setLoading(true);
    fetch("/api/wordlists")
      .then((r) => r.json())
      .then((d) => { setWordlists(d); setLoading(false); })
      .catch(() => { setError("Failed to load wordlists"); setLoading(false); });
  };

  useEffect(fetchList, []);

  // If selected file was removed, fall back to first available
  useEffect(() => {
    if (!loading && wordlists.available.length > 0) {
      const names = wordlists.available.map((w) => w.name);
      if (!names.includes(value)) onChange(wordlists.available[0].name);
    }
  }, [loading, wordlists]);

  const handleDownload = async (name) => {
    if (dlState[name]?.downloading) return;
    setDlState((s) => ({ ...s, [name]: { downloading: true, pct: 0, bytes: 0 } }));
    setError(null);

    try {
      const res = await fetch("/api/wordlists/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) {
        const msg = (await res.json()).detail ?? "Download failed";
        throw new Error(msg);
      }

      // Consume SSE stream
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value: chunk } = await reader.read();
        if (done) break;
        buf += decoder.decode(chunk, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();          // keep incomplete tail

        for (const part of parts) {
          const line = part.replace(/^data:\s*/, "");
          if (!line) continue;
          let evt;
          try { evt = JSON.parse(line); } catch { continue; }

          if (evt.error) throw new Error(evt.error);

          if (evt.done) {
            setDlState((s) => ({ ...s, [name]: { downloading: false, done: true, lines: evt.lines } }));
            fetchList();
            onChange(evt.name);
            setTimeout(() => setDlState((s) => { const n = { ...s }; delete n[name]; return n; }), 3000);
            return;
          }

          setDlState((s) => ({ ...s, [name]: { downloading: true, pct: evt.progress, bytes: evt.bytes } }));
        }
      }
    } catch (e) {
      setError(`Download failed: ${e.message}`);
      setDlState((s) => ({ ...s, [name]: { downloading: false, error: true } }));
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadState("uploading");
    setError(null);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch("/api/wordlists/upload", { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json()).detail);
      const info = await r.json();
      fetchList();
      onChange(info.name);
      setUploadState("done");
      setTimeout(() => setUploadState(null), 2500);
    } catch (e) {
      setError(`Upload failed: ${e.message}`);
      setUploadState("error");
    }
    e.target.value = "";
  };

  const handleDelete = async (name) => {
    if (!confirm(`Delete "${name}"?`)) return;
    setDeleting(name);
    try {
      const r = await fetch(`/api/wordlists/${encodeURIComponent(name)}`, { method: "DELETE" });
      if (!r.ok) throw new Error((await r.json()).detail);
      if (value === name) onChange(wordlists.available.find((w) => w.name !== name)?.name ?? "");
      fetchList();
    } catch (e) {
      setError(`Delete failed: ${e.message}`);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="wl-picker">
      <div className="wl-header">
        <span className="settings-label">Subdomain Wordlist</span>
        <div className="wl-actions">
          <button className="wl-btn-sm"
                  onClick={() => fileRef.current?.click()}
                  disabled={disabled || uploadState === "uploading"}>
            {uploadState === "uploading" ? "Uploading…"
              : uploadState === "done" ? "✓ Uploaded"
              : "📎 Upload"}
          </button>
          <input ref={fileRef} type="file" accept=".txt"
                 style={{ display: "none" }} onChange={handleUpload} />
          <button className="wl-btn-sm" onClick={fetchList}
                  disabled={loading || disabled} title="Refresh">↺</button>
        </div>
      </div>

      {error && <p className="wl-error">{error}</p>}

      {loading ? (
        <p className="wl-loading">Loading wordlists…</p>
      ) : (
        <div className="wl-list">

          {/* ── Available ── */}
          {wordlists.available.map((w) => (
            <div key={w.name}
                 className={`wl-row${value === w.name ? " selected" : ""}`}
                 onClick={() => !disabled && onChange(w.name)}>
              <span className="wl-radio">{value === w.name ? "◉" : "○"}</span>
              <span className="wl-name">{w.name}</span>
              <span className="wl-meta">{w.lines.toLocaleString()} words · {w.size_kb} KB</span>
              {w.name !== "subdomains-ctf.txt" && (
                <button className="wl-del" title="Delete"
                        disabled={disabled || deleting === w.name}
                        onClick={(e) => { e.stopPropagation(); handleDelete(w.name); }}>
                  {deleting === w.name ? "…" : "🗑"}
                </button>
              )}
            </div>
          ))}

          {/* ── Downloadable ── */}
          {wordlists.downloadable.length > 0 && (
            <>
              <div className="wl-divider">Click to download</div>
              {wordlists.downloadable.map((d) => {
                const st = dlState[d.name] ?? {};
                const isDownloading = !!st.downloading;
                const isDone        = !!st.done;
                const isErr         = !!st.error;
                const pct           = st.pct ?? 0;
                const unknown       = pct < 0;

                return (
                  <div key={d.name}
                       className={`wl-row wl-row-dl${isDownloading ? " downloading" : ""}${isDone ? " dl-done" : ""}${isErr ? " dl-error" : ""}`}
                       onClick={() => !disabled && !isDownloading && handleDownload(d.name)}
                       title={isDownloading ? "Downloading…" : "Click to download"}>

                    <span className="wl-radio wl-dl-icon">
                      {isDownloading ? "⏳" : isDone ? "✓" : isErr ? "✗" : "⬇"}
                    </span>

                    <div className="wl-dl-info">
                      <span className="wl-name">{d.name}</span>
                      <span className="wl-meta">{d.description}</span>

                      {isDownloading && (
                        <div className="wl-progress-wrap">
                          <div className="wl-progress-bar">
                            <div className="wl-progress-fill"
                                 style={{ width: unknown ? "100%" : `${pct}%`,
                                          animation: unknown ? "wl-indeterminate 1.4s linear infinite" : "none" }} />
                          </div>
                          <span className="wl-progress-label">
                            {unknown ? `${fmt(st.bytes ?? 0)} received…`
                              : `${pct}% · ${fmt(st.bytes ?? 0)}`}
                          </span>
                        </div>
                      )}

                      {isDone && <span className="wl-done-msg">✓ Downloaded — {st.lines?.toLocaleString()} words</span>}
                      {isErr  && <span className="wl-err-msg">Failed — click to retry</span>}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}
