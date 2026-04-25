"""
SARIF v2.1.0 Reporter for GitHub Actions Code Scanning Integration
Converts VAPT findings to GitHub-compatible SARIF format for security tab display.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4


class VAPTSarifReporter:
    """
    Generates SARIF v2.1.0 formatted reports compatible with GitHub Actions.
    Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
    """

    # Severity mapping: VAPT -> SARIF
    SEVERITY_MAP = {
        'critical': 'error',
        'high': 'error',
        'medium': 'warning',
        'low': 'note',
        'info': 'note',
    }

    # SARIF rule levels mapping
    LEVEL_MAP = {
        'critical': 'error',
        'high': 'error',
        'medium': 'warning',
        'low': 'note',
        'info': 'none',
    }

    def __init__(
        self,
        tool_version: str = "1.0.0",
        scan_target: str = "http://localhost:3000",
        organization: str = "VAPT Toolkit",
    ):
        """
        Initialize SARIF reporter.

        Args:
            tool_version: Version of VAPT tool
            scan_target: Target URL that was scanned
            organization: Organization name for tool info
        """
        self.tool_version = tool_version
        self.scan_target = scan_target
        self.organization = organization
        self.run_id = str(uuid4())

    def generate(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert VAPT findings to SARIF format.

        Args:
            findings: List of vulnerability findings from VAPT scanner

        Returns:
            SARIF v2.1.0 compatible dictionary
        """
        results = []

        for idx, finding in enumerate(findings):
            result = self._convert_finding_to_result(finding, idx)
            results.append(result)

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": self._get_tool_info(),
                    "invocation": self._get_invocation_info(),
                    "results": results,
                    "properties": {
                        "scanTarget": self.scan_target,
                        "generatedAt": datetime.utcnow().isoformat() + "Z",
                    },
                }
            ],
        }

    def _get_tool_info(self) -> Dict[str, Any]:
        """Get SARIF tool information."""
        return {
            "driver": {
                "name": "VAPT Toolkit",
                "version": self.tool_version,
                "organization": self.organization,
                "informationUri": "https://github.com/yourusername/vapt-toolkit",
                "semanticVersion": self.tool_version,
                "dottedQuadFileVersion": f"{self.tool_version}.0",
                "rules": self._get_rules(),
            }
        }

    def _get_rules(self) -> List[Dict[str, Any]]:
        """Get rule definitions for all vulnerability types."""
        return [
            {
                "id": "VAPT-SQL-INJECTION",
                "name": "SQL Injection",
                "shortDescription": {
                    "text": "SQL Injection vulnerability detected"
                },
                "fullDescription": {
                    "text": "A SQL injection vulnerability allows attackers to interfere with database queries, "
                            "potentially leading to unauthorized data access, manipulation, or deletion."
                },
                "help": {
                    "text": "SQL Injection is a code injection technique that exploits a security vulnerability "
                            "in the database layer. Inputs should be properly sanitized and parameterized queries used."
                },
                "messageStrings": {
                    "default": {
                        "text": "SQL injection vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-89"],
                    "owasp": ["A03:2021 - Injection"],
                    "tags": ["security", "injection", "database"]
                }
            },
            {
                "id": "VAPT-XSS",
                "name": "Cross-Site Scripting",
                "shortDescription": {
                    "text": "Cross-Site Scripting (XSS) vulnerability detected"
                },
                "fullDescription": {
                    "text": "Cross-Site Scripting (XSS) allows attackers to inject malicious scripts into web pages "
                            "viewed by other users, potentially compromising session cookies and sensitive data."
                },
                "help": {
                    "text": "XSS vulnerabilities arise when user input is reflected or stored without proper encoding. "
                            "Use proper output encoding, content security policies, and input validation."
                },
                "messageStrings": {
                    "default": {
                        "text": "XSS vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-79"],
                    "owasp": ["A03:2021 - Injection"],
                    "tags": ["security", "xss", "client-side"]
                }
            },
            {
                "id": "VAPT-CSRF",
                "name": "Cross-Site Request Forgery",
                "shortDescription": {
                    "text": "CSRF vulnerability detected"
                },
                "fullDescription": {
                    "text": "Cross-Site Request Forgery (CSRF) attacks trick authenticated users into performing "
                            "unwanted actions on a different website."
                },
                "help": {
                    "text": "Implement CSRF tokens, use SameSite cookies, validate origin/referer headers, "
                            "and use POST instead of GET for state-changing operations."
                },
                "messageStrings": {
                    "default": {
                        "text": "CSRF vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-352"],
                    "owasp": ["A01:2021 - Broken Access Control"],
                    "tags": ["security", "csrf", "authentication"]
                }
            },
            {
                "id": "VAPT-IDOR",
                "name": "Insecure Direct Object Reference",
                "shortDescription": {
                    "text": "IDOR vulnerability detected"
                },
                "fullDescription": {
                    "text": "IDOR vulnerabilities allow attackers to access unauthorized resources by manipulating "
                            "object identifiers in requests."
                },
                "help": {
                    "text": "Implement proper access controls, verify user permissions before accessing resources, "
                            "and use unpredictable identifiers."
                },
                "messageStrings": {
                    "default": {
                        "text": "IDOR vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-639"],
                    "owasp": ["A01:2021 - Broken Access Control"],
                    "tags": ["security", "authorization", "idor"]
                }
            },
            {
                "id": "VAPT-SSRF",
                "name": "Server-Side Request Forgery",
                "shortDescription": {
                    "text": "SSRF vulnerability detected"
                },
                "fullDescription": {
                    "text": "SSRF vulnerabilities allow attackers to make the server perform requests on their behalf, "
                            "potentially accessing internal resources or performing unauthorized actions."
                },
                "help": {
                    "text": "Validate and sanitize user inputs, implement whitelist-based URL validation, "
                            "and disable unnecessary protocols."
                },
                "messageStrings": {
                    "default": {
                        "text": "SSRF vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-918"],
                    "owasp": ["A10:2021 - Server-Side Request Forgery (SSRF)"],
                    "tags": ["security", "ssrf", "network"]
                }
            },
            {
                "id": "VAPT-AUTH-WEAKNESS",
                "name": "Authentication Weakness",
                "shortDescription": {
                    "text": "Authentication weakness detected"
                },
                "fullDescription": {
                    "text": "Weak authentication mechanisms may allow attackers to bypass authentication or impersonate users."
                },
                "help": {
                    "text": "Implement strong authentication mechanisms, use secure password policies, enable MFA, "
                            "and properly handle session management."
                },
                "messageStrings": {
                    "default": {
                        "text": "Authentication weakness detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-287"],
                    "owasp": ["A07:2021 - Identification and Authentication Failures"],
                    "tags": ["security", "authentication"]
                }
            },
            {
                "id": "VAPT-WEAK-CRYPTO",
                "name": "Weak Cryptography",
                "shortDescription": {
                    "text": "Weak cryptographic algorithm detected"
                },
                "fullDescription": {
                    "text": "Weak or deprecated cryptographic algorithms may be vulnerable to attacks."
                },
                "help": {
                    "text": "Use strong, modern cryptographic algorithms (AES-256, SHA-256+, etc.), "
                            "avoid deprecated algorithms (DES, MD5, SHA-1), and use authenticated encryption."
                },
                "messageStrings": {
                    "default": {
                        "text": "Weak cryptography detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-327"],
                    "owasp": ["A02:2021 - Cryptographic Failures"],
                    "tags": ["security", "cryptography"]
                }
            },
            {
                "id": "VAPT-SECURITY-MISCONFIGURATION",
                "name": "Security Misconfiguration",
                "shortDescription": {
                    "text": "Security misconfiguration detected"
                },
                "fullDescription": {
                    "text": "Improper security configuration can expose sensitive information or allow unauthorized access."
                },
                "help": {
                    "text": "Follow security hardening guidelines, disable unnecessary features, "
                            "use security headers, and regularly audit configurations."
                },
                "messageStrings": {
                    "default": {
                        "text": "Security misconfiguration detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "warning"
                },
                "properties": {
                    "cwe": ["CWE-16"],
                    "owasp": ["A05:2021 - Security Misconfiguration"],
                    "tags": ["security", "misconfiguration", "headers"]
                }
            },
            {
                "id": "VAPT-SENSITIVE-DATA",
                "name": "Sensitive Data Exposure",
                "shortDescription": {
                    "text": "Sensitive data exposure detected"
                },
                "fullDescription": {
                    "text": "Sensitive information such as API keys, passwords, or PII may be exposed in responses."
                },
                "help": {
                    "text": "Encrypt sensitive data in transit and at rest, avoid logging sensitive data, "
                            "use proper access controls, and implement data masking."
                },
                "messageStrings": {
                    "default": {
                        "text": "Sensitive data exposure detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-200"],
                    "owasp": ["A02:2021 - Cryptographic Failures"],
                    "tags": ["security", "data-exposure", "privacy"]
                }
            },
            {
                "id": "VAPT-FILE-UPLOAD",
                "name": "Insecure File Upload",
                "shortDescription": {
                    "text": "Insecure file upload vulnerability detected"
                },
                "fullDescription": {
                    "text": "Improper file upload validation may allow attackers to upload malicious files."
                },
                "help": {
                    "text": "Validate file types and sizes, store uploads outside web root, disable script execution, "
                            "use antivirus scanning, and implement proper access controls."
                },
                "messageStrings": {
                    "default": {
                        "text": "Insecure file upload detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "error"
                },
                "properties": {
                    "cwe": ["CWE-434"],
                    "owasp": ["A04:2021 - Insecure Design"],
                    "tags": ["security", "file-upload"]
                }
            },
            {
                "id": "VAPT-BUSINESS-LOGIC",
                "name": "Business Logic Vulnerability",
                "shortDescription": {
                    "text": "Business logic vulnerability detected"
                },
                "fullDescription": {
                    "text": "Flaws in business logic may allow attackers to abuse application features."
                },
                "help": {
                    "text": "Thoroughly test business logic, implement proper state management, "
                            "validate all workflows, and conduct security reviews."
                },
                "messageStrings": {
                    "default": {
                        "text": "Business logic vulnerability detected at {0}"
                    }
                },
                "defaultConfiguration": {
                    "level": "warning"
                },
                "properties": {
                    "cwe": ["CWE-290"],
                    "owasp": ["A04:2021 - Insecure Design"],
                    "tags": ["security", "business-logic"]
                }
            },
        ]

    def _get_invocation_info(self) -> Dict[str, Any]:
        """Get SARIF invocation information."""
        return {
            "toolExecutionSuccessful": True,
            "startTimeUtc": datetime.utcnow().isoformat() + "Z",
            "endTimeUtc": datetime.utcnow().isoformat() + "Z",
            "properties": {
                "runId": self.run_id,
                "environment": "GitHub Actions CI/CD",
            }
        }

    def _convert_finding_to_result(
        self, finding: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """
        Convert a VAPT finding to SARIF result format.

        Args:
            finding: VAPT finding dictionary
            index: Finding index

        Returns:
            SARIF result format
        """
        severity = finding.get("severity", "medium").lower()
        vuln_type = finding.get("type", "Unknown")
        rule_id = self._get_rule_id(vuln_type)
        level = self.LEVEL_MAP.get(severity, "warning")

        # Build location information
        location = self._build_location(finding)

        # Build message
        message_text = finding.get(
            "message",
            f"{vuln_type} vulnerability detected"
        )

        return {
            "ruleId": rule_id,
            "ruleIndex": 0,
            "kind": "fail",
            "level": level,
            "message": {
                "text": message_text,
                "id": "default"
            },
            "locations": [location],
            "partialFingerprints": {
                "primaryLocationLineHash": f"{vuln_type}_{finding.get('location', 'unknown')}_{index}"
            },
            "properties": {
                "severity": severity,
                "confidence": finding.get("confidence", 0.8),
                "vulnerabilityType": vuln_type,
                "cweId": finding.get("cwe_id", "CWE-16"),
                "owaspCategory": finding.get("owasp_category", "A05:2021"),
                "evidence": finding.get("evidence", ""),
                "parameter": finding.get("parameter", ""),
                "tags": self._get_tags(vuln_type),
            },
            "fixes": self._get_fixes(vuln_type),
        }

    def _build_location(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Build SARIF location object."""
        location_path = finding.get("location", "/")
        parameter = finding.get("parameter", "")

        # Construct readable location message
        location_msg = location_path
        if parameter:
            location_msg = f"{location_path}[{parameter}]"

        return {
            "id": 0,
            "physicalLocation": {
                "address": {
                    "relativeUrl": location_path,
                    "length": len(location_path),
                },
                "region": {
                    "startLine": 1,
                    "snippet": {
                        "text": location_msg
                    }
                }
            },
            "logicalLocations": [
                {
                    "name": location_path,
                    "kind": "uri-based-locator"
                }
            ]
        }

    def _get_rule_id(self, vuln_type: str) -> str:
        """Map vulnerability type to SARIF rule ID."""
        type_map = {
            "SQL Injection": "VAPT-SQL-INJECTION",
            "XSS": "VAPT-XSS",
            "Cross-Site Scripting": "VAPT-XSS",
            "CSRF": "VAPT-CSRF",
            "SSRF": "VAPT-SSRF",
            "IDOR": "VAPT-IDOR",
            "Authentication Weakness": "VAPT-AUTH-WEAKNESS",
            "Weak Cryptography": "VAPT-WEAK-CRYPTO",
            "Weak Security Headers": "VAPT-SECURITY-MISCONFIGURATION",
            "Security Misconfiguration": "VAPT-SECURITY-MISCONFIGURATION",
            "Sensitive Data Exposure": "VAPT-SENSITIVE-DATA",
            "File Upload": "VAPT-FILE-UPLOAD",
            "Business Logic": "VAPT-BUSINESS-LOGIC",
        }
        return type_map.get(vuln_type, "VAPT-SECURITY-MISCONFIGURATION")

    def _get_tags(self, vuln_type: str) -> List[str]:
        """Get tags for vulnerability type."""
        tags = ["security", "vapt", "vulnerability"]

        if "SQL" in vuln_type:
            tags.append("injection")
        if "XSS" in vuln_type:
            tags.append("client-side")
        if "CSRF" in vuln_type:
            tags.append("authentication")
        if "Authentication" in vuln_type:
            tags.append("authentication")
        if "Crypto" in vuln_type:
            tags.append("cryptography")
        if "Header" in vuln_type or "Misconfiguration" in vuln_type:
            tags.append("configuration")

        return tags

    def _get_fixes(self, vuln_type: str) -> List[Dict[str, Any]]:
        """Get recommended fixes for vulnerability type."""
        fixes_map = {
            "SQL Injection": [
                {
                    "description": {
                        "text": "Use parameterized queries and prepared statements"
                    }
                },
                {
                    "description": {
                        "text": "Implement input validation and sanitization"
                    }
                }
            ],
            "XSS": [
                {
                    "description": {
                        "text": "Properly encode all user input in output"
                    }
                },
                {
                    "description": {
                        "text": "Implement Content Security Policy (CSP) headers"
                    }
                }
            ],
            "CSRF": [
                {
                    "description": {
                        "text": "Implement and validate CSRF tokens"
                    }
                },
                {
                    "description": {
                        "text": "Use SameSite cookie attribute"
                    }
                }
            ],
            "IDOR": [
                {
                    "description": {
                        "text": "Verify user permissions before accessing resources"
                    }
                },
                {
                    "description": {
                        "text": "Use unpredictable and indirect object references"
                    }
                }
            ],
        }

        return fixes_map.get(vuln_type, [
            {
                "description": {
                    "text": "Review OWASP security guidelines for this vulnerability type"
                }
            }
        ])


def create_sarif_report(
    findings: List[Dict[str, Any]],
    tool_version: str = "1.0.0",
    scan_target: str = "http://localhost:3000",
) -> Dict[str, Any]:
    """
    Convenience function to create a SARIF report.

    Args:
        findings: List of vulnerability findings
        tool_version: Version of VAPT tool
        scan_target: Target URL that was scanned

    Returns:
        SARIF v2.1.0 formatted dictionary
    """
    reporter = VAPTSarifReporter(
        tool_version=tool_version,
        scan_target=scan_target
    )
    return reporter.generate(findings)
