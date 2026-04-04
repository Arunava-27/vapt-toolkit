#!/usr/bin/env python3
"""VAPT Toolkit - Main CLI entry point."""

import click
import asyncio
from scanner.recon import ReconScanner
from scanner.port_scanner import PortScanner
from scanner.web_scanner import WebScanner
from reporter.html_reporter import HTMLReporter

@click.group()
@click.version_option("1.0.0")
def cli():
    """VAPT Toolkit - Automated Vulnerability Assessment & Penetration Testing"""
    pass

@cli.command()
@click.option("--target", "-t", required=True, help="Target domain or IP")
@click.option("--output", "-o", default="report.html", help="Output report path")
@click.option("--full-scan", is_flag=True, help="Run all scan modules")
@click.option("--recon", is_flag=True, help="Subdomain enumeration only")
@click.option("--ports", is_flag=True, help="Port scan only")
@click.option("--range", "port_range", default="1-1024", help="Port range (default: 1-1024)")
def scan(target, output, full_scan, recon, ports, port_range):
    """Run VAPT scan against a target."""
    click.echo(f"[*] Starting VAPT scan on: {target}")
    results = {}

    if recon or full_scan:
        click.echo("[*] Running reconnaissance...")
        scanner = ReconScanner(target)
        results["recon"] = asyncio.run(scanner.run())

    if ports or full_scan:
        click.echo(f"[*] Scanning ports {port_range}...")
        scanner = PortScanner(target, port_range)
        results["ports"] = scanner.run()

    if full_scan:
        click.echo("[*] Probing web vulnerabilities...")
        scanner = WebScanner(f"https://{target}")
        results["web"] = asyncio.run(scanner.run())

    reporter = HTMLReporter(target, results)
    reporter.generate(output)
    click.echo(f"[+] Report saved to: {output}")

if __name__ == "__main__":
    cli()
