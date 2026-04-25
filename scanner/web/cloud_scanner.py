"""Cloud configuration scanner — AWS, GCP, Azure metadata and bucket detection."""

import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import socket


class CloudConfigScanner:
    """Detect and analyze cloud provider misconfigurations and metadata endpoints."""

    def __init__(self, timeout: int = 5):
        """
        Initialize cloud scanner.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.findings = []

    # ── AWS Detection ──────────────────────────────────────────────────────────

    def check_aws_metadata(self, target: str) -> List[Dict]:
        """
        Detect AWS metadata endpoint (169.254.169.254).
        
        Returns:
            List of findings with endpoint paths and status codes
        """
        findings = []
        metadata_paths = [
            "/latest/meta-data/",
            "/latest/meta-data/instance-id",
            "/latest/meta-data/ami-id",
            "/latest/meta-data/instance-type",
            "/latest/meta-data/security-groups",
            "/latest/meta-data/iam/security-credentials/",
            "/latest/meta-data/iam/security-credentials",
            "/latest/user-data",
        ]

        for path in metadata_paths:
            try:
                url = f"http://169.254.169.254{path}"
                response = self._sync_check_url(url)
                if response and response.get("status_code") in [200, 401]:
                    findings.append({
                        "type": "AWS Metadata Endpoint",
                        "endpoint": url,
                        "status_code": response.get("status_code"),
                        "confidence": "HIGH",
                        "risk": "Allows SSRF attacks to retrieve IAM credentials",
                        "remediation": "Restrict access to 169.254.169.254 via security groups/WAF",
                    })
            except Exception:
                pass

        return findings

    def check_s3_buckets(self, domain: str) -> List[Dict]:
        """
        Enumerate S3 bucket patterns.
        
        Returns:
            List of S3 bucket findings
        """
        findings = []
        bucket_patterns = [
            f"{domain}.s3.amazonaws.com",
            f"{domain}-backup.s3.amazonaws.com",
            f"{domain}-test.s3.amazonaws.com",
            f"{domain}-prod.s3.amazonaws.com",
            f"{domain}-uploads.s3.amazonaws.com",
            f"s3.{domain}.com",
            f"bucket.{domain}.com",
        ]

        for bucket_url in bucket_patterns:
            try:
                response = self._sync_check_url(f"http://{bucket_url}")
                if response and response.get("status_code") == 200:
                    findings.append({
                        "type": "S3 Bucket Enumeration",
                        "bucket": bucket_url,
                        "status_code": 200,
                        "confidence": "MEDIUM",
                        "risk": "Publicly accessible S3 bucket discovered",
                        "remediation": "Enable S3 Block Public Access and review bucket policies",
                    })
                elif response and response.get("status_code") == 403:
                    findings.append({
                        "type": "S3 Bucket Found (Access Denied)",
                        "bucket": bucket_url,
                        "status_code": 403,
                        "confidence": "HIGH",
                        "risk": "Bucket exists but access is restricted",
                        "remediation": "Review bucket policies and ACLs",
                    })
            except Exception:
                pass

        return findings

    def check_aws_endpoints(self, domain: str) -> List[Dict]:
        """
        Detect AWS CloudFront, API Gateway, Lambda, RDS endpoints.
        
        Returns:
            List of AWS endpoint findings
        """
        findings = []
        
        # CloudFront patterns
        cloudfront_pattern = r"d[a-z0-9]+\.cloudfront\.net"
        # API Gateway patterns
        apigw_pattern = r"[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com"
        # Lambda patterns
        lambda_pattern = r"[a-z0-9]+\.lambda\.[a-z0-9-]+\.amazonaws\.com"
        # RDS patterns
        rds_pattern = r"[a-z0-9-]+\.rds\.[a-z0-9-]+\.amazonaws\.com"

        # Check for CloudFront
        if re.search(cloudfront_pattern, domain):
            findings.append({
                "type": "AWS CloudFront Distribution",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "CloudFront distribution detected; check origin security",
                "remediation": "Ensure origin is properly secured and distribution settings are correct",
            })

        # Check for API Gateway
        if re.search(apigw_pattern, domain):
            findings.append({
                "type": "AWS API Gateway",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "API Gateway endpoint discovered; verify authorization controls",
                "remediation": "Implement API key, AWS IAM, or Cognito authentication",
            })

        # Check for Lambda
        if re.search(lambda_pattern, domain):
            findings.append({
                "type": "AWS Lambda Function",
                "endpoint": domain,
                "confidence": "MEDIUM",
                "risk": "Lambda function endpoint identified",
                "remediation": "Review Lambda execution role and resource policies",
            })

        # Check for RDS
        if re.search(rds_pattern, domain):
            findings.append({
                "type": "AWS RDS Database",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Database endpoint exposed; verify network isolation",
                "remediation": "Use security groups and VPC to restrict access",
            })

        return findings

    def check_aws_cloudtrail(self, domain: str) -> List[Dict]:
        """
        Detect publicly exposed CloudTrail logs.
        
        Returns:
            List of CloudTrail exposure findings
        """
        findings = []
        cloudtrail_indicators = [
            "AWSLogs",
            "CloudTrail",
            "cloudtrail",
            "aws-logs",
        ]

        for indicator in cloudtrail_indicators:
            if indicator in domain:
                findings.append({
                    "type": "Potential CloudTrail Logs Exposure",
                    "pattern": indicator,
                    "confidence": "MEDIUM",
                    "risk": "CloudTrail logs may be publicly accessible",
                    "remediation": "Enable S3 Block Public Access and review bucket policies",
                })

        return findings

    # ── GCP Detection ──────────────────────────────────────────────────────────

    def check_gcp_metadata(self) -> List[Dict]:
        """
        Detect Google Cloud metadata service.
        
        Returns:
            List of GCP metadata findings
        """
        findings = []
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/"
        headers = {"Metadata-Flavor": "Google"}

        try:
            response = self._sync_check_url(metadata_url, headers)
            if response and response.get("status_code") == 200:
                findings.append({
                    "type": "GCP Metadata Endpoint",
                    "endpoint": metadata_url,
                    "status_code": 200,
                    "confidence": "HIGH",
                    "risk": "SSRF to GCP metadata exposes service account credentials",
                    "remediation": "Use GCP IAM roles and service account impersonation",
                })
        except Exception:
            pass

        return findings

    def check_gcp_storage(self, domain: str) -> List[Dict]:
        """
        Detect GCP Cloud Storage buckets.
        
        Returns:
            List of GCP storage findings
        """
        findings = []
        gcp_patterns = [
            f"{domain}.storage.googleapis.com",
            f"gs://{domain}",
            f"{domain}-backup.storage.googleapis.com",
            f"{domain}-prod.storage.googleapis.com",
        ]

        for bucket_url in gcp_patterns:
            try:
                response = self._sync_check_url(f"http://{bucket_url}")
                if response and response.get("status_code") in [200, 403]:
                    findings.append({
                        "type": "GCP Cloud Storage Bucket",
                        "bucket": bucket_url,
                        "status_code": response.get("status_code"),
                        "confidence": "HIGH",
                        "risk": "GCS bucket discovered; check public access settings",
                        "remediation": "Use uniform bucket-level access and IAM policies",
                    })
            except Exception:
                pass

        return findings

    def check_gcp_endpoints(self, domain: str) -> List[Dict]:
        """
        Detect GCP Cloud Run, Cloud Functions, Firestore endpoints.
        
        Returns:
            List of GCP endpoint findings
        """
        findings = []

        # Cloud Run pattern
        cloudrun_pattern = r"[a-z0-9]+-[a-z0-9]+\.a\.run\.app"
        # Cloud Functions pattern
        cloudfunc_pattern = r"us-[a-z0-9]+-[a-z0-9]+\.cloudfunctions\.net"
        # Firestore pattern
        firestore_pattern = r"[a-z0-9-]+\.firebaseio\.com"

        if re.search(cloudrun_pattern, domain):
            findings.append({
                "type": "GCP Cloud Run Service",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Cloud Run endpoint discovered; verify authentication",
                "remediation": "Use Cloud Run security policies and IAM for access control",
            })

        if re.search(cloudfunc_pattern, domain):
            findings.append({
                "type": "GCP Cloud Function",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Cloud Function endpoint identified",
                "remediation": "Restrict HTTP access and use IAM authentication",
            })

        if re.search(firestore_pattern, domain):
            findings.append({
                "type": "GCP Firestore Database",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Firestore database exposed; verify security rules",
                "remediation": "Implement strict Firestore security rules",
            })

        return findings

    # ── Azure Detection ────────────────────────────────────────────────────────

    def check_azure_metadata(self) -> List[Dict]:
        """
        Detect Azure metadata endpoint.
        
        Returns:
            List of Azure metadata findings
        """
        findings = []
        metadata_url = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
        headers = {"Metadata": "true"}

        try:
            response = self._sync_check_url(metadata_url, headers)
            if response and response.get("status_code") == 200:
                findings.append({
                    "type": "Azure Metadata Endpoint",
                    "endpoint": metadata_url,
                    "status_code": 200,
                    "confidence": "HIGH",
                    "risk": "SSRF to Azure metadata leaks managed identity tokens",
                    "remediation": "Use Azure AD managed identities and restrict metadata access",
                })
        except Exception:
            pass

        return findings

    def check_azure_storage(self, domain: str) -> List[Dict]:
        """
        Detect Azure Blob Storage, Table Storage endpoints.
        
        Returns:
            List of Azure storage findings
        """
        findings = []
        azure_patterns = [
            f"{domain}.blob.core.windows.net",
            f"{domain}-backup.blob.core.windows.net",
            f"{domain}-prod.blob.core.windows.net",
            f"{domain}.table.core.windows.net",
            f"{domain}.file.core.windows.net",
            f"{domain}.queue.core.windows.net",
        ]

        for storage_url in azure_patterns:
            try:
                response = self._sync_check_url(f"http://{storage_url}")
                if response and response.get("status_code") in [200, 403, 409]:
                    findings.append({
                        "type": "Azure Storage Account",
                        "storage": storage_url,
                        "status_code": response.get("status_code"),
                        "confidence": "HIGH",
                        "risk": "Azure storage endpoint discovered; check access controls",
                        "remediation": "Enable storage account firewall and use managed identities",
                    })
            except Exception:
                pass

        return findings

    def check_azure_endpoints(self, domain: str) -> List[Dict]:
        """
        Detect Azure App Service, Databases, and other endpoints.
        
        Returns:
            List of Azure endpoint findings
        """
        findings = []

        # App Service pattern
        appservice_pattern = r"[a-z0-9-]+\.azurewebsites\.net"
        # Database pattern
        db_pattern = r"[a-z0-9-]+\.(database|postgres|mysql)\.windows\.net"
        # Key Vault pattern
        keyvault_pattern = r"[a-z0-9-]+\.vault\.azure\.net"
        # Application Insights pattern
        appinsights_pattern = r"[a-z0-9-]+\.applicationinsights\.io"

        if re.search(appservice_pattern, domain):
            findings.append({
                "type": "Azure App Service",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "App Service endpoint exposed; verify authentication",
                "remediation": "Enable authentication/authorization and use role-based access",
            })

        if re.search(db_pattern, domain):
            findings.append({
                "type": "Azure Database",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Database endpoint discovered; verify network isolation",
                "remediation": "Use virtual networks and firewall rules",
            })

        if re.search(keyvault_pattern, domain):
            findings.append({
                "type": "Azure Key Vault",
                "endpoint": domain,
                "confidence": "HIGH",
                "risk": "Key Vault endpoint identified; check access policies",
                "remediation": "Use role-based access control (RBAC) for Key Vault",
            })

        if re.search(appinsights_pattern, domain):
            findings.append({
                "type": "Azure Application Insights",
                "endpoint": domain,
                "confidence": "MEDIUM",
                "risk": "Application Insights endpoint exposed",
                "remediation": "Review Application Insights API key permissions",
            })

        return findings

    # ── Firebase Detection ────────────────────────────────────────────────────

    def check_firebase_config(self, domain: str) -> List[Dict]:
        """
        Detect Firebase configuration and misconfigurations.
        
        Returns:
            List of Firebase findings
        """
        findings = []
        
        # Firebase patterns
        firebase_patterns = [
            r"[a-z0-9-]+\.firebaseio\.com",
            r"[a-z0-9-]+\.firebasedatabase\.app",
            r"[a-z0-9-]+\.web\.app",
            r"[a-z0-9-]+\.firebaseapp\.com",
        ]

        for pattern in firebase_patterns:
            if re.search(pattern, domain):
                findings.append({
                    "type": "Firebase Application",
                    "endpoint": domain,
                    "confidence": "HIGH",
                    "risk": "Firebase endpoint discovered; check security rules",
                    "remediation": "Implement proper Firebase security rules and authentication",
                })
                break

        return findings

    # ── Helper Methods ────────────────────────────────────────────────────────

    def _sync_check_url(self, url: str, headers: Optional[Dict] = None) -> Optional[Dict]:
        """
        Synchronously check URL status without actually fetching content.
        Uses socket connections for fast checking.
        
        Returns:
            Dict with status_code or None if unreachable
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc
            port = 80 if parsed.scheme == "http" else 443

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))
            sock.close()

            return {"status_code": 200, "reachable": True}
        except socket.timeout:
            return {"status_code": 408, "reachable": False}
        except socket.gaierror:
            return None
        except Exception:
            return None

    def scan_target(self, target: str) -> Dict:
        """
        Perform comprehensive cloud configuration scan on target.
        
        Args:
            target: Domain or IP to scan
            
        Returns:
            Dict with all findings organized by cloud provider
        """
        results = {
            "target": target,
            "aws": [],
            "gcp": [],
            "azure": [],
            "firebase": [],
            "summary": {},
        }

        # AWS checks
        results["aws"].extend(self.check_aws_metadata(target))
        results["aws"].extend(self.check_s3_buckets(target))
        results["aws"].extend(self.check_aws_endpoints(target))
        results["aws"].extend(self.check_aws_cloudtrail(target))

        # GCP checks
        results["gcp"].extend(self.check_gcp_metadata())
        results["gcp"].extend(self.check_gcp_storage(target))
        results["gcp"].extend(self.check_gcp_endpoints(target))

        # Azure checks
        results["azure"].extend(self.check_azure_metadata())
        results["azure"].extend(self.check_azure_storage(target))
        results["azure"].extend(self.check_azure_endpoints(target))

        # Firebase checks
        results["firebase"].extend(self.check_firebase_config(target))

        # Generate summary
        results["summary"] = {
            "total_findings": sum(len(v) for v in results.values() if isinstance(v, list)),
            "high_risk": sum(
                1 for findings in results.values()
                if isinstance(findings, list)
                for f in findings
                if f.get("confidence") == "HIGH"
            ),
            "medium_risk": sum(
                1 for findings in results.values()
                if isinstance(findings, list)
                for f in findings
                if f.get("confidence") == "MEDIUM"
            ),
        }

        return results
