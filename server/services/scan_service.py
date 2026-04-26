"""Scan execution service with notification and webhook handling."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.cve_scanner import CVEScanner
from scanner.web_scanner import WebScanner
from scanner.web.web_scanner_orchestrator import WebVulnerabilityScanner, WebScanConfiguration
from scanner.scope import validate_scope, get_scope_summary
from scanner.notifications import get_notification_manager
from scanner.webhooks import get_webhook_manager, WebhookEvent
from database import save_project

logger = logging.getLogger(__name__)
notification_manager = get_notification_manager()
webhook_manager = get_webhook_manager()


def _should_send_notification(
    severity: str,
    finding_type: str,
    config: dict
) -> bool:
    """Check if a finding should trigger a notification based on config."""
    severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
    
    # Check severity filter
    if config['severity_filter'] != 'all':
        min_severity = severity_levels.get(config['severity_filter'], 0)
        finding_severity = severity_levels.get(severity.lower(), 0)
        if finding_severity < min_severity:
            return False
    
    # Check finding type filter
    if config['finding_types'] != 'all':
        if finding_type not in config['finding_types']:
            return False
    
    return True


async def _send_notification_for_finding(
    state,
    finding_title: str,
    finding_details: dict,
    severity: str = "high",
    finding_type: str = "finding"
):
    """Send notification for a finding if it matches the config."""
    if not _should_send_notification(severity, finding_type, state.notification_config):
        return
    
    channels = state.notification_config.get('channels', ['desktop'])
    email = state.notification_config.get('email')
    
    await notification_manager.send_finding_notification(
        finding_title=finding_title,
        finding_details=finding_details,
        severity=severity,
        finding_type=finding_type,
        recipient_email=email,
        channels=channels
    )


async def _execute_scan(state):
    """Execute a complete vulnerability scan with all modules."""
    from scanner.scope import validate_scope
    from database import save_project
    
    # Import ScanRequest from server.py or wherever it's defined
    try:
        from server_original import ScanRequest
    except ImportError:
        # Fallback if imports don't work
        class ScanRequest:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
            
            def dict(self):
                return self.__dict__
    
    req = ScanRequest(**state.config)
    results: dict = {}

    def push(event: str, **kwargs):
        state.events.append({"event": event, **kwargs})

    async def push_progress(msg: str):
        push("progress", message=msg)

    try:
        push("start", target=req.target, scan_type=req.scan_classification)
        
        # Trigger webhook for scan start (non-blocking)
        try:
            await asyncio.wait_for(
                webhook_manager.trigger_webhook(
                    WebhookEvent(
                        event_type="scan_started",
                        scan_id=state.scan_id,
                        data={
                            "target": req.target,
                            "scan_type": req.scan_classification,
                        }
                    )
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Webhook trigger timeout for scan {state.scan_id}")
        except Exception as webhook_err:
            logger.warning(f"Webhook trigger failed: {webhook_err}")
        
        # Validate target for active scans
        is_active = req.scan_classification == "active"
        if is_active or req.ports or req.web:
            try:
                if not validate_scope(req.target, req.scope):
                    error_msg = f"Target '{req.target}' is NOT in authorized scope. {get_scope_summary(req.scope or [])}"
                    push("module_error", module="scope", message=error_msg)
                    state.status = "error"
                    raise ValueError(error_msg)
                if req.scope:
                    push("progress", message=f"✓ Target verified in scope. {get_scope_summary(req.scope)}")
            except ValueError as e:
                push("module_error", module="scope", message=str(e))
                state.status = "error"
                raise
        
        # Determine which modules to run based on scan classification
        is_passive = req.scan_classification == "passive"
        is_hybrid = req.scan_classification == "hybrid" or req.full_scan

        if (req.recon or req.full_scan or is_passive or is_hybrid) and state.status != "stopped":
            push("module_start", module="recon")
            try:
                scanner = ReconScanner(req.target, wordlist=req.recon_wordlist)
                results["recon"] = await scanner.run(progress_cb=push_progress)
                push("recon", data=results["recon"])
            except Exception as e:
                push("module_error", module="recon", message=str(e))

        # CONSTRAINT: Passive scans NEVER run port or web scanning
        if is_passive:
            push("progress", message="[PASSIVE SCAN] Skipping port scanning (intrusive). Only OSINT and CVE lookups.")
        
        if (req.ports or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="ports")
            try:
                loop = asyncio.get_event_loop()
                version_detect = req.version_detect or (req.cve or req.full_scan)
                port_scanner = PortScanner(
                    target=req.target,
                    port_range=req.port_range,
                    version_detect=version_detect,
                    scan_type=req.scan_type,
                    os_detect=req.os_detect,
                    script=req.port_script,
                    timing=req.port_timing,
                    skip_ping=req.skip_ping,
                    extra_flags=req.port_extra_flags,
                )
                state.port_scanner = port_scanner
                push("progress", message=f"Launching nmap on {req.target} (range: {req.port_range}, type: {req.scan_type})…")
                results["ports"] = await loop.run_in_executor(None, port_scanner.run)
                state.port_scanner = None
                logger.info(f"[SERVER] Port scan completed for {req.target}, found {len(results['ports'].get('open_ports', []))} ports")
                if state.status == "stopped":
                    push("module_error", module="ports", message="Stopped by user.")
                else:
                    logger.info(f"[SERVER] Pushing 'ports' event with {len(results['ports'].get('open_ports', []))} ports to frontend")
                    push("ports", data=results["ports"])
                    
                    # Send notifications for critical open ports
                    open_ports = results["ports"].get("open_ports", [])
                    for port in open_ports:
                        port_num = port.get("port")
                        service = port.get("service", "unknown")
                        severity = "high" if service in ["ssh", "rdp", "telnet", "ftp"] else "medium"
                        
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"Open Port Detected: {port_num}",
                            finding_details={
                                "port": port_num,
                                "protocol": port.get("protocol", "tcp"),
                                "service": service,
                                "version": port.get("version", "unknown"),
                                "target": req.target,
                            },
                            severity=severity,
                            finding_type="open_port"
                        )
            except Exception as e:
                push("module_error", module="ports", message=str(e))

        open_ports = (
            results.get("ports", {}).get("open_ports")
            or req.existing_ports
            or []
        )

        # CVE scanning works with both port data AND OSINT recon data
        if (req.cve or req.full_scan or is_passive or is_hybrid) and state.status != "stopped":
            push("module_start", module="cve")
            try:
                recon_data = results.get("recon") if is_passive else None
                cve_scanner = CVEScanner(open_ports=open_ports or [], recon_data=recon_data)
                results["cve"] = await cve_scanner.run(progress_cb=push_progress)
                push("cve", data=results["cve"])
                
                # Send notifications for critical CVEs
                cves = results["cve"].get("vulnerabilities", [])
                for cve in cves:
                    severity = cve.get("severity", "medium").lower()
                    if severity in ["critical", "high"]:
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"CVE Found: {cve.get('id', 'Unknown')}",
                            finding_details={
                                "cve_id": cve.get("id", "Unknown"),
                                "severity": severity,
                                "description": cve.get("description", "")[:500],
                                "target": req.target,
                                "cvss_score": cve.get("cvss_score", "N/A"),
                            },
                            severity=severity,
                            finding_type="cve"
                        )
            except Exception as e:
                push("module_error", module="cve", message=str(e))
        elif is_passive and not open_ports:
            push("progress", message="[PASSIVE SCAN] CVE lookup uses public OSINT data only. No direct port scanning.")

        # CONSTRAINT: Passive scans NEVER run web scanning
        if (req.web or req.full_scan) and not is_passive and state.status != "stopped":
            push("module_start", module="web")
            try:
                web_url = req.target
                if not web_url.startswith("http"):
                    http_ports = [p.get("port") for p in open_ports if p.get("proto") == "TCP" and p.get("port") in [80, 8000, 8080, 8009, 8180, 8888, 3000]]
                    if http_ports:
                        web_url = f"http://{req.target}:{http_ports[0]}"
                    else:
                        web_url = f"https://{req.target}"
                
                web_scanner = WebScanner(web_url, depth=req.web_depth)
                results["web"] = await web_scanner.run(progress_cb=push_progress)
                push("web", data=results["web"])
            except Exception as e:
                push("module_error", module="web", message=str(e))
        
        # Comprehensive Web Vulnerability Scanner
        if (req.web_vulnerability_scan or req.full_scan or is_active or is_hybrid) and not is_passive and state.status != "stopped":
            push("module_start", module="web_vulnerabilities")
            try:
                web_url = req.target
                if not web_url.startswith("http"):
                    http_ports = [p.get("port") for p in open_ports if p.get("proto") == "TCP" and p.get("port") in [80, 8000, 8080, 8009, 8180, 8888, 3000]]
                    if http_ports:
                        web_url = f"http://{req.target}:{http_ports[0]}"
                    else:
                        web_url = f"https://{req.target}"
                
                web_config = WebScanConfiguration(
                    target_url=web_url,
                    scope=req.scope,
                    scope_strict=True,
                    override_robots_txt=req.override_robots_txt,
                    verify_ssl=True,
                    request_timeout=10.0,
                    depth=req.web_depth,
                    test_injection=req.web_test_injection,
                    test_xss=req.web_test_xss,
                    test_auth=req.web_test_auth,
                    test_idor=req.web_test_idor,
                    test_csrf_ssrf=req.web_test_csrf_ssrf,
                    test_file_upload=req.web_test_file_upload,
                    test_misconfiguration=req.web_test_misconfiguration,
                    test_sensitive_data=req.web_test_sensitive_data,
                    test_business_logic=req.web_test_business_logic,
                    test_rate_limiting=req.web_test_rate_limiting,
                    max_pages_to_crawl=50,
                    max_payloads_per_param=30,
                    rate_limit_delay=0.1,
                )
                
                push("progress", message="Starting comprehensive web vulnerability scanning (13 modules)...")
                
                loop = asyncio.get_event_loop()
                web_vuln_scanner = WebVulnerabilityScanner(web_config)
                
                async def run_web_scan():
                    return await loop.run_in_executor(None, web_vuln_scanner.run_scan)
                
                web_vuln_results = await run_web_scan()
                results["web_vulnerabilities"] = web_vuln_results
                
                total_findings = web_vuln_results.get("total_findings", 0)
                high_severity = web_vuln_results.get("high_severity_count", 0)
                push("progress", message=f"Web vulnerability scan complete: {total_findings} total findings ({high_severity} high severity)")
                push("web_vulnerabilities", data=web_vuln_results)
                
                # Send notifications for critical web vulnerabilities
                vulnerabilities = web_vuln_results.get("vulnerabilities", [])
                for vuln in vulnerabilities:
                    severity = vuln.get("severity", "medium").lower()
                    if severity in ["critical", "high"]:
                        await _send_notification_for_finding(
                            state,
                            finding_title=f"Web Vulnerability: {vuln.get('type', 'Unknown')}",
                            finding_details={
                                "type": vuln.get("type", "Unknown"),
                                "severity": severity,
                                "description": vuln.get("description", "")[:500],
                                "url": vuln.get("url", ""),
                                "target": req.target,
                            },
                            severity=severity,
                            finding_type="web_vulnerability"
                        )
                
            except Exception as e:
                push("module_error", module="web_vulnerabilities", message=str(e))

        if state.status != "stopped":
            name = (req.project_name or "").strip() or \
                   f"{req.target} — {req.scan_classification.title()} — {datetime.now().strftime('%b %d %H:%M')}"
            pid = save_project(name, req.target, state.config, results)
            state.project_id = pid
            state.project_name = name
            push("done", project_id=pid, project_name=name, scan_type=req.scan_classification)
            state.status = "done"
            
            # Trigger webhook events
            try:
                await asyncio.wait_for(
                    webhook_manager.trigger_webhook(
                        WebhookEvent(
                            event_type="scan_completed",
                            project_id=pid,
                            scan_id=state.scan_id,
                            data={
                                "target": req.target,
                                "scan_type": req.scan_classification,
                                "results_summary": {
                                    "cves": results.get("cve", {}).get("total_cves", 0),
                                    "ports": len(results.get("ports", {}).get("open_ports", [])),
                                    "subdomains": len(results.get("recon", {}).get("subdomains", [])),
                                    "web_vulns": results.get("web_vulnerabilities", {}).get("total_findings", 0),
                                }
                            }
                        )
                    ),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception) as webhook_err:
                logger.warning(f"Failed to trigger completion webhook: {webhook_err}")

    except asyncio.CancelledError:
        state.status = "stopped"
        push("stopped", message="Scan was cancelled.")
    except Exception as e:
        logger.exception(f"Scan execution error for {req.target}: {e}")
        state.status = "error"
        push("error", message=str(e))
        
        # Trigger webhook for scan failure
        try:
            await webhook_manager.trigger_webhook(
                WebhookEvent(
                    event_type="scan_failed",
                    scan_id=state.scan_id,
                    project_id=state.project_id,
                    data={
                        "target": req.target,
                        "error": str(e),
                        "scan_type": req.scan_classification,
                    }
                )
            )
        except Exception as webhook_err:
            logger.warning(f"Failed to trigger webhook: {webhook_err}")
