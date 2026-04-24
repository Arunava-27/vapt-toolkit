export default function CollapsibleTable({
  title,
  countLabel,
  children,
  defaultOpen = true,
}) {
  return (
    <details className="collapsible-table" open={defaultOpen}>
      <summary className="collapsible-table-summary">
        <span className="collapsible-table-arrow" aria-hidden="true">▸</span>
        <span className="collapsible-table-title">{title}</span>
        {countLabel && <span className="collapsible-table-count">{countLabel}</span>}
      </summary>
      <div className="collapsible-table-body">
        {children}
      </div>
    </details>
  );
}
