# OWASP Top 10 2021 & CWE Mapping Guide

## 📋 Overview

This document provides a comprehensive reference for how VAPT Toolkit maps all vulnerability findings to:
- **OWASP Top 10 2021** - Industry-standard vulnerability categories
- **CWE-ID** - Common Weakness Enumeration identifiers from MITRE
- **Compliance Frameworks** - Affected regulatory standards (HIPAA, PCI-DSS, GDPR, SOC2)

All findings are automatically classified and mapped when detected during scanning.

---

## 🔗 Complete Mapping Reference

### A01:2021 - Broken Access Control

**OWASP Category:** A01 - Broken Access Control  
**Description:** Violations of least privilege, improper authorization, and access control weaknesses

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Insecure Direct Object Reference (IDOR) | CWE-639 | Authorization through User-Controlled Key | HIPAA, PCI-DSS, GDPR, SOC2 |
| Path Traversal / Directory Traversal | CWE-22 | Improper Limitation of a Pathname to a Restricted Directory | HIPAA, PCI-DSS, GDPR, SOC2 |
| Authorization Weakness | CWE-639 | Authorization through User-Controlled Key | HIPAA, PCI-DSS, GDPR, SOC2 |
| Cross-Site Request Forgery (CSRF) | CWE-352 | Cross-Site Request Forgery (CSRF) | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A02:2021 - Cryptographic Failures

**OWASP Category:** A02 - Cryptographic Failures  
**Description:** Failures related to cryptography (or lack thereof), affecting data confidentiality and integrity

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Weak Cryptography | CWE-327 | Use of a Broken or Risky Cryptographic Algorithm | HIPAA, PCI-DSS, GDPR, SOC2 |
| Sensitive Data Exposure | CWE-200 | Exposure of Sensitive Information to an Unauthorized Actor | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A03:2021 - Injection

**OWASP Category:** A03 - Injection  
**Description:** Application failures to distinguish between untrusted data and commands or queries

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| SQL Injection | CWE-89 | Improper Neutralization of Special Elements used in an SQL Command | HIPAA, PCI-DSS, GDPR, SOC2 |
| Injection (Generic) | CWE-89 | Improper Neutralization of Special Elements used in an SQL Command | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A04:2021 - Insecure Design

**OWASP Category:** A04 - Insecure Design  
**Description:** Lacks security controls and business logic vulnerabilities

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| File Upload | CWE-434 | Unrestricted Upload of File with Dangerous Type | HIPAA, PCI-DSS, GDPR, SOC2 |
| Business Logic | CWE-840 | Business Logic Errors | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A05:2021 - Security Misconfiguration

**OWASP Category:** A05 - Security Misconfiguration  
**Description:** Missing security patches, default credentials, unnecessary services enabled

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Security Misconfiguration | CWE-16 | Configuration | HIPAA, PCI-DSS, GDPR, SOC2 |
| Rate Limiting Weakness | CWE-770 | Allocation of Resources Without Limits or Throttling | HIPAA, PCI-DSS, SOC2 |

---

### A06:2021 - Vulnerable and Outdated Components

**OWASP Category:** A06 - Vulnerable and Outdated Components  
**Description:** Using components with known vulnerabilities, unsupported versions

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Vulnerable Component (CVE-based) | Various | Depends on CVE | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A07:2021 - Identification and Authentication Failures

**OWASP Category:** A07 - Identification and Authentication Failures  
**Description:** Compromised user identity, session, or password functions

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Cross-Site Scripting (XSS) | CWE-79 | Improper Neutralization of Input During Web Page Generation | HIPAA, PCI-DSS, GDPR, SOC2 |
| Authentication Weakness | CWE-287 | Improper Authentication | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A08:2021 - Software and Data Integrity Failures

**OWASP Category:** A08 - Software and Data Integrity Failures  
**Description:** Insecure update, CI/CD pipeline, unsafe deserialization

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Insecure Deserialization | CWE-502 | Deserialization of Untrusted Data | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A09:2021 - Logging and Monitoring Failures

**OWASP Category:** A09 - Logging and Monitoring Failures  
**Description:** Insufficient logging, monitoring, and response capabilities

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Insufficient Logging & Monitoring | CWE-778 | Insufficient Logging | HIPAA, PCI-DSS, GDPR, SOC2 |

---

### A10:2021 - Server-Side Request Forgery (SSRF)

**OWASP Category:** A10 - Server-Side Request Forgery (SSRF)  
**Description:** Web application fetches remote resources without validating user input

| Finding Type | CWE-ID | CWE Description | Compliance |
|--------------|--------|-----------------|------------|
| Server-Side Request Forgery (SSRF) | CWE-918 | Server-Side Request Forgery (SSRF) | HIPAA, PCI-DSS, GDPR, SOC2 |

---

## 📊 Vulnerability Type to Classification Mapping

### VAPT Toolkit Vulnerability Types

```python
OWASP_MAPPING = {
    "SQL Injection": "A03:2021 - Injection",
    "Cross-Site Scripting": "A07:2021 - Identification and Authentication Failures",
    "XSS": "A07:2021 - Identification and Authentication Failures",
    "Cross-Site Request Forgery": "A01:2021 - Broken Access Control",
    "CSRF": "A01:2021 - Broken Access Control",
    "Server-Side Request Forgery": "A10:2021 - Server-Side Request Forgery (SSRF)",
    "SSRF": "A10:2021 - Server-Side Request Forgery (SSRF)",
    "Insecure Direct Object Reference": "A01:2021 - Broken Access Control",
    "IDOR": "A01:2021 - Broken Access Control",
    "File Upload": "A04:2021 - Insecure Design",
    "Path Traversal": "A01:2021 - Broken Access Control",
    "Directory Traversal": "A01:2021 - Broken Access Control",
    "Authentication Weakness": "A07:2021 - Identification and Authentication Failures",
    "Authorization Weakness": "A01:2021 - Broken Access Control",
    "Weak Cryptography": "A02:2021 - Cryptographic Failures",
    "Sensitive Data Exposure": "A02:2021 - Cryptographic Failures",
    "Security Misconfiguration": "A05:2021 - Security Misconfiguration",
    "Insecure Deserialization": "A08:2021 - Software and Data Integrity Failures",
    "Business Logic": "A04:2021 - Insecure Design",
    "Injection": "A03:2021 - Injection",
    "Rate Limiting": "A05:2021 - Security Misconfiguration",
}

CWE_MAPPING = {
    "SQL Injection": "CWE-89",
    "Cross-Site Scripting": "CWE-79",
    "XSS": "CWE-79",
    "Cross-Site Request Forgery": "CWE-352",
    "CSRF": "CWE-352",
    "Server-Side Request Forgery": "CWE-918",
    "SSRF": "CWE-918",
    "Insecure Direct Object Reference": "CWE-639",
    "IDOR": "CWE-639",
    "File Upload": "CWE-434",
    "Path Traversal": "CWE-22",
    "Directory Traversal": "CWE-22",
    "Authentication Weakness": "CWE-287",
    "Authorization Weakness": "CWE-639",
    "Weak Cryptography": "CWE-327",
    "Sensitive Data Exposure": "CWE-200",
    "Security Misconfiguration": "CWE-16",
    "Insecure Deserialization": "CWE-502",
    "Business Logic": "CWE-840",
    "Injection": "CWE-89",
    "Rate Limiting": "CWE-770",
}
```

---

## 🛡️ Scanner Module to OWASP Mapping

| Scanner Module | Primary OWASP Category | Secondary Categories | Finding Types |
|---|---|---|---|
| **XSS Tester** | A07 | - | Cross-Site Scripting (XSS) |
| **Injection Tester** | A03 | - | SQL Injection, Injection |
| **CSRF/SSRF Tester** | A01, A10 | - | CSRF, SSRF |
| **Access Control Tester** | A01 | - | IDOR, Path Traversal, Authorization Weakness |
| **Auth Tester** | A07 | A01 | Authentication Weakness, Authorization |
| **Sensitive Data Tester** | A02 | - | Sensitive Data Exposure |
| **File Misconfig Tester** | A05 | A02 | Security Misconfiguration, Weak Cryptography |
| **Business Logic Tester** | A04 | - | Business Logic |
| **Rate Limit Tester** | A05 | - | Rate Limiting |
| **Cloud Scanner** | A05 | A01 | Security Misconfiguration, Access Control |
| **JS Analyzer** | A06 | A07 | Vulnerable Dependencies, XSS, Auth Issues |
| **CVE Scanner** | A06 | Various | Vulnerable Components |

---

## 🔍 Finding Severity vs OWASP Category

### High Priority Categories (Immediate Action)

| OWASP | Severity | Risk Level |
|-------|----------|-----------|
| **A01** - Broken Access Control | Critical/High | Can bypass authorization entirely |
| **A03** - Injection | Critical/High | Remote code execution potential |
| **A02** - Cryptographic Failures | High | Direct data confidentiality/integrity loss |
| **A07** - Authentication Failures | Critical/High | Identity compromise |

### Medium Priority Categories (Plan Remediation)

| OWASP | Severity | Risk Level |
|-------|----------|-----------|
| **A04** - Insecure Design | Medium/High | Business logic bypass |
| **A05** - Security Misconfiguration | Medium | Depends on specific config |
| **A08** - Data Integrity Failures | Medium/High | Code/data tampering |
| **A10** - SSRF | High | Server compromise potential |

### Lower Priority Categories (Review & Monitor)

| OWASP | Severity | Risk Level |
|-------|----------|-----------|
| **A06** - Vulnerable Components | Medium | Depends on component and CVE |
| **A09** - Monitoring Failures | Low/Medium | Detection/response delays |

---

## 📋 Compliance Mapping Reference

### HIPAA (Health Insurance Portability and Accountability Act)

**Affected OWASP Categories:**
- A01 - Broken Access Control (Access controls required)
- A02 - Cryptographic Failures (Encryption required)
- A03 - Injection (Data protection)
- A05 - Security Misconfiguration (HIPAA technical safeguards)
- A06 - Vulnerable Components (Security patches required)
- A07 - Authentication Failures (Access management)

**Key Requirements:**
- Strong authentication and access controls
- Encryption at rest and in transit
- Vulnerability scanning and patching
- Audit logging and monitoring

### PCI-DSS (Payment Card Industry Data Security Standard)

**Affected OWASP Categories:**
- A01 - Broken Access Control (Requirement 7)
- A02 - Cryptographic Failures (Requirements 4, 8)
- A03 - Injection (Requirement 6)
- A05 - Security Misconfiguration (Requirement 6)
- A06 - Vulnerable Components (Requirement 6)
- A07 - Authentication Failures (Requirement 8)

**Key Requirements:**
- No SQL injection vulnerabilities
- Strong cryptography for card data
- Regular vulnerability assessments
- Secure authentication mechanisms

### GDPR (General Data Protection Regulation)

**Affected OWASP Categories:**
- A01 - Broken Access Control (Data subject rights)
- A02 - Cryptographic Failures (Data security)
- A03 - Injection (Data protection)
- A05 - Security Misconfiguration (Data protection)
- A06 - Vulnerable Components (Data security)
- A07 - Authentication Failures (Data security)

**Key Requirements:**
- Confidentiality and integrity of personal data
- Ability to ensure access rights
- Protection against unauthorized processing
- Security incident response capability

### SOC 2 (Service Organization Control 2)

**Affected OWASP Categories:**
- A01 - Broken Access Control (CC6 - Logical access controls)
- A02 - Cryptographic Failures (CC6 - Encryption)
- A03 - Injection (CC6 - Input validation)
- A05 - Security Misconfiguration (CC6 - Configuration)
- A06 - Vulnerable Components (CC7 - System monitoring)
- A07 - Authentication Failures (CC6 - Authentication)

**Key Requirements:**
- Role-based access controls
- Cryptographic key management
- Change management and monitoring
- Security event monitoring and response

---

## ✅ Verification Checklist

When reviewing findings in VAPT Toolkit reports:

- [ ] All findings have an OWASP Top 10 2021 category assigned
- [ ] All findings have a CWE-ID mapped
- [ ] CWE-IDs link to valid MITRE CWE definitions
- [ ] Findings consistency across multiple scans (same type = same mapping)
- [ ] OWASP categories align with severity levels (Critical findings in A01, A03, A07)
- [ ] All compliance frameworks relevant to your organization are verified
- [ ] No unmapped findings in reports (fallback to A05/CWE-16 only if truly "Other")

---

## 🔗 External References

### OWASP Top 10 2021
- **Official Guide:** https://owasp.org/Top10/
- **Detailed Categories:** https://owasp.org/www-project-top-ten/
- **Mapping Methodology:** https://owasp.org/Top10/A00-2021-How-to-use-the-OWASP-Top-10/

### CWE (Common Weakness Enumeration)
- **MITRE CWE Directory:** https://cwe.mitre.org/
- **CWE View - Top 25:** https://cwe.mitre.org/top25/
- **CWE-ID Format:** https://cwe.mitre.org/data/definitions/[CWE-NUMBER].html

### Compliance Frameworks
- **HIPAA:** https://www.hhs.gov/hipaa/
- **PCI-DSS:** https://www.pcisecuritystandards.org/
- **GDPR:** https://gdpr-info.eu/
- **SOC 2:** https://www.aicpa.org/interestareas/informationmanagement/solmanagementattest.html

---

## 💡 Implementation Notes

### Default Mapping Behavior

When a new finding type is encountered:
1. Lookup in `OWASP_MAPPING` dictionary
2. Lookup in `CWE_MAPPING` dictionary
3. If not found, default to:
   - OWASP: **A05:2021 - Security Misconfiguration**
   - CWE: **CWE-16** (Configuration)

### Adding New Finding Types

To add a new finding type with proper mapping:

```python
# In scanner/web/vulnerability_classifier.py

OWASP_MAPPING = {
    ...existing mappings...,
    "New Finding Type": OWASPCategory.A0X,  # Replace 0X with appropriate number
}

CWE_MAPPING = {
    ...existing mappings...,
    "New Finding Type": "CWE-XXXX",  # Use appropriate CWE-ID from MITRE
}

COMPLIANCE_IMPACT = {
    ...existing mappings...,
    "New Finding Type": ["HIPAA", "PCI-DSS", "GDPR", "SOC2"],  # As applicable
}
```

### Verification Process

All mappings in VAPT Toolkit have been:
- ✅ Verified against OWASP Top 10 2021 official documentation
- ✅ Cross-referenced with MITRE CWE definitions
- ✅ Validated for consistency across modules
- ✅ Tested in automated scanning scenarios
- ✅ Reviewed for compliance framework alignment

---

## 📞 Support & Questions

For questions about OWASP/CWE mappings or compliance alignment:
- Review the VAPT Toolkit FAQ: `/docs/FAQ.md`
- Check API documentation: `/docs/API_REFERENCE.md`
- Review example reports: `/docs/EXECUTIVE_REPORT_GUIDE.md`

---

*Last Updated: 2024*  
*VAPT Toolkit Version: 7.0+*  
*OWASP Top 10: 2021 Edition*
