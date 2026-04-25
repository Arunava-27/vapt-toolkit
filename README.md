# 🛡️ VAPT Toolkit

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ed?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

> **Professional-grade Vulnerability Assessment & Penetration Testing automation platform**  
> Streamline reconnaissance, port scanning, web vulnerability probing, CVE correlation, and comprehensive reporting — all in one unified dashboard.

---

## 📖 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Quick Start (3 Steps)](#-quick-start-3-steps)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Architecture](#-architecture)
- [Web Modules](#-web-modules)
- [Phase Enhancements](#-phase-enhancements)
- [Contributing](#-contributing)
- [License](#-license)
- [Documentation Index](#-documentation-index)

---

## 🎯 Project Overview

VAPT Toolkit is a comprehensive vulnerability assessment and penetration testing automation framework designed for security teams, penetration testers, and DevSecOps engineers. It combines powerful reconnaissance capabilities, intelligent vulnerability detection, and professional reporting into a single, easy-to-use platform.

**Built for:**
- 🔒 **Security Teams** — Comprehensive vulnerability assessments at scale
- 🛡️ **Penetration Testers** — Efficient recon & exploitation workflows
- ⚙️ **DevSecOps Engineers** — Integrated security scanning in CI/CD pipelines
- 📊 **Compliance Auditors** — Detailed evidence-based reports

**Key Capabilities:**
- ✅ Full-stack reconnaissance (OSINT + network scanning)
- ✅ Multi-vector vulnerability detection
- ✅ Intelligent CVE correlation & prioritization
- ✅ Professional HTML/PDF/Excel reporting
- ✅ REST API for integration & automation
- ✅ Real-time web-based dashboard

---

## ✨ Features

### Core Scanning Modules (15)

| Module | Capability | Use Case |
|--------|-----------|----------|
| 🔍 **Recon** | Subdomain enumeration, DNS brute-force, passive DNS | Initial reconnaissance |
| 🚪 **Port Scanner** | Nmap integration, service detection, OS fingerprinting | Network mapping |
| 🐛 **CVE Scanner** | NVD API correlation, CVSS scoring, exploit database | Vulnerability assessment |
| 🕸️ **Web Scanner** | SQL Injection, XSS, CSRF, IDOR, XXE, SSRF detection | Web vulnerability testing |
| 🔐 **Auth Tester** | Authentication bypass, session management, MFA testing | Authentication testing |
| 🎯 **API Security** | API endpoint scanning, rate limiting, credential testing | API vulnerability assessment |
| 📁 **File Upload** | Malicious file upload detection, MIME type validation | File handling vulnerabilities |
| 📍 **SSRF Scanner** | Server-side request forgery detection, URL validation | Infrastructure testing |
| 🔄 **Redirect Tester** | Open redirect detection, URL manipulation | Client-side vulnerabilities |
| 💉 **Injection Tester** | SQL, NoSQL, Command, LDAP injection detection | Injection attack testing |
| 📄 **XXE Tester** | XML External Entity attack detection | XML processing vulnerabilities |
| 🗂️ **Path Traversal** | Directory traversal, file access testing | File system security |
| 📋 **Cookie Security** | Cookie flags, encryption, secure transport | Session management |
| 🔒 **Header Analysis** | Security header detection, misconfiguration | HTTP security |
| 📊 **JavaScript Analyzer** | Client-side vulnerability detection, dependency scanning | Frontend security |

### Phase 1-7 Enhancements ✨

| Phase | Enhancement | Status |
|-------|-----------|--------|
| **Phase 1** | Core scanning framework & CLI | ✅ Complete |
| **Phase 2** | FastAPI REST API & dashboard | ✅ Complete |
| **Phase 3** | Scan comparison & heatmap visualization | ✅ Complete |
| **Phase 4** | Bulk scanning API & scheduling | ✅ Complete |
| **Phase 5** | Executive reports & 6-format exports | ✅ Complete |
| **Phase 6** | Manual testing framework & quality assurance | ✅ Complete |
| **Phase 7** | Advanced features (webhooks, CI/CD integration) | ✅ Complete |

**Advanced Features:**
- 🎨 **Theme System** — Dark/light mode with professional styling
- 🔔 **Notifications** — Real-time alerts for scan completion
- 📧 **Webhooks** — Integrate with external systems & automation
- 📅 **Scheduling** — Recurring scans on custom intervals
- 🔗 **Scope Editor** — Visual target management interface
- 📊 **Heatmap Generator** — Vulnerability distribution visualization
- 📈 **Comparison Engine** — Side-by-side scan analysis
- 💾 **Bulk Export** — Multi-format data export (JSON, CSV, XLSX, HTML, MD, SARIF)
- 🔀 **False Positive Patterns** — Smart fingerprinting of false positives
- ✍️ **Verification Hints** — Guided manual verification workflows
- 🤖 **Confidence Scoring** — AI-enhanced finding validation
- 🔗 **GitHub Actions** — CI/CD pipeline integration

---

## 🚀 Quick Start (3 Steps)

### Step 1: Clone & Setup Environment
```bash
git clone https://github.com/Arunava-27/vapt-toolkit.git
cd vapt-toolkit

# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies & Start Backend
```bash
pip install -r requirements.txt
python server.py
# → API running at http://localhost:8000
# → Docs at http://localhost:8000/docs
```

### Step 3: Start Frontend & Open Dashboard
```bash
# In a new terminal
cd frontend
npm install
npm run dev
# → Dashboard at http://localhost:5173
```

**Done!** Open http://localhost:5173 in your browser. Default credentials: `admin` / `admin`

---

## 📦 Installation

### System Requirements

- **Python:** 3.10 or higher
- **Node.js:** 16+ (for frontend)
- **Git:** Latest version
- **OS:** Windows, Linux, macOS

### Option 1: Native Installation

#### Backend Setup
```bash
# Clone repository
git clone https://github.com/Arunava-27/vapt-toolkit.git
cd vapt-toolkit

# Create virtual environment
python -m venv .venv

# Activate (choose one)
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (optional)
cp .env.example .env

# Start server
python server.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Option 2: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Verify services
docker-compose ps

# Access dashboard
# http://localhost:5173 (Frontend)
# http://localhost:8000 (API)
```

See [**DOCKER_IMPLEMENTATION.md**](DOCKER_IMPLEMENTATION.md) for advanced Docker setup.

### Option 3: WSL on Windows (Recommended for Windows Users)

For native Linux tool support (Nmap, SearchSploit):

```powershell
# Enable WSL 2 and install Ubuntu
wsl --install --distribution Ubuntu

# In WSL Ubuntu terminal
sudo apt update && sudo apt install -y python3-pip python3-venv nmap exploitdb
cd /path/to/vapt-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

See [**WSL_INTEGRATION.md**](WSL_INTEGRATION.md) for detailed WSL setup.

---

## 📖 Usage Guide

### Web Dashboard (Recommended)
1. Open http://localhost:5173
2. Create a new project
3. Add targets (domains, IPs, URLs)
4. Select scan type and modules
5. Start scan → Monitor progress → View results
6. Generate report (HTML/PDF/Excel)

### REST API

```bash
# Create scan
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "modules": ["recon", "web"]}'

# List scans
curl http://localhost:8000/api/scans

# Get results
curl http://localhost:8000/api/scans/{scan_id}/results

# Export report
curl http://localhost:8000/api/exports/scan/{scan_id}?format=html > report.html
```

See [**API documentation**](http://localhost:8000/docs) for complete endpoint reference.

### Command-Line Interface (CLI)

```bash
# Full hybrid scan (all modules)
python main.py scan --target example.com --full-scan

# Recon only (passive)
python main.py scan --target example.com --recon

# Port scan only (active)
python main.py scan --target 192.168.1.1 --ports

# Web vulnerability scan (active)
python main.py scan --target example.com --web

# CVE lookup (after port scan)
python main.py scan --target example.com --cve

# Custom output
python main.py scan --target example.com --full-scan \
  --output report.html \
  --json-output results.json \
  --format json
```

### Scan Types

| Type | Scope | Speed | Stealth | Best For |
|------|-------|-------|---------|----------|
| **Passive** | OSINT + DNS only | ⚡⚡⚡ | 🟢 High | Reconnaissance, stealth |
| **Active** | Port + web scanning | ⚡⚡ | 🔴 Low | Comprehensive testing |
| **Hybrid** | All modules | ⚡ | 🟡 Medium | Full assessment |

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VAPT Toolkit                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │   Frontend   │                    │  REST API    │       │
│  │  (React UI)  │◄──────HTTP────────►│  (FastAPI)   │       │
│  └──────────────┘                    └──────────────┘       │
│       :5173                               :8000              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                    Backend Services                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌────────────┐  ┌──────────────┐      │
│  │ Scanning Engine │  │  Reporter  │  │  Scheduler   │      │
│  │                 │  │            │  │              │      │
│  │ • Recon         │  │ • HTML     │  │ • Task Queue │      │
│  │ • Port Scan     │  │ • PDF      │  │ • Cron Jobs  │      │
│  │ • Web Scan      │  │ • Excel    │  │ • Webhooks   │      │
│  │ • CVE Lookup    │  │ • JSON     │  │              │      │
│  │ • Auth Test     │  │ • SARIF    │  │              │      │
│  └─────────────────┘  └────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Integrated Data Layer                       │   │
│  │  SQLite Database | File Storage | Cache Layer        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

External Tools Integration:
├─ Nmap (port scanning)
├─ SearchSploit (exploit lookup)
├─ NVD API (CVE data)
├─ crt.sh (certificate transparency)
└─ HackerTarget API (OSINT)
```

### Module Interaction Flow

```
User Input (UI/API)
       ↓
Scan Orchestrator
       ↓
    ┌──┴──────────────────┬──────────────┐
    ↓                     ↓              ↓
 Recon Module      Port Scanner    Web Scanner
    ↓                     ↓              ↓
 DNS Data          Service List    Vulnerabilities
    ↓                     ↓              ↓
    └──────────┬──────────┴──────────┘
               ↓
        CVE Correlator
               ↓
        Reporter Engine
               ↓
    ┌─────────┬──────────┬────────────┐
    ↓         ↓          ↓            ↓
  HTML      JSON      Excel       PDF
  Report    Data      Workbook    Report
```

---

## 🧩 Web Modules

### Recognition & Enumeration
- **Subdomain Enumeration** — Certificate transparency, DNS brute-force, HackerTarget API
- **DNS Resolution** — Multi-record lookup (A, AAAA, CNAME, MX, NS, TXT)
- **WHOIS Data** — Domain registration & contact information
- **Technology Fingerprinting** — Web framework & CMS detection

### Network Scanning
- **Port Discovery** — Nmap integration with custom port ranges
- **Service Version Detection** — Accurate service identification
- **OS Fingerprinting** — Operating system detection
- **Traceroute Analysis** — Network path visualization

### Vulnerability Detection
- **SQL Injection** — Multiple payload vectors & encoding
- **Cross-Site Scripting (XSS)** — Reflected, stored, DOM-based
- **Cross-Site Request Forgery (CSRF)** — Token validation & bypass
- **Insecure Direct Object References (IDOR)** — ID enumeration
- **Authentication Bypass** — Login mechanism testing
- **Security Headers** — Missing/misconfigured header detection
- **Sensitive Data Exposure** — Information leakage patterns

### Advanced Detection
- **XXE Injection** — XML entity injection vectors
- **Server-Side Request Forgery (SSRF)** — Internal request testing
- **Command Injection** — Shell metacharacter detection
- **Path Traversal** — Directory escape patterns
- **File Upload Flaws** — Malicious file handling
- **Open Redirects** — URL validation bypass
- **JavaScript Vulnerabilities** — Client-side dependency scanning

---

## 📊 Phase Enhancements

### Phase 1: Core Framework ✅
- CLI interface with Click
- Modular scanner architecture
- Basic reporting (HTML, JSON)

### Phase 2: Web Platform ✅
- FastAPI REST API
- React dashboard
- Project & scan management

### Phase 3: Data Analytics ✅
- Scan comparison engine
- Vulnerability heatmap
- Trend analysis

### Phase 4: Enterprise Features ✅
- Bulk scanning API
- Task scheduling (APScheduler)
- Batch operations

### Phase 5: Advanced Reporting ✅
- Executive summary reports
- Multi-format exports (6 formats)
- False positive pattern detection

### Phase 6: Quality Assurance ✅
- Manual testing framework
- Test environment setup (DVWA, WebGoat, Juice Shop)
- Comprehensive test suite
- Defect tracking system

### Phase 7: Integration & Automation ✅
- GitHub Actions integration
- Webhook notifications
- CI/CD pipeline support
- Slack/Teams integration
- Verification hints system
- Confidence scoring

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

### Setting Up Development Environment

```bash
# Fork and clone repository
git clone https://github.com/YOUR_USERNAME/vapt-toolkit.git
cd vapt-toolkit

# Create feature branch
git checkout -b feature/your-feature-name

# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Create changes and test
python -m pytest tests/ -v --cov=scanner
```

### Code Standards

- **Python:** Follow PEP 8, use type hints
- **JavaScript:** Use ESLint config provided
- **Commits:** Clear, descriptive commit messages
- **Tests:** Maintain 80%+ code coverage
- **Documentation:** Update docs for any new features

### Pull Request Process

1. Update `CHANGELOG.md` with changes
2. Add/update tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Update relevant documentation
5. Submit PR with clear description

### Reporting Issues

- **Bugs:** Include reproduction steps, expected vs actual behavior
- **Features:** Describe use case and expected functionality
- **Security:** Email security@example.com instead of opening issue

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details

**You are free to:**
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Sublicense

**Conditions:**
- ⚠️ Include license and copyright notice
- ⚠️ Include list of changes

**Limitations:**
- ❌ Liability — software provided as-is
- ❌ Warranty — no warranties provided

---

## 📚 Documentation Index

### Getting Started
| Document | Purpose |
|----------|---------|
| [**PHASE6_README.md**](PHASE6_README.md) | Manual testing & QA framework |
| [**TEST_ENVIRONMENTS_SETUP.md**](TEST_ENVIRONMENTS_SETUP.md) | Setup vulnerable test apps |
| [**DOCKER_IMPLEMENTATION.md**](DOCKER_IMPLEMENTATION.md) | Docker deployment guide |
| [**WSL_INTEGRATION.md**](WSL_INTEGRATION.md) | Windows WSL setup |

### Feature Guides
| Document | Feature |
|----------|---------|
| [**BULK_SCANNING_API.md**](BULK_SCANNING_API.md) | Bulk scanning endpoint |
| [**SCOPE_EDITOR_README.md**](SCOPE_EDITOR_README.md) | Target scope management |
| [**HEATMAP_QUICK_REFERENCE.md**](HEATMAP_QUICK_REFERENCE.md) | Vulnerability heatmap |
| [**WEBHOOK_GUIDE.md**](WEBHOOK_GUIDE.md) | Webhook integration |
| [**NOTIFICATIONS_GUIDE.md**](NOTIFICATIONS_GUIDE.md) | Real-time notifications |
| [**SCHEDULING_IMPLEMENTATION.md**](SCHEDULING_IMPLEMENTATION.md) | Recurring scans |
| [**GITHUB_ACTIONS_README.md**](GITHUB_ACTIONS_README.md) | CI/CD integration |

### Advanced Topics
| Document | Topic |
|----------|-------|
| [**EXPORTS_GUIDE.md**](EXPORTS_GUIDE.md) | 6-format data export |
| [**FP_PATTERNS_GUIDE.md**](FP_PATTERNS_GUIDE.md) | False positive management |
| [**VERIFICATION_HINTS_GUIDE.md**](VERIFICATION_HINTS_GUIDE.md) | Manual verification workflows |
| [**CONFIDENCE_SCORING_IMPLEMENTATION.md**](CONFIDENCE_SCORING_IMPLEMENTATION.md) | Smart confidence ranking |
| [**JAVASCRIPT_ANALYZER.md**](JAVASCRIPT_ANALYZER.md) | Client-side scanning |
| [**COMPARISON_INTEGRATION_GUIDE.md**](COMPARISON_INTEGRATION_GUIDE.md) | Scan comparison |

### Deployment & Operations
| Document | Purpose |
|----------|---------|
| [**DOCKER_QUICKREF.md**](DOCKER_QUICKREF.md) | Docker quick commands |
| [**README_DOCKER.md**](README_DOCKER.md) | Docker setup details |
| [**GITHUB_ACTIONS_QUICKSTART.md**](GITHUB_ACTIONS_QUICKSTART.md) | GitHub Actions setup |
| [**PERFORMANCE_OPTIMIZATION.md**](PERFORMANCE_OPTIMIZATION.md) | Optimization tips |

### Testing & Quality
| Document | Purpose |
|----------|---------|
| [**MANUAL_TESTING_GUIDE.md**](MANUAL_TESTING_GUIDE.md) | Testing methodology |
| [**MANUAL_TESTING_REPORT.md**](MANUAL_TESTING_REPORT.md) | Test results template |
| [**PHASE6_TESTING_CHECKLIST.md**](PHASE6_TESTING_CHECKLIST.md) | QA checklist |

### Reference & Checklists
| Document | Purpose |
|----------|---------|
| [**IMPLEMENTATION_CHECKLIST.md**](IMPLEMENTATION_CHECKLIST.md) | Feature implementation status |
| [**DELIVERY_SUMMARY.md**](DELIVERY_SUMMARY.md) | Phase summaries |
| [**COMPLIANCE_REPORT.md**](COMPLIANCE_REPORT.md) | Compliance status |

---

## 🔗 Quick Links

- 🌐 **Live Demo:** [https://vapt-toolkit-demo.com](https://vapt-toolkit-demo.com)
- 📖 **Full Documentation:** [https://docs.vapt-toolkit.com](https://docs.vapt-toolkit.com)
- 🐛 **Issue Tracker:** [GitHub Issues](https://github.com/Arunava-27/vapt-toolkit/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Arunava-27/vapt-toolkit/discussions)
- 📧 **Email:** support@vapt-toolkit.com

---

## ⚠️ Legal & Ethical Guidelines

**This toolkit is for authorized security testing only.**

Before using on any system:
- ✅ Obtain written authorization from system owner
- ✅ Comply with all applicable laws and regulations
- ✅ Never test systems you don't own without permission
- ✅ Report findings responsibly to affected parties
- ✅ Use only in authorized professional contexts

**Responsible Disclosure:**
- Do not publicly disclose vulnerabilities before vendor has patched
- Provide reasonable time for remediation (typically 90 days)
- Share findings only with authorized personnel
- Follow your organization's responsible disclosure policy

---

## 🎯 Roadmap

### Upcoming Features (Q1 2024)
- [ ] Machine learning-based false positive reduction
- [ ] Mobile app for scan monitoring
- [ ] Advanced machine learning for vulnerability prioritization
- [ ] Integration with popular SIEM platforms
- [ ] Custom plugin system

### Community Requests (In Progress)
- [ ] Enhanced API rate limiting & caching
- [ ] Additional export formats
- [ ] Multi-language UI support
- [ ] Advanced role-based access control

---

## 🙏 Acknowledgments

Built with ❤️ by the security community.

**Technologies Used:**
- FastAPI — Modern, fast web framework
- React — Interactive UI components
- Nmap — Network scanning
- NVD — Vulnerability data
- And many open-source libraries...

---

**Ready to begin?** See [**Quick Start**](#-quick-start-3-steps) or read the [**Installation Guide**](#-installation).

**Need help?** Check the [**Documentation Index**](#-documentation-index) or open an [issue](https://github.com/Arunava-27/vapt-toolkit/issues).

---

*VAPT Toolkit v7.0 | MIT License | [GitHub](https://github.com/Arunava-27/vapt-toolkit)*
