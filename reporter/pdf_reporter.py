"""Server-side PDF report generator using ReportLab — produces real text-based PDFs."""
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, KeepTogether,
)

# ── Palette ────────────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#1f6feb")
PRIMARY_D = colors.HexColor("#0d419d")
BG_ROW    = colors.HexColor("#f6f8fa")
BORDER    = colors.HexColor("#d0d7de")
TEXT      = colors.HexColor("#24292f")
MUTED     = colors.HexColor("#57606a")
WHITE     = colors.white

SEV_COLORS = {
    "Critical": (colors.HexColor("#cf222e"), colors.HexColor("#FFEBE9")),
    "High":     (colors.HexColor("#bc4c00"), colors.HexColor("#FFF8C5")),
    "HIGH":     (colors.HexColor("#bc4c00"), colors.HexColor("#FFF8C5")),
    "Medium":   (colors.HexColor("#9a6700"), colors.HexColor("#fff3c4")),
    "MEDIUM":   (colors.HexColor("#9a6700"), colors.HexColor("#fff3c4")),
    "Low":      (colors.HexColor("#1a7f37"), colors.HexColor("#DAFBE1")),
    "LOW":      (colors.HexColor("#1a7f37"), colors.HexColor("#DAFBE1")),
}

PAGE_W, PAGE_H = A4
MARGIN    = 15 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
CVE_ROWS_PER_CHUNK = 12


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles():
    return {
        "banner_title": ParagraphStyle("bt", fontName="Helvetica-Bold", fontSize=18,
                                       textColor=WHITE, spaceAfter=3),
        "banner_meta":  ParagraphStyle("bm", fontName="Helvetica", fontSize=8.5,
                                       textColor=colors.HexColor("#c8d3e0"), leading=14),
        "h2":           ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11,
                                       textColor=PRIMARY, spaceBefore=6, spaceAfter=3),
        "sub_head":     ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=8.5,
                                       textColor=TEXT, spaceBefore=4, spaceAfter=2, keepWithNext=1),
        "body":         ParagraphStyle("body", fontName="Helvetica", fontSize=8,
                                       textColor=TEXT, leading=11),
        "code":         ParagraphStyle("code", fontName="Courier", fontSize=7.5,
                                       textColor=TEXT, leading=11),
        "bold":         ParagraphStyle("bold", fontName="Helvetica-Bold", fontSize=8,
                                       textColor=TEXT),
        "muted":        ParagraphStyle("muted", fontName="Helvetica", fontSize=7.5,
                                       textColor=MUTED),
        "stat_num":     ParagraphStyle("sn", fontName="Helvetica-Bold", fontSize=22,
                           textColor=PRIMARY, alignment=TA_CENTER, leading=24, spaceAfter=2),
        "stat_lbl":     ParagraphStyle("sl", fontName="Helvetica", fontSize=7.5,
                           textColor=MUTED, alignment=TA_CENTER, leading=9),
        "footer":       ParagraphStyle("ft", fontName="Helvetica", fontSize=7,
                                       textColor=MUTED, alignment=TA_RIGHT),
    }


# ── Table helpers ─────────────────────────────────────────────────────────────

def _base_tbl_style():
    return [
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("TOPPADDING",    (0, 0), (-1, 0),  5),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  5),
        # Body rows
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, BG_ROW]),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER),
    ]


def _make_table(rows, col_widths):
    # Keep row-level integrity so long descriptions don't split awkwardly.
    t = Table(rows, colWidths=col_widths, repeatRows=1, splitByRow=1)
    t.setStyle(TableStyle(_base_tbl_style()))
    return t


def _apply_sev_colors(table, findings_list, sev_col_index=1, start_row=1):
    """Apply severity background color to individual cells."""
    for i, item in enumerate(findings_list, start=start_row):
        sev = item.get("severity", "")
        if sev in SEV_COLORS:
            _, bg = SEV_COLORS[sev]
            table.setStyle(TableStyle([
                ("BACKGROUND", (sev_col_index, i), (sev_col_index, i), bg),
                ("TEXTCOLOR",  (sev_col_index, i), (sev_col_index, i), SEV_COLORS[sev][0]),
                ("FONTNAME",   (sev_col_index, i), (sev_col_index, i), "Helvetica-Bold"),
            ]))


def _sev_text(sev):
    return sev or "N/A"


def _chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _section(title, S):
    return [
        Paragraph(title, S["h2"]),
        HRFlowable(width=CONTENT_W, thickness=0.5, color=PRIMARY, spaceAfter=3),
    ]


# ── Page footer ───────────────────────────────────────────────────────────────

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 9 * mm, "VAPT Toolkit — Confidential Security Report")
    canvas.drawRightString(
        PAGE_W - MARGIN, 9 * mm,
        f"Page {doc.page}"
    )
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, 11 * mm, PAGE_W - MARGIN, 11 * mm)
    canvas.restoreState()


# ── Main generator ────────────────────────────────────────────────────────────

def generate_pdf(project: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=18 * mm,
        title=f"VAPT Report — {project['target']}",
        author="VAPT Toolkit",
    )
    S = _styles()
    story = []

    cfg      = project.get("config", {})
    res      = project.get("results", {})
    created  = datetime.fromisoformat(project["created_at"]).strftime("%B %d, %Y  %H:%M UTC")
    name     = project.get("name", project["target"])

    # Build modules string
    if cfg.get("full_scan"):
        mods_str = "Recon  ·  Port Scan  ·  CVE Lookup  ·  Web Vulns"
    else:
        parts = []
        if cfg.get("recon"):  parts.append("Recon")
        if cfg.get("ports"):  parts.append(f"Port Scan ({cfg.get('port_range','?')})")
        if cfg.get("version_detect"): parts.append("Version Detection")
        if cfg.get("cve"):    parts.append("CVE Lookup")
        if cfg.get("web"):    parts.append(f"Web Vulns (depth {cfg.get('web_depth',1)})")
        mods_str = "  ·  ".join(parts) or "N/A"

    # ── Banner ────────────────────────────────────────────────────────────────
    banner = Table(
        [[
            Paragraph("VAPT TOOLKIT", S["banner_title"]),
            Paragraph(
                f"<b>Project:</b> {name}<br/>"
                f"<b>Target:</b>  {project['target']}<br/>"
                f"<b>Date:</b>    {created}<br/>"
                f"<b>Modules:</b> {mods_str}",
                S["banner_meta"]
            ),
        ]],
        colWidths=[55 * mm, CONTENT_W - 55 * mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PRIMARY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    story.append(banner)
    story.append(Spacer(1, 5 * mm))

    # ── Summary stats ─────────────────────────────────────────────────────────
    n_sub  = len(res.get("recon", {}).get("subdomains", []))
    n_port = len(res.get("ports", {}).get("open_ports", []))
    n_cve  = res.get("cve",  {}).get("total_cves", 0)
    n_web  = res.get("web",  {}).get("total", 0)

    def stat(n, lbl):
        return [Paragraph(str(n), S["stat_num"]), Paragraph(lbl, S["stat_lbl"])]

    stats = Table(
        [[stat(n_sub, "Subdomains"), stat(n_port, "Open Ports"),
          stat(n_cve, "CVEs"),       stat(n_web, "Web Findings")]],
        colWidths=[CONTENT_W / 4] * 4,
    )
    stats.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND",    (0, 0), (-1, -1), BG_ROW),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(stats)
    story.append(Spacer(1, 6 * mm))

    # ── Recon ─────────────────────────────────────────────────────────────────
    recon = res.get("recon")
    if recon:
        story += _section("Reconnaissance — Subdomains", S)

        # Root domain info
        root = recon.get("root", {})
        if root.get("a") or root.get("ns") or root.get("mx"):
            root_rows = []
            if root.get("a"):  root_rows.append(["Root A",  ", ".join(root["a"])])
            if root.get("ns"): root_rows.append(["NS",      ", ".join(root["ns"])])
            if root.get("mx"): root_rows.append(["MX",      ", ".join(root["mx"])])
            rt = Table(root_rows, colWidths=[25 * mm, CONTENT_W - 25 * mm])
            rt.setStyle(TableStyle([
                ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("TOPPADDING",    (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("TEXTCOLOR",     (0, 0), (0, -1), MUTED),
                ("BACKGROUND",    (0, 0), (-1, -1), BG_ROW),
                ("BOX",           (0, 0), (-1, -1), 0.4, BORDER),
                ("INNERGRID",     (0, 0), (-1, -1), 0.4, BORDER),
            ]))
            story.append(rt)
            story.append(Spacer(1, 3 * mm))

        subs = recon.get("subdomains", [])
        if subs:
            rows = [["Subdomain", "IPv4", "IPv6", "CNAME", "CDN / Hosting"]]
            for s in subs:
                ipv4 = ", ".join(s.get("ipv4") or s.get("ips") or []) or "—"
                ipv6 = ", ".join(s.get("ipv6") or []) or "—"
                cname = " → ".join(s.get("cname") or []) or "—"
                cdn = s.get("cdn") or "Direct"
                rows.append([
                    Paragraph(s.get("subdomain", ""), S["code"]),
                    Paragraph(ipv4, S["body"]),
                    Paragraph(ipv6, S["body"]),
                    Paragraph(cname, S["code"]),
                    Paragraph(cdn, S["body"]),
                ])
            t = _make_table(rows, [45 * mm, 28 * mm, 28 * mm, 45 * mm, CONTENT_W - 146 * mm])
            story.append(KeepTogether(t))
        else:
            story.append(Paragraph("No subdomains discovered.", S["muted"]))
        story.append(Spacer(1, 4 * mm))

    # ── Ports ─────────────────────────────────────────────────────────────────
    ports_res = res.get("ports")
    if ports_res:
        story += _section("Port Scan Results", S)

        # Host & OS info
        host_i = ports_res.get("host_info", {})
        os_i   = ports_res.get("os_info", {})
        if host_i or os_i:
            meta_rows = []
            if host_i.get("hostname"): meta_rows.append(["Hostname", host_i["hostname"]])
            if host_i.get("mac"):      meta_rows.append(["MAC", host_i["mac"]])
            if host_i.get("vendor"):   meta_rows.append(["Vendor",   host_i["vendor"]])
            if os_i.get("name"):
                meta_rows.append([
                    "OS",
                    f"{os_i['name']} ({os_i.get('accuracy','')}% confidence)"
                    + (f" — {os_i['osfamily']}" if os_i.get("osfamily") else "")
                ])
            if meta_rows:
                mt = Table([[Paragraph(k, S["bold"]), Paragraph(v, S["body"])]
                            for k, v in meta_rows],
                           colWidths=[25*mm, CONTENT_W-25*mm])
                mt.setStyle(TableStyle([
                    ("FONTSIZE", (0,0), (-1,-1), 8),
                    ("TOPPADDING", (0,0), (-1,-1), 3),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                    ("BACKGROUND", (0,0), (-1,-1), BG_ROW),
                    ("BOX", (0,0), (-1,-1), 0.4, BORDER),
                    ("INNERGRID", (0,0), (-1,-1), 0.4, BORDER),
                ]))
                story.append(mt)
                story.append(Spacer(1, 2*mm))

        ports = ports_res.get("open_ports", [])
        if ports:
            rows = [["Port", "Proto", "Service", "Product / Version", "Extra Info"]]
            for p in ports:
                ver = " ".join(filter(None, [p.get("product",""), p.get("version","")])) or "—"
                rows.append([
                    Paragraph(str(p["port"]), S["code"]),
                    Paragraph(p.get("proto","TCP"), S["body"]),
                    Paragraph(p.get("service","—") or "—", S["body"]),
                    Paragraph(ver, S["body"]),
                    Paragraph(p.get("extrainfo","") or "—", S["muted"]),
                ])
            t = _make_table(rows, [16*mm, 14*mm, 28*mm, 55*mm, CONTENT_W-113*mm])
            story.append(KeepTogether(t))

            # Script output (abbreviated)
            has_scripts = any(p.get("scripts") for p in ports)
            if has_scripts:
                story.append(Spacer(1, 2*mm))
                story.append(Paragraph("NSE Script Output", S["sub_head"]))
                for p in ports:
                    for sid, out in (p.get("scripts") or {}).items():
                        label = f"Port {p['port']} — {sid}"
                        story.append(Paragraph(label, S["bold"]))
                        story.append(Paragraph(out[:400].replace("\n", " "), S["code"]))
        else:
            story.append(Paragraph("No open ports found.", S["muted"]))
        story.append(Spacer(1, 4*mm))

    # ── CVE ───────────────────────────────────────────────────────────────────
    cve_res = res.get("cve")
    if cve_res:
        sources_used = cve_res.get("sources_used", ["NVD"])
        story += _section(f"CVE Correlation  [{', '.join(sources_used)}]", S)
        correlations = [c for c in cve_res.get("correlations", []) if c.get("cves")]
        if correlations:
            for entry in correlations:
                label = f"Port {entry['port']} — {entry.get('service','')} {entry.get('version','')}"
                cves = entry["cves"]
                for idx, cve_chunk in enumerate(_chunked(cves, CVE_ROWS_PER_CHUNK)):
                    chunk_label = label.strip() if idx == 0 else f"{label.strip()} (continued)"
                    story.append(Paragraph(chunk_label, S["sub_head"]))

                    rows = [["CVE / ID", "Source", "Severity", "Score", "Description / Exploits"]]
                    for cve in cve_chunk:
                        ref_url = ((cve.get("references") or [None])[0]
                                   or f"https://nvd.nist.gov/vuln/detail/{cve['cve_id']}")
                        exploit_text = ""
                        if cve.get("exploits"):
                            exploit_text = "<br/>" + "<br/>".join(
                                f'<link href="{e}" color="#cf222e">💥 {e[:60]}</link>'
                                for e in cve["exploits"][:2]
                            )
                        rows.append([
                            Paragraph(f'<link href="{ref_url}" color="#1f6feb">{cve["cve_id"]}</link>', S["body"]),
                            Paragraph(cve.get("source", "NVD"), S["body"]),
                            Paragraph(_sev_text(cve.get("severity")), S["bold"]),
                            Paragraph(str(cve.get("score", "N/A")), S["body"]),
                            Paragraph(cve.get("description", "")[:240] + exploit_text, S["body"]),
                        ])

                    col_w = [27*mm, 18*mm, 18*mm, 13*mm, CONTENT_W - 76*mm]
                    t = _make_table(rows, col_w)
                    _apply_sev_colors(t, cve_chunk)
                    story.append(KeepTogether(t))
                    story.append(Spacer(1, 3 * mm))
        else:
            story.append(Paragraph("No CVEs correlated.", S["muted"]))
        story.append(Spacer(1, 4 * mm))

    # ── Web ───────────────────────────────────────────────────────────────────
    web_res = res.get("web")
    if web_res:
        story += _section("Web Vulnerability Findings", S)
        findings = web_res.get("findings", [])
        if findings:
            rows = [["Type", "Severity", "Parameter", "Payload", "Evidence"]]
            for f in findings:
                rows.append([
                    Paragraph(f.get("type", ""), S["body"]),
                    Paragraph(_sev_text(f.get("severity")), S["bold"]),
                    Paragraph(f.get("parameter", ""), S["code"]),
                    Paragraph(f.get("payload", "")[:55], S["code"]),
                    Paragraph(f.get("evidence", ""), S["body"]),
                ])
            t = _make_table(rows, [36 * mm, 18 * mm, 24 * mm, 38 * mm, CONTENT_W - 116 * mm])
            _apply_sev_colors(t, findings)
            story.append(KeepTogether(t))
        else:
            story.append(Paragraph("No web vulnerabilities detected.", S["muted"]))
        story.append(Spacer(1, 4 * mm))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
