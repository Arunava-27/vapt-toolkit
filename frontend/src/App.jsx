import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import "./App.css";
import ScanPage         from "./pages/ScanPage";
import ProjectsPage     from "./pages/ProjectsPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";

function Header() {
  return (
    <header className="header">
      <span style={{ fontSize: "1.3rem" }}>🛡️</span>
      <h1>VAPT Toolkit</h1>
      <span className="version">v1.0.0</span>
      <nav className="nav">
        <NavLink to="/"         end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>New Scan</NavLink>
        <NavLink to="/projects"     className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>🗂 Projects</NavLink>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <Routes>
          <Route path="/"            element={<ScanPage />} />
          <Route path="/projects"    element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
