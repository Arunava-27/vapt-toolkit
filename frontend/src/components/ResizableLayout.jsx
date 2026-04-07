import { useState, useRef, useEffect, useCallback } from "react";

const MIN_W = 220;
const MAX_W = 600;
const DEFAULT_W = 300;
const STORAGE_KEY = "vapt-sidebar-width";

export default function ResizableLayout({ sidebar, children }) {
  const [width, setWidth] = useState(() => {
    const saved = parseInt(localStorage.getItem(STORAGE_KEY), 10);
    return saved && saved >= MIN_W && saved <= MAX_W ? saved : DEFAULT_W;
  });
  const dragging = useRef(false);
  const startX   = useRef(0);
  const startW   = useRef(0);

  const onMouseDown = useCallback((e) => {
    dragging.current = true;
    startX.current   = e.clientX;
    startW.current   = width;
    document.body.style.cursor    = "col-resize";
    document.body.style.userSelect = "none";
    e.preventDefault();
  }, [width]);

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      const delta = e.clientX - startX.current;
      const next  = Math.min(MAX_W, Math.max(MIN_W, startW.current + delta));
      setWidth(next);
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor    = "";
      document.body.style.userSelect = "";
      setWidth((w) => { localStorage.setItem(STORAGE_KEY, w); return w; });
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup",   onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup",   onUp);
    };
  }, []);

  const resetWidth = () => {
    setWidth(DEFAULT_W);
    localStorage.setItem(STORAGE_KEY, DEFAULT_W);
  };

  return (
    <div className="layout">
      <aside className="sidebar" style={{ width, minWidth: width, maxWidth: width }}>
        {sidebar}
      </aside>

      <div className="resize-handle" onMouseDown={onMouseDown} onDoubleClick={resetWidth}
           title="Drag to resize · double-click to reset" />

      <main className="main">
        {children}
      </main>
    </div>
  );
}
