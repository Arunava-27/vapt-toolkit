import ReconResults from "./ReconResults";
import PortResults from "./PortResults";
import CVEResults from "./CVEResults";
import WebResults from "./WebResults";

export default function ResultsDashboard({
  results,
  id = "results-content",
  collapsibleTables = false,
}) {
  if (!results || !Object.keys(results).length) return null;
  return (
    <div id={id}>
      <div className="summary-cards">
        <div className="card">
          <div className="num">{results?.recon?.subdomains?.length ?? "—"}</div>
          <div className="lbl">Subdomains</div>
        </div>
        <div className="card">
          <div className="num">{results?.ports?.open_ports?.length ?? "—"}</div>
          <div className="lbl">Open Ports</div>
        </div>
        <div className="card">
          <div className="num">{results?.cve?.total_cves ?? "—"}</div>
          <div className="lbl">CVEs</div>
        </div>
        <div className="card">
          <div className="num">{results?.web?.total ?? "—"}</div>
          <div className="lbl">Web Findings</div>
        </div>
      </div>
      <ReconResults data={results.recon} collapsibleTables={collapsibleTables} />
      <PortResults  data={results.ports} collapsibleTables={collapsibleTables} />
      <CVEResults   data={results.cve} collapsibleTables={collapsibleTables} />
      <WebResults   data={results.web} collapsibleTables={collapsibleTables} />
    </div>
  );
}
