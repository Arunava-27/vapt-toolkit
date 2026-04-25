import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import "./App.css";
import { ScanProvider, useScan } from "./context/ScanContext";
import DashboardPage    from "./pages/DashboardPage";
import ScanPage         from "./pages/ScanPage";
import ProjectsPage     from "./pages/ProjectsPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";

// Ensure dark mode is applied
document.documentElement.setAttribute('data-theme', 'dark');

function ScanIndicator() {
  const { scanning } = useScan();
  if (!scanning) return null;
  return (
    <span className="scan-indicator">
      <span className="scan-dot" /> Scanning…
    </span>
  );
}

function Header() {
  return (
    <header className="header">
      <span style={{ fontSize: "1.3rem" }}>🛡️</span>
      <h1>VAPT Toolkit</h1>
      <span className="version">v1.0.0</span>
      <ScanIndicator />
      <nav className="nav">
        <NavLink to="/"        end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>📊 Dashboard</NavLink>
        <NavLink to="/scan"        className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>⚡ New Scan</NavLink>
        <NavLink to="/projects"    className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>🗂 Projects</NavLink>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ScanProvider>
        <div className="app">
          <Header />
          <Routes>
            <Route path="/"             element={<DashboardPage />} />
            <Route path="/scan"         element={<ScanPage />} />
            <Route path="/projects"     element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
          </Routes>
        </div>
      </ScanProvider>
    </BrowserRouter>
  );
}
