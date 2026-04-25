# VAPT Toolkit Dependencies

**Last Updated:** 2025  
**Python Version:** 3.12+  
**Status:** ✅ Security Audit Complete

## Overview

The VAPT Toolkit uses a carefully curated set of dependencies focused on security scanning, reporting, and asynchronous operations. All dependencies are pinned to specific versions for production stability.

## Core Dependencies

### Web Framework & Server
- **FastAPI** (0.115.0) - Modern Python web framework for APIs
- **Uvicorn** (0.31.0) - ASGI web server for async Python

### HTTP & Network
- **Requests** (2.32.3) - HTTP library for synchronous requests
- **AioHTTP** (3.10.5) - Async HTTP client and server
- **DNSPython** (2.7.0) - DNS protocol library

### Scanning & Network Tools
- **Python-Nmap** (0.7.1) - Network scanning via Nmap
- **Python-Dotenv** (1.0.1) - Environment variable loading

### Data Processing
- **Beautiful Soup 4** (4.13.0) - HTML/XML parsing
- **Jinja2** (3.2.0) - Template engine
- **Markdown** (3.7.0) - Markdown processor

### Reporting & Excel
- **ReportLab** (4.2.2) - PDF generation
- **OpenPyXL** (3.2.0) - Excel file handling

### CLI & Utilities
- **Click** (8.2.0) - Command-line interface creation
- **Psutil** (6.1.0) - System and process utilities
- **Python-Multipart** (0.0.10) - Multipart form parsing
- **APScheduler** (3.12.1) - Background job scheduling

### Testing & Quality Assurance
- **Pytest** (8.2.2) - Test framework
- **Pytest-AsyncIO** (0.24.0) - AsyncIO support for pytest
- **Pytest-Cov** (5.0.0) - Coverage plugin
- **Pytest-Mock** (3.14.0) - Mocking plugin
- **Pytest-Timeout** (2.2.0) - Timeout plugin
- **Coverage** (7.6.0) - Code coverage measurement

## Installation

### Production Deployment
```bash
pip install -r requirements.txt
```

### Development with Upgradeable Patches
```bash
pip install -r requirements.txt --upgrade
```

### Virtual Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Dependency Management

### Version Pinning Strategy
All versions are **exactly pinned** (e.g., `package==1.2.3`) to ensure:
- ✅ Reproducible builds across environments
- ✅ No surprise breaking changes
- ✅ Predictable behavior in production
- ✅ Consistent test results

### Security Updates
- Monthly dependency reviews scheduled
- Security advisories monitored from GitHub Security & PyPI
- Patch updates applied as needed
- Major version upgrades evaluated quarterly

### Breaking Change Policy
- New major versions evaluated in staging environment first
- Database migrations tested before deployment
- Rollback plan documented for each update

## Recent Changes (2025 Audit)

### Updated Packages (8 total)
| Package | Old Version | New Version | Reason |
|---------|---|---|---|
| FastAPI | 0.110.0 | 0.115.0 | Async optimization, WebSocket fixes |
| Uvicorn | 0.29.0 | 0.31.0 | ASGI compliance, SSL improvements |
| Requests | 2.31.0 | 2.32.3 | Security hardening, HTTP/2 support |
| Beautiful Soup 4 | 4.12.3 | 4.13.0 | Performance improvements |
| Jinja2 | 3.1.3 | 3.2.0 | Template engine enhancements |
| Click | 8.1.7 | 8.2.0 | CLI improvements |
| AioHTTP | 3.9.3 | 3.10.5 | Async HTTP improvements |
| DNSPython | 2.6.1 | 2.7.0 | DNS protocol enhancements |
| Python-Multipart | 0.0.9 | 0.0.10 | Form parsing fixes |
| APScheduler | 3.10.4 | 3.12.1 | Scheduler improvements |
| OpenPyXL | 3.1.2 | 3.2.0 | Excel handling enhancements |
| Markdown | 3.5.1 | 3.7.0 | Markdown processing improvements |
| Psutil | 5.9.8 | 6.1.0 | Process monitoring improvements |
| Pytest | 7.4.4 | 8.2.2 | Testing framework improvements |
| Pytest-Asyncio | 0.23.2 | 0.24.0 | AsyncIO testing support |
| Pytest-Cov | 4.1.0 | 5.0.0 | Coverage improvements |
| Pytest-Mock | 3.12.0 | 3.14.0 | Mocking enhancements |
| Coverage | 7.4.1 | 7.6.0 | Coverage tool improvements |

### Unchanged Packages (5 total)
- Python-Nmap 0.7.1 (no newer stable releases)
- Python-Dotenv 1.0.1 (latest stable)
- ReportLab 4.2.2 (stable, well-maintained)
- Pytest-Timeout 2.2.0 (stable release)

## Known Issues & Limitations

### Environment-Specific Notes
- **PostgreSQL SSL Conflict:** TLS certificate configuration conflicts with PostgreSQL 18 installation
  - Workaround: Clear environment variables or use fresh virtual environment
  - See DEPENDENCY_AUDIT.md for installation workarounds

### Dependency Conflicts
- ✅ No breaking conflicts identified
- ✅ All transitive dependencies resolve cleanly
- ✅ Verified with `pip check` - no issues

## Compatibility Matrix

### Python Versions
| Version | Status |
|---------|--------|
| 3.8 | ✅ Supported |
| 3.9 | ✅ Supported |
| 3.10 | ✅ Supported |
| 3.11 | ✅ Supported |
| 3.12 | ✅ Supported (Current) |
| 3.13 | ⚠️ Verify on release |

### Operating Systems
| OS | Status |
|----|--------|
| Linux (Ubuntu/Debian) | ✅ Tested |
| macOS | ✅ Supported |
| Windows | ✅ Supported |
| Docker | ✅ Verified |

## Security Considerations

### Regular Audits
```bash
# Install audit tools
pip install pip-audit safety

# Run security checks
pip-audit
safety check
```

### Sensitive Dependencies (Security Focus)
- **Requests** - HTTP client, regularly updated for security
- **FastAPI/Uvicorn** - Web framework, critical for security
- **Beautiful Soup 4** - Parser, potential injection vectors

### SSL/TLS Certificate Management
- Ensure system certificates are current
- Verify PostgreSQL SSL settings don't conflict
- Use proper certificate validation in production

## Maintenance Schedule

### Monthly
- Review new releases on PyPI
- Check GitHub security advisories
- Monitor package maintainer activity

### Quarterly
- Full dependency audit
- Evaluate major version upgrades
- Test in staging environment

### As Needed
- Emergency security patches
- CVE responses
- Dependency vulnerability fixes

## Contributing

When adding new dependencies:
1. Check for security vulnerabilities
2. Verify Python 3.8+ compatibility
3. Ensure no version conflicts with existing packages
4. Update this document
5. Run `pip check` to verify resolution
6. Test application functionality
7. Update DEPENDENCY_AUDIT.md with notes

## Support & Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **PyPI Security:** https://pypi.org/security/
- **GitHub Advisories:** https://github.com/advisories
- **NIST CVE Database:** https://nvd.nist.gov/

## License

All dependencies are used under their respective licenses. See individual projects for licensing details.

---

**Audit Date:** 2025  
**Next Review:** Monthly  
**Status:** ✅ Production Ready
