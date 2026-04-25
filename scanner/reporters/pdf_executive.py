"""PDF Executive Report Generator using ReportLab - Single page professional reports."""

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String
from reportlab.graphics.charts.barcharts import BarChart


# ── Color Palette ────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#1f6feb")
PRIMARY_D = colors.HexColor("#0d419d")
CRITICAL = colors.HexColor("#cf222e")
HIGH = colors.HexColor("#f0883e")
MEDIUM = colors.HexColor("#d29922")
LOW = colors.HexColor("#3fb950")
BG_LIGHT = colors.HexColor("#f6f8fa")
BG_BORDER = colors.HexColor("#d0d7de")
TEXT_PRIMARY = colors.HexColor("#24292f")
TEXT_MUTED = colors.HexColor("#57606a")
WHITE = colors.white


class ExecutivePDFGenerator:
    """Generate single-page executive summary PDF reports."""

    PAGE_W, PAGE_H = letter
    MARGIN = 12 * mm
    CONTENT_W = PAGE_W - 2 * MARGIN

    def __init__(self, executive_data: Dict[str, Any]):
        """
        Initialize PDF generator.

        Args:
            executive_data: Summary data from ExecutiveReporter.get_summary_data()
        """
        self.data = executive_data
        self.styles = self._create_styles()

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles."""
        return {
            "title": ParagraphStyle(
                "title",
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=PRIMARY,
                spaceAfter=8,
                alignment=TA_LEFT,
            ),
            "section_title": ParagraphStyle(
                "section_title",
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=TEXT_PRIMARY,
                spaceBefore=8,
                spaceAfter=6,
                alignment=TA_LEFT,
            ),
            "metric_label": ParagraphStyle(
                "metric_label",
                fontName="Helvetica",
                fontSize=8,
                textColor=TEXT_MUTED,
                alignment=TA_CENTER,
            ),
            "body": ParagraphStyle(
                "body",
                fontName="Helvetica",
                fontSize=9,
                textColor=TEXT_PRIMARY,
                leading=11,
                alignment=TA_LEFT,
            ),
            "small": ParagraphStyle(
                "small",
                fontName="Helvetica",
                fontSize=8,
                textColor=TEXT_PRIMARY,
                leading=10,
                alignment=TA_LEFT,
            ),
            "footer": ParagraphStyle(
                "footer",
                fontName="Helvetica",
                fontSize=7,
                textColor=TEXT_MUTED,
                alignment=TA_CENTER,
            ),
        }

    def _draw_risk_gauge(self, risk_score: int) -> Drawing:
        """Draw risk gauge as circular progress."""
        width, height = 100, 100
        drawing = Drawing(width, height)

        # Background circle
        drawing.add(Circle(width / 2, height / 2, 45, fillColor=BG_LIGHT, strokeColor=BG_BORDER))

        # Determine color based on score
        if risk_score >= 66:
            fill_color = CRITICAL
        elif risk_score >= 33:
            fill_color = HIGH
        else:
            fill_color = LOW

        # Arc (simplified as circle segments)
        drawing.add(Circle(width / 2, height / 2, 40, fillColor=None, strokeColor=fill_color, strokeWidth=8))

        # Center text
        drawing.add(
            String(
                width / 2,
                height / 2 + 5,
                str(risk_score),
                fontSize=24,
                fontName="Helvetica-Bold",
                fillColor=fill_color,
                textAnchor="middle",
            )
        )
        drawing.add(
            String(
                width / 2,
                height / 2 - 8,
                "/ 100",
                fontSize=8,
                fontName="Helvetica",
                fillColor=TEXT_MUTED,
                textAnchor="middle",
            )
        )

        return drawing

    def _get_severity_badge_color(self, severity: str) -> Tuple[colors.Color, colors.Color]:
        """Get text and background colors for severity badge."""
        severity_map = {
            "Critical": (WHITE, CRITICAL),
            "High": (WHITE, HIGH),
            "Medium": (WHITE, MEDIUM),
            "Low": (WHITE, LOW),
        }
        return severity_map.get(severity.lower(), (TEXT_PRIMARY, BG_LIGHT))

    def generate(self) -> BytesIO:
        """Generate PDF and return BytesIO object."""
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=self.MARGIN,
            leftMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN,
            title="Executive Security Summary",
        )

        # Build content
        story = []

        # Header
        risk_score = self.data.get("risk_score", 0)
        risk_level = self.data.get("risk_level", "Unknown")

        header_data = [
            [
                Paragraph("<b>🛡️ Executive Security Summary</b>", self.styles["title"]),
                Paragraph(
                    f"<b>Risk Level:</b> {risk_level}<br/><b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}",
                    self.styles["small"],
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=[self.CONTENT_W * 0.6, self.CONTENT_W * 0.4])
        header_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 6 * mm))

        # Risk Score and Metrics Grid
        metrics = self.data.get("metrics", {})
        metrics_data = [
            [
                Paragraph(f"<b>{risk_score}</b>", self.styles["title"]),
                Paragraph(f"<b>{metrics.get('critical_count', 0)}</b>", self.styles["title"]),
                Paragraph(f"<b>{metrics.get('high_count', 0)}</b>", self.styles["title"]),
                Paragraph(f"<b>{metrics.get('total_findings', 0)}</b>", self.styles["title"]),
            ],
            [
                Paragraph("Risk Score", self.styles["metric_label"]),
                Paragraph("Critical", self.styles["metric_label"]),
                Paragraph("High", self.styles["metric_label"]),
                Paragraph("Total", self.styles["metric_label"]),
            ],
        ]
        metrics_table = Table(metrics_data, colWidths=[self.CONTENT_W / 4] * 4)
        metrics_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                ("TEXTCOLOR", (0, 0), (0, 0), CRITICAL),
                ("TEXTCOLOR", (1, 0), (1, 0), CRITICAL),
                ("TEXTCOLOR", (2, 0), (2, 0), HIGH),
                ("TEXTCOLOR", (3, 0), (3, 0), PRIMARY),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("BORDER", (0, 0), (-1, -1), 1),
                ("BORDERCOLOR", (0, 0), (-1, -1), BG_BORDER),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ])
        )
        story.append(metrics_table)
        story.append(Spacer(1, 8 * mm))

        # Key Findings
        story.append(Paragraph("<b>🔴 Top Critical Findings</b>", self.styles["section_title"]))
        key_findings = self.data.get("key_findings", [])[:5]
        if key_findings:
            findings_data = []
            for idx, finding in enumerate(key_findings, 1):
                severity = finding.get("severity", "Low")
                title = finding.get("title", "Unknown")[:50]
                text_color, bg_color = self._get_severity_badge_color(severity)
                findings_data.append(
                    [
                        Paragraph(f"{idx}. {title}", self.styles["small"]),
                        Paragraph(severity, self.styles["small"]),
                    ]
                )
            findings_table = Table(findings_data, colWidths=[self.CONTENT_W * 0.75, self.CONTENT_W * 0.25])
            findings_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BORDER", (0, 0), (-1, -1), 0.5),
                    ("BORDERCOLOR", (0, 0), (-1, -1), BG_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(findings_table)
        else:
            story.append(Paragraph("No critical findings detected", self.styles["body"]))
        story.append(Spacer(1, 6 * mm))

        # Compliance Status
        story.append(Paragraph("<b>📋 OWASP Top 10 Coverage</b>", self.styles["section_title"]))
        compliance = self.data.get("compliance_status", {})
        if compliance:
            compliance_data = []
            for category, percent in sorted(compliance.items())[:8]:
                cat_short = category.split(":")[0].strip() if ":" in category else category[:8]
                compliance_data.append([Paragraph(cat_short, self.styles["small"]), Paragraph(f"{percent:.0f}%", self.styles["small"])])
            compliance_table = Table(compliance_data, colWidths=[self.CONTENT_W * 0.5, self.CONTENT_W * 0.5])
            compliance_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BORDER", (0, 0), (-1, -1), 0.5),
                    ("BORDERCOLOR", (0, 0), (-1, -1), BG_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(compliance_table)
        else:
            story.append(Paragraph("No OWASP categories detected", self.styles["body"]))
        story.append(Spacer(1, 6 * mm))

        # Remediation Roadmap
        story.append(Paragraph("<b>🔧 Remediation Roadmap</b>", self.styles["section_title"]))
        roadmap = self.data.get("remediation_roadmap", [])[:3]
        if roadmap:
            roadmap_data = []
            for item in roadmap:
                title = item.get("title", "Unknown")[:40]
                severity = item.get("severity", "Low")
                roadmap_data.append([Paragraph(f"• {title}", self.styles["small"]), Paragraph(severity, self.styles["small"])])
            roadmap_table = Table(roadmap_data, colWidths=[self.CONTENT_W * 0.75, self.CONTENT_W * 0.25])
            roadmap_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BORDER", (0, 0), (-1, -1), 0.5),
                    ("BORDERCOLOR", (0, 0), (-1, -1), BG_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 4),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(roadmap_table)
        else:
            story.append(Paragraph("No remediation items available", self.styles["body"]))

        story.append(Spacer(1, 0.1 * inch))

        # Footer
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | VAPT Toolkit", self.styles["footer"]))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
