#!/usr/bin/env python3
"""VAPT Toolkit - Main CLI entry point."""

import click
import asyncio
from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.web_scanner import WebScanner
from scanner.cve_scanner import CVEScanner
from reporter.html_reporter import HTMLReporter

@click.group()
@click.version_option("1.0.0")
def cli():
    """VAPT Toolkit - Automated Vulnerability Assessment & Penetration Testing"""
    pass

@cli.command()
@click.option("--target", "-t", required=True, help="Target domain or IP")
@click.option("--output", "-o", default="report.html", help="Output HTML report path")
@click.option("--json-output", "-j", default=None, help="Also save a JSON report to this path")
@click.option("--full-scan", is_flag=True, help="Run all scan modules")
@click.option("--recon", is_flag=True, help="Subdomain enumeration only")
@click.option("--ports", is_flag=True, help="Port scan only")
@click.option("--web", is_flag=True, help="Web vulnerability probe only")
@click.option("--cve", is_flag=True, help="CVE correlation (requires --ports or --full-scan)")
@click.option("--range", "port_range", default="1-1024", help="Port range (default: 1-1024)")
def scan(target, output, json_output, full_scan, recon, ports, web, cve, port_range):
    """Run VAPT scan against a target."""
    click.echo(f"[*] Starting VAPT scan on: {target}")
    results = {}

    if recon or full_scan:
        click.echo("[*] Running reconnaissance...")
        scanner = ReconScanner(target)
        results["recon"] = asyncio.run(scanner.run())
        found = len(results["recon"]["subdomains"])
        click.echo(f"[+] Found {found} subdomain(s).")

    if ports or full_scan:
        click.echo(f"[*] Scanning ports {port_range}...")
        scanner = PortScanner(target, port_range)
        results["ports"] = scanner.run()
        found = len(results["ports"]["open_ports"])
        click.echo(f"[+] Found {found} open port(s).")

    if (cve or full_scan) and results.get("ports"):
        click.echo("[*] Correlating CVEs via NVD API...")
        cve_scanner = CVEScanner(results["ports"]["open_ports"])
        results["cve"] = asyncio.run(cve_scanner.run())
        click.echo(f"[+] Found {results['cve']['total_cves']} CVE(s).")

    if web or full_scan:
        scheme = "https" if not target.startswith("http") else ""
        url = f"{scheme}://{target}" if scheme else target
        click.echo(f"[*] Probing web vulnerabilities on {url}...")
        scanner = WebScanner(url)
        results["web"] = asyncio.run(scanner.run())
        click.echo(f"[+] Found {results['web']['total']} web finding(s).")

    reporter = HTMLReporter(target, results)
    reporter.generate(output)
    click.echo(f"[+] HTML report saved to: {output}")

    if json_output:
        reporter.generate_json(json_output)
        click.echo(f"[+] JSON report saved to: {json_output}")

if __name__ == "__main__":
    cli()
