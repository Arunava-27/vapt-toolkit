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
- 📄 **Report generation** — structured HTML & JSON output
- ⚡ **Async scanning** — concurrent target processing with asyncio

## 🚀 Quick Start
```bash
git clone https://github.com/Arunava-27/vapt-toolkit
cd vapt-toolkit
pip install -r requirements.txt
python main.py --target example.com --full-scan
```

## 📋 Usage
```bash
# Basic recon
python main.py --target example.com --recon

# Full scan with report
python main.py --target example.com --full-scan --output report.html

# Port scan only
python main.py --target 192.168.1.1 --ports --range 1-1024
```

## 🛠️ Tech Stack
- Python 3.10+, FastAPI, asyncio
- python-nmap, requests, BeautifulSoup4
- Jinja2 (reports), SQLite (cache), Click (CLI)

## ⚠️ Legal Disclaimer
Only use on systems you own or have explicit permission to test.

## 📄 License
MIT License — see [LICENSE](LICENSE)
