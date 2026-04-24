# 🛡️ VAPT Toolkit

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

A comprehensive **Vulnerability Assessment & Penetration Testing** automation framework. Automates recon, port scanning, CVE correlation, and web vulnerability probing — then generates structured HTML/JSON reports.

## ✨ Features
- 🔍 **Subdomain enumeration** — brute-force + passive DNS
- 🚪 **Port scanning** — Nmap integration with service detection
- 🐛 **CVE correlation** — NVD API lookup for discovered services
- 🕸️ **Web vuln probing** — SQL injection, XSS, open redirect detection
- 📄 **Report generation** — structured HTML, JSON, and PDF output with charts
- ⚡ **Async scanning** — concurrent target processing with asyncio
- 🪟 **Windows + WSL support** — Nmap & SearchSploit via WSL on Windows

## 🚀 Quick Start

### Backend (FastAPI + venv)
```bash
git clone https://github.com/Arunava-27/vapt-toolkit
cd vapt-toolkit

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt

# Start the API server
python server.py               # → http://localhost:8000
```

### Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev                    # → http://localhost:5173
```

Open http://localhost:5173 in your browser.

### 🪟 Windows Users: WSL Setup (Optional but Recommended)
For native Linux tools (Nmap, SearchSploit) on Windows:
```powershell
# Enable WSL 2 and install Ubuntu
wsl --install --distribution Ubuntu

# In WSL Ubuntu terminal:
sudo apt update
sudo apt install -y nmap exploitdb

# Run backend from Windows — tools auto-detected in WSL!
python server.py
```
See [**WSL_INTEGRATION.md**](WSL_INTEGRATION.md) for details.

## 🔍 Scan Types

The toolkit supports three scan classifications to balance speed, stealth, and comprehensiveness:

### 🔍 Passive Scan
- **Only OSINT & public data** — no packet transmission
- ✓ Subdomain enumeration via Certificate Transparency (crt.sh), DNS brute-force, HackerTarget API
- ✓ DNS queries (A, AAAA, CNAME, MX, NS records)
- ✗ **NO port scanning** (Nmap disabled)
- ✗ **NO HTTP probing** (web scanner disabled)
- ✗ **NO direct network packets** sent to target
- Perfect for: **Initial reconnaissance, stealth assessment, compliance**

### ⚡ Active Scan
- **Full reconnaissance** — intrusive network scanning
- ✓ Nmap port scanning with service version detection
- ✓ Web vulnerability probing (SQLi, XSS, Open Redirect)
- ✓ CVE lookup on discovered services
- ✗ Subdomain recon (can use Recon module if needed)
- Perfect for: **Comprehensive pentesting, internal networks, authorized tests**

### 🎯 Hybrid Scan
- **All modules** — maximum coverage
- ✓ Passive recon (OSINT + DNS)
- ✓ Active scanning (ports + web)
- ✓ CVE correlation on all findings
- Perfect for: **Full vulnerability assessment, security research**

## 📋 Usage
```bash
# Subdomain recon only
python main.py scan --target example.com --recon

# Port scan only
python main.py scan --target 192.168.1.1 --ports --range 1-1024

# Web vulnerability probe only
python main.py scan --target example.com --web

# CVE correlation (after port scan)
python main.py scan --target example.com --ports --cve

# Full scan with HTML + JSON reports
python main.py scan --target example.com --full-scan --output report.html --json-output report.json
```

## 🛠️ Tech Stack
- Python 3.10+, FastAPI, asyncio
- python-nmap, requests, BeautifulSoup4
- Jinja2 (reports), SQLite (cache), Click (CLI)

## ⚠️ Legal Disclaimer
Only use on systems you own or have explicit permission to test.

## 📄 License
MIT License — see [LICENSE](LICENSE)
