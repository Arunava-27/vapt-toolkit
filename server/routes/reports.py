"""Report generation and export endpoints."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from database import get_project, list_projects
from scanner.web.scan_comparison import ScanComparator
from scanner.reporters.executive_reporter import ExecutiveReporter
from scanner.reporters.pdf_executive import ExecutivePDFGenerator
from scanner.reporters.heatmap_generator import HeatMapGenerator
from scanner.reporters.export_generator import ExportGenerator, ExportFormat
from scanner.reporters.template_engine import TemplateEngine
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

template_engine = TemplateEngine(db_conn_factory=True)


class ComparisonRequest(BaseModel):
    """Request to compare two scans."""
    scan_id_1: str
    scan_id_2: str
    severity_filter: Optional[list[str]] = None
    finding_types: Optional[list[str]] = None
    confidence_min: Optional[int] = None


# Export Endpoints

@router.get("/exports/scan/{pid}")
async def api_export_scan(
    pid: str,
    format: str = "json",
    include_metadata: bool = True,
    include_evidence: bool = True,
    severity: str = None,
    confidence: str = None,
):
    """Export scan results in various formats."""
    try:
        p = get_project(pid)
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build scan data from latest scan
        scans = p.get("scans", [])
        if not scans:
            raise HTTPException(status_code=404, detail="No scans found for this project")

        latest_scan = scans[-1]
        scan_data = {
            "config": latest_scan.get("config", {}),
            "results": latest_scan.get("results", {}),
            "timestamp": latest_scan.get("timestamp", datetime.now().isoformat()),
        }

        # Create exporter
        exporter = ExportGenerator(scan_data)

        # Validate format
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        # Generate export
        loop = asyncio.get_event_loop()
        exported_data = await loop.run_in_executor(
            None,
            exporter.export,
            export_format,
            include_metadata,
            include_evidence,
            severity,
            confidence,
        )

        # Determine response based on format
        if export_format == ExportFormat.JSON:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="scan-export.json"'},
            )
        elif export_format == ExportFormat.CSV:
            return Response(
                content=exported_data,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="scan-export.csv"'},
            )
        elif export_format == ExportFormat.HTML:
            return Response(
                content=exported_data,
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="scan-export.html"'},
            )
        elif export_format == ExportFormat.MARKDOWN:
            return Response(
                content=exported_data,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="scan-export.md"'},
            )
        elif export_format == ExportFormat.SARIF:
            return Response(
                content=exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="scan-export.sarif.json"'},
            )
        elif export_format == ExportFormat.XLSX:
            return Response(
                content=exported_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="scan-export.xlsx"'},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exports/bulk")
async def api_export_bulk(
    project_ids: list = None,
    format: str = "json",
    include_metadata: bool = True,
):
    """Export multiple scans in specified format."""
    try:
        if not project_ids:
            all_projects = list_projects()
            project_ids = [p["id"] for p in all_projects]

        exports = []
        for pid in project_ids[:50]:
            p = get_project(pid)
            if not p:
                continue

            scans = p.get("scans", [])
            if not scans:
                continue

            latest_scan = scans[-1]
            scan_data = {
                "config": latest_scan.get("config", {}),
                "results": latest_scan.get("results", {}),
                "timestamp": latest_scan.get("timestamp", datetime.now().isoformat()),
            }

            exporter = ExportGenerator(scan_data)
            loop = asyncio.get_event_loop()
            exported = await loop.run_in_executor(
                None,
                exporter.export,
                ExportFormat(format.lower()),
                include_metadata,
                False,
                None,
                None,
            )

            exports.append({
                "project_id": pid,
                "target": p.get("target"),
                "data": exported if format.lower() != "json" else json.loads(exported),
            })

        response_data = {
            "format": format,
            "count": len(exports),
            "exports": exports,
        }

        return Response(
            content=json.dumps(response_data),
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports/templates")
async def api_get_export_templates():
    """Get list of available export templates."""
    return {
        "templates": [
            {
                "format": "json",
                "name": "JSON",
                "description": "Pretty JSON with full details and metadata",
                "use_case": "Data analysis, integration, archival",
            },
            {
                "format": "csv",
                "name": "CSV",
                "description": "Spreadsheet-compatible findings grid",
                "use_case": "Excel, import to other tools",
            },
            {
                "format": "html",
                "name": "HTML",
                "description": "Standalone interactive report",
                "use_case": "Sharing via email, web view",
            },
            {
                "format": "xlsx",
                "name": "Excel",
                "description": "Professional multi-sheet workbook with formatting",
                "use_case": "Professional reports, executive summaries",
            },
            {
                "format": "markdown",
                "name": "Markdown",
                "description": "GitHub and documentation compatible",
                "use_case": "GitHub repositories, wikis, documentation",
            },
            {
                "format": "sarif",
                "name": "SARIF",
                "description": "GitHub Security Alerts format",
                "use_case": "GitHub integration, CI/CD workflows",
            },
        ]
    }


@router.get("/findings/{finding_id}/hints")
async def api_get_finding_hints(finding_id: str):
    """Get manual verification hints for a specific finding."""
    try:
        from scanner.web.verification_hints import VerificationHints
        
        all_projects = list_projects()
        for project in all_projects:
            pid = project["id"]
            p = get_project(pid)
            if not p or not p.get("scans"):
                continue
            
            for scan in p["scans"]:
                results = scan.get("results", {})
                web_vulns = results.get("web_vulnerabilities", {}).get("findings", [])
                
                for finding in web_vulns:
                    if finding.get("finding_id") == finding_id:
                        finding_type = finding.get("type")
                        hints = VerificationHints.get_hints_for_type(finding_type)
                        
                        if hints:
                            return {
                                "finding_id": finding_id,
                                "finding_type": finding_type,
                                "hints": {
                                    "title": hints.title,
                                    "description": hints.description,
                                    "steps": hints.steps,
                                    "tools": hints.tools,
                                    "expected_signs": hints.expected_signs,
                                    "false_positive_indicators": hints.false_positive_indicators
                                }
                            }
        
        raise HTTPException(status_code=404, detail="Finding not found")
    except Exception as e:
        logger.error(f"Error retrieving hints for finding {finding_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hints")


@router.post("/compare/scans")
async def api_compare_scans(body: ComparisonRequest):
    """Compare two scans and return detailed comparison results."""
    project_1 = None
    project_2 = None
    scan_1 = None
    scan_2 = None
    
    all_projects = list_projects()
    for project in all_projects:
        pid = project["id"]
        p = get_project(pid)
        if p and p.get("scans"):
            for scan in p["scans"]:
                if scan.get("scan_id") == body.scan_id_1:
                    project_1 = p
                    scan_1 = scan
                if scan.get("scan_id") == body.scan_id_2:
                    project_2 = p
                    scan_2 = scan
    
    if not scan_1 or not scan_2:
        raise HTTPException(
            status_code=404,
            detail="One or both scans not found"
        )
    
    # Build filters
    filters = {}
    if body.severity_filter:
        filters["severity"] = body.severity_filter
    if body.finding_types:
        filters["finding_types"] = body.finding_types
    if body.confidence_min is not None:
        filters["confidence_min"] = body.confidence_min
    
    # Compare scans
    comparator = ScanComparator()
    comparison_result = comparator.compare_scans(scan_1, scan_2, filters if filters else None)
    
    return comparison_result.to_dict()


# Executive Report Endpoints

@router.get("/reports/executive/{pid}")
async def get_executive_report(pid: str):
    """Get executive summary report data for a project."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_report():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        return reporter.get_summary_data()
    
    loop = asyncio.get_event_loop()
    report_data = await loop.run_in_executor(None, generate_report)
    
    return {
        "project_id": pid,
        "target": project.get("target"),
        "scan_count": len(scans),
        **report_data,
    }


@router.get("/reports/executive/{pid}/html")
async def get_executive_report_html(pid: str):
    """Get executive summary report as HTML."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_html():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        return reporter.generate_html()
    
    loop = asyncio.get_event_loop()
    html_content = await loop.run_in_executor(None, generate_html)
    
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in project.get("target", "report"))
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="executive-{slug}.html"'},
    )


@router.get("/reports/executive/{pid}/pdf")
async def get_executive_report_pdf(pid: str):
    """Get executive summary report as PDF."""
    project = get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    latest_scan = scans[-1]
    scan_result = latest_scan.get("results", {})
    
    def generate_pdf():
        reporter = ExecutiveReporter(scan_result, historical_scans=scans[:-1] if len(scans) > 1 else [])
        report_data = reporter.get_summary_data()
        pdf_generator = ExecutivePDFGenerator(report_data)
        return pdf_generator.generate()
    
    loop = asyncio.get_event_loop()
    pdf_buffer = await loop.run_in_executor(None, generate_pdf)
    
    slug = "".join(c if c.isalnum() or c in "-_." else "-" for c in project.get("target", "report"))
    filename = f"executive-{slug}-{pid[:8]}.pdf"
    
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Heatmap Report Endpoints

@router.get("/reports/heatmap/by-target")
async def get_heatmap_by_target(
    projectId: str,
    start_date: str = None,
    end_date: str = None
):
    """Get heat map data organized by target and severity."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_target(scan_results, start_date, end_date)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@router.get("/reports/heatmap/by-time")
async def get_heatmap_by_time(
    projectId: str,
    target: str = None,
    period: str = "week"
):
    """Get time-series heat map data."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_time(scan_results, target, period)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@router.get("/reports/heatmap/by-severity")
async def get_heatmap_by_severity(projectId: str):
    """Get severity distribution heat map."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    findings = []
    for scan in scans:
        results = scan.get("results", {})
        
        web_vulns = results.get("web_vulnerabilities", {})
        if isinstance(web_vulns, dict):
            findings.extend(web_vulns.get("findings", []))
        
        cve_data = results.get("cve", {})
        for corr in cve_data.get("correlations", []):
            for cve in corr.get("cves", []):
                findings.append({
                    "type": "CVE",
                    "title": cve.get("id", "Unknown"),
                    "severity": cve.get("severity", "Medium"),
                    "description": cve.get("description", ""),
                    "cvss_score": cve.get("cvss_score", 0),
                })
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_severity(findings)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data


@router.get("/reports/heatmap/by-type")
async def get_heatmap_by_type(projectId: str):
    """Get heat map data organized by vulnerability type and severity."""
    project = get_project(projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scans = project.get("scans", [])
    if not scans:
        raise HTTPException(status_code=404, detail="No scans available for this project")
    
    scan_results = [scan.get("results", {}) for scan in scans]
    
    def generate_heatmap():
        generator = HeatMapGenerator()
        return generator.generate_by_vulnerability_type(scan_results)
    
    loop = asyncio.get_event_loop()
    heatmap_data = await loop.run_in_executor(None, generate_heatmap)
    
    return heatmap_data
