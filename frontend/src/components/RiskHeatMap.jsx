import React, { useState, useEffect, useRef } from "react";
import "../styles/RiskHeatMap.css";

export default function RiskHeatMap({ projectId }) {
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("by_target");
  const [period, setPeriod] = useState("week");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedTarget, setSelectedTarget] = useState("");
  const [targets, setTargets] = useState([]);
  const [tooltip, setTooltip] = useState(null);
  const canvasRef = useRef(null);

  // Load targets list
  useEffect(() => {
    const fetchTargets = async () => {
      try {
        const response = await fetch(`/api/projects/${projectId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.scans && data.scans.length > 0) {
            const uniqueTargets = [...new Set(data.scans.map(s => s.config?.target).filter(Boolean))];
            setTargets(uniqueTargets);
            if (uniqueTargets.length > 0 && !selectedTarget) {
              setSelectedTarget(uniqueTargets[0]);
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch targets:", err);
      }
    };

    if (projectId) {
      fetchTargets();
    }
  }, [projectId, selectedTarget]);

  // Fetch heat map data
  useEffect(() => {
    fetchHeatMap();
  }, [viewMode, period, startDate, endDate, selectedTarget, projectId]);

  const fetchHeatMap = async () => {
    if (!projectId) return;

    setLoading(true);
    setError(null);

    try {
      let url = `/api/reports/heatmap/${viewMode}?projectId=${projectId}`;

      if (viewMode === "by_target" && (startDate || endDate)) {
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
      }

      if (viewMode === "by_time") {
        url += `&period=${period}`;
        if (selectedTarget) url += `&target=${selectedTarget}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch heat map data");

      const data = await response.json();
      setHeatmapData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCellClick = (rowIndex, colIndex) => {
    if (!heatmapData) return;

    const rowData = heatmapData.data?.[rowIndex];
    if (!rowData) return;

    const cell = rowData[colIndex];
    if (cell && cell.count > 0) {
      // Navigate to findings with filter
      const filterParams = {
        ...cell,
        view: viewMode,
      };
      console.log("Cell clicked:", filterParams);
      // Could trigger drill-down modal or navigation here
    }
  };

  const handleMouseEnter = (rowIndex, colIndex, event) => {
    if (!heatmapData) return;

    const rowData = heatmapData.data?.[rowIndex];
    if (!rowData) return;

    const cell = rowData[colIndex];
    if (cell) {
      const rect = event.currentTarget.getBoundingClientRect();
      setTooltip({
        x: rect.left + rect.width / 2,
        y: rect.top - 10,
        ...cell,
      });
    }
  };

  const handleMouseLeave = () => {
    setTooltip(null);
  };

  const handleExportSVG = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const svg = canvas.querySelector("svg");
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `heatmap-${new Date().toISOString().split("T")[0]}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPNG = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const { default: html2canvas } = await import("html2canvas");
      const pngCanvas = await html2canvas(canvas, { backgroundColor: "#ffffff" });
      const link = document.createElement("a");
      link.href = pngCanvas.toDataURL("image/png");
      link.download = `heatmap-${new Date().toISOString().split("T")[0]}.png`;
      link.click();
    } catch (err) {
      alert("Failed to export PNG: " + err.message);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const renderHeatmap = () => {
    if (!heatmapData) return null;

    const { data, severities, targets: heatmapTargets, time_periods } = heatmapData;
    const labels = viewMode === "by_target" ? heatmapTargets : 
                   viewMode === "by_time" ? time_periods :
                   heatmapData.vulnerability_types || [];

    return (
      <div className="heatmap-container">
        <div className="heatmap-labels">
          <div className="severity-labels">
            {(heatmapData.data || []).map((_, rowIndex) => {
              const severity = severities?.[rowIndex] || heatmapData.vulnerability_types?.[rowIndex] || `Row ${rowIndex}`;
              return (
                <div key={rowIndex} className="label">
                  {severity}
                </div>
              );
            })}
          </div>

          <div className="heatmap-grid-wrapper">
            <div className="target-labels">
              {labels.map((label, idx) => (
                <div key={idx} className="label">{label}</div>
              ))}
            </div>

            <div className="heatmap-grid" ref={canvasRef}>
              {data?.map((row, rowIndex) => (
                <div key={rowIndex} className="heatmap-row">
                  {row?.map((cell, colIndex) => {
                    const cellData = cell;
                    const color = cellData?.color || "#eaeaea";
                    const value = cellData?.value || 0;

                    return (
                      <div
                        key={colIndex}
                        className="heatmap-cell"
                        style={{
                          backgroundColor: color,
                          opacity: 0.5 + (value / 100) * 0.5,
                        }}
                        onClick={() => handleCellClick(rowIndex, colIndex)}
                        onMouseEnter={(e) => handleMouseEnter(rowIndex, colIndex, e)}
                        onMouseLeave={handleMouseLeave}
                        title={`${cellData?.count || 0} findings`}
                      >
                        {cellData?.count > 0 && (
                          <span className="cell-count">{cellData.count}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        {tooltip && (
          <div
            className="tooltip"
            style={{
              left: `${tooltip.x}px`,
              top: `${tooltip.y}px`,
            }}
          >
            <div className="tooltip-content">
              {viewMode === "by_target" && (
                <>
                  <strong>{tooltip.target}</strong>
                  <div>{tooltip.severity}</div>
                </>
              )}
              {viewMode === "by_time" && (
                <>
                  <strong>{tooltip.period}</strong>
                  <div>{tooltip.severity}</div>
                </>
              )}
              {viewMode === "by_severity" && (
                <>
                  <strong>{tooltip.severity}</strong>
                </>
              )}
              <div className="tooltip-count">
                {tooltip.count} finding{tooltip.count !== 1 ? "s" : ""}
              </div>
              {tooltip.value !== undefined && (
                <div className="tooltip-risk">Risk: {tooltip.value.toFixed(1)}</div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSeverityDistribution = () => {
    if (!heatmapData || heatmapData.type !== "by_severity") return null;

    const { distribution, percentages, total, risk_score, colors } = heatmapData;

    return (
      <div className="severity-distribution">
        <div className="distribution-stats">
          <div className="stat-box">
            <div className="stat-label">Total Findings</div>
            <div className="stat-value">{total}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Risk Score</div>
            <div className="stat-value risk-score">{risk_score}</div>
          </div>
        </div>

        <div className="distribution-bars">
          {Object.entries(distribution).map(([severity, count]) => (
            <div key={severity} className="distribution-bar">
              <div className="bar-label">{severity}</div>
              <div className="bar-container">
                <div
                  className="bar-fill"
                  style={{
                    width: `${percentages[severity]}%`,
                    backgroundColor: colors[severity],
                  }}
                />
              </div>
              <div className="bar-stats">
                <span>{count}</span>
                <span>({percentages[severity].toFixed(1)}%)</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading && !heatmapData) {
    return <div className="heatmap-loading">Loading heat map...</div>;
  }

  return (
    <div className="risk-heatmap">
      <div className="heatmap-header">
        <h2>Risk Heat Map</h2>
        <div className="header-controls">
          <button
            onClick={handleExportSVG}
            className="btn-secondary"
            title="Export as SVG"
          >
            📥 SVG
          </button>
          <button
            onClick={handleExportPNG}
            className="btn-secondary"
            title="Export as PNG"
          >
            📥 PNG
          </button>
          <button
            onClick={handlePrint}
            className="btn-secondary"
            title="Print"
          >
            🖨️ Print
          </button>
          <button
            onClick={fetchHeatMap}
            disabled={loading}
            className="btn-secondary"
            title="Refresh data"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="heatmap-controls">
        <div className="control-group">
          <label>View Mode:</label>
          <select value={viewMode} onChange={(e) => setViewMode(e.target.value)}>
            <option value="by_target">By Target</option>
            <option value="by_time">By Time Series</option>
            <option value="by_severity">By Severity</option>
            <option value="by_type">By Vulnerability Type</option>
          </select>
        </div>

        {viewMode === "by_target" && (
          <>
            <div className="control-group">
              <label>Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="control-group">
              <label>End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </>
        )}

        {viewMode === "by_time" && (
          <>
            <div className="control-group">
              <label>Period:</label>
              <select value={period} onChange={(e) => setPeriod(e.target.value)}>
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
                <option value="month">Monthly</option>
                <option value="quarter">Quarterly</option>
                <option value="year">Yearly</option>
              </select>
            </div>
            {targets.length > 0 && (
              <div className="control-group">
                <label>Target:</label>
                <select value={selectedTarget} onChange={(e) => setSelectedTarget(e.target.value)}>
                  <option value="">All Targets</option>
                  {targets.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            )}
          </>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {viewMode === "by_severity" ? renderSeverityDistribution() : renderHeatmap()}

      {loading && (
        <div className="heatmap-loading-overlay">
          <div className="spinner"></div>
          <div>Updating heat map...</div>
        </div>
      )}
    </div>
  );
}
