"""Server-side PDF report generator using ReportLab — produces real text-based PDFs."""
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
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
CHART_GAP = 5 * mm
CHART_W = (CONTENT_W - CHART_GAP) / 2

BAR_COLORS = [
    colors.HexColor("#58a6ff"),
    colors.HexColor("#3fb950"),
    colors.HexColor("#bf91f3"),
    colors.HexColor("#f0883e"),
    colors.HexColor("#f85149"),
    colors.HexColor("#79c0ff"),
    colors.HexColor("#d29922"),
]


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


def _normalize_sev(sev):
    value = (sev or "N/A").upper()
    if value == "CRITICAL":
        return "Critical"
    if value == "HIGH":
        return "High"
    if value == "MEDIUM":
        return "Medium"
    if value == "LOW":
        return "Low"
    return "N/A"


def _count_by(items, key_fn):
    counts = {}
    for item in items:
        key = key_fn(item) or "Unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _score_bucket(score):
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "N/A"
    if value < 3:
        return "0-3"
    if value < 5:
        return "3-5"
    if value < 7:
        return "5-7"
    if value < 9:
        return "7-9"
    return "9-10"


def _trim_label(text, limit=18):
    text = str(text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _plain(value):
    return escape("" if value is None else str(value))


def _chart_colors(items, color_map=None):
    fills = []
    for idx, (label, _) in enumerate(items):
        fills.append((color_map or {}).get(label, BAR_COLORS[idx % len(BAR_COLORS)]))
    return fills


def _bar_chart(title, items, *, width=CHART_W, color_map=None, max_items=6):
    items = [(str(label), int(value)) for label, value in items if value is not None][:max_items]
    row_h = 18
    top_pad = 30
    bottom_pad = 14
    height = top_pad + max(len(items), 1) * row_h + bottom_pad
    drawing = Drawing(width, height)

    drawing.add(Rect(0, 0, width, height, fillColor=BG_ROW, strokeColor=BORDER, strokeWidth=0.6, rx=6, ry=6))
    drawing.add(String(10, height - 18, title, fontName="Helvetica-Bold", fontSize=9, fillColor=TEXT))

    if not items:
        drawing.add(String(10, height - 40, "No data available", fontName="Helvetica", fontSize=8, fillColor=MUTED))
        return drawing

    fills = _chart_colors(items, color_map=color_map)
    label_w = 72
    value_w = 20
    bar_x = 10 + label_w
    bar_w = width - bar_x - value_w - 14
    max_value = max(value for _, value in items) or 1
    y = height - top_pad - 1

    for idx, ((label, value), fill) in enumerate(zip(items, fills)):
        y -= row_h
        drawing.add(String(10, y + 3, _trim_label(label), fontName="Helvetica", fontSize=7.5, fillColor=MUTED))
        drawing.add(Rect(bar_x, y, bar_w, 10, fillColor=WHITE, strokeColor=BORDER, strokeWidth=0.3))
        fill_w = 0 if value <= 0 else max(10, (bar_w * value) / max_value)
        drawing.add(Rect(bar_x, y, min(fill_w, bar_w), 10, fillColor=fill, strokeColor=fill, strokeWidth=0))
        drawing.add(String(bar_x + bar_w + 6, y + 2, str(value), fontName="Helvetica-Bold", fontSize=7.5, fillColor=TEXT))

    return drawing


def _chart_grid(charts):
    if not charts:
        return []
    rows = []
    for i in range(0, len(charts), 2):
        row = charts[i:i + 2]
        if len(row) == 1:
            row = [row[0], Spacer(CHART_W, 1)]
        rows.append(row)
    grid = Table(rows, colWidths=[CHART_W, CHART_W], hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), CHART_GAP),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [grid]


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

    # ── Visual summary ────────────────────────────────────────────────────────
    summary_chart = _bar_chart(
        "Overview Metrics",
        [
            ("Subdomains", n_sub),
            ("Open Ports", n_port),
            ("CVEs", n_cve),
            ("Web Findings", n_web),
        ],
    )
    story += _section("Visual Summary", S)
    story += _chart_grid([summary_chart])
    story.append(Spacer(1, 2 * mm))

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
            direct = sum(1 for s in subs if not s.get("cdn"))
            behind = len(subs) - direct
            source_counts = _count_by(subs, lambda s: s.get("source") or "brute")
            story += _chart_grid([
                _bar_chart("Direct vs CDN Exposure", [("Direct", direct), ("Behind CDN", behind)]),
                _bar_chart("Discovery Sources", sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))),
            ])
            rows = [["Subdomain", "IPv4", "IPv6", "CNAME", "CDN / Hosting"]]
            for s in subs:
                ipv4 = ", ".join(s.get("ipv4") or s.get("ips") or []) or "—"
                ipv6 = ", ".join(s.get("ipv6") or []) or "—"
                cname = " → ".join(s.get("cname") or []) or "—"
                cdn = s.get("cdn") or "Direct"
                rows.append([
                        Paragraph(_plain(s.get("subdomain", "")), S["code"]),
                    Paragraph(_plain(ipv4), S["body"]),
                    Paragraph(_plain(ipv6), S["body"]),
                    Paragraph(_plain(cname), S["code"]),
                    Paragraph(_plain(cdn), S["body"]),
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
                mt = Table([[Paragraph(_plain(k), S["bold"]), Paragraph(_plain(v), S["body"])]
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
            service_counts = _count_by(ports, lambda p: p.get("service") or "unknown")
            proto_counts = _count_by(ports, lambda p: (p.get("proto") or p.get("protocol") or "tcp").upper())
            story += _chart_grid([
                _bar_chart("Top Services", sorted(service_counts.items(), key=lambda item: (-item[1], item[0]))),
                _bar_chart("Protocol Split", sorted(proto_counts.items(), key=lambda item: (-item[1], item[0]))),
            ])
            rows = [["Port", "Proto", "Service", "Product / Version", "Extra Info"]]
            for p in ports:
                ver = " ".join(filter(None, [p.get("product",""), p.get("version","")])) or "—"
                rows.append([
                    Paragraph(str(p["port"]), S["code"]),
                    Paragraph(_plain(p.get("proto","TCP")), S["body"]),
                    Paragraph(_plain(p.get("service","—") or "—"), S["body"]),
                    Paragraph(_plain(ver), S["body"]),
                    Paragraph(_plain(p.get("extrainfo","") or "—"), S["muted"]),
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
                        story.append(Paragraph(_plain(label), S["bold"]))
                        story.append(Paragraph(_plain(out[:400].replace("\n", " ")), S["code"]))
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
            cves_flat = [cve for entry in correlations for cve in entry.get("cves", [])]
            severity_counts = _count_by(cves_flat, lambda cve: _normalize_sev(cve.get("severity")))
            ordered_severity = ["Critical", "High", "Medium", "Low", "N/A"]
            severity_items = [(label, severity_counts.get(label, 0)) for label in ordered_severity if severity_counts.get(label, 0)]
            score_counts = _count_by(cves_flat, lambda cve: _score_bucket(cve.get("score")))
            score_order = ["0-3", "3-5", "5-7", "7-9", "9-10", "N/A"]
            score_items = [(label, score_counts.get(label, 0)) for label in score_order if score_counts.get(label, 0)]
            sev_fill_map = {
                "Critical": SEV_COLORS["Critical"][0],
                "High": SEV_COLORS["High"][0],
                "Medium": SEV_COLORS["Medium"][0],
                "Low": SEV_COLORS["Low"][0],
                "N/A": MUTED,
            }
            score_fill_map = {
                "0-3": MUTED,
                "3-5": SEV_COLORS["Low"][0],
                "5-7": SEV_COLORS["Medium"][0],
                "7-9": SEV_COLORS["High"][0],
                "9-10": SEV_COLORS["Critical"][0],
                "N/A": MUTED,
            }
            story += _chart_grid([
                _bar_chart("Severity Distribution", severity_items, color_map=sev_fill_map),
                _bar_chart("CVSS Score Buckets", score_items, color_map=score_fill_map),
            ])
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
                            Paragraph(_plain(cve.get("source", "NVD")), S["body"]),
                            Paragraph(_plain(_sev_text(cve.get("severity"))), S["bold"]),
                            Paragraph(_plain(cve.get("score", "N/A")), S["body"]),
                            Paragraph(_plain(cve.get("description", "")[:240]) + exploit_text, S["body"]),
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
            type_counts = _count_by(findings, lambda f: f.get("type") or "Unknown")
            severity_counts = _count_by(findings, lambda f: _normalize_sev(f.get("severity")))
            ordered_severity = ["Critical", "High", "Medium", "Low", "N/A"]
            severity_items = [(label, severity_counts.get(label, 0)) for label in ordered_severity if severity_counts.get(label, 0)]
            sev_fill_map = {
                "Critical": SEV_COLORS["Critical"][0],
                "High": SEV_COLORS["High"][0],
                "Medium": SEV_COLORS["Medium"][0],
                "Low": SEV_COLORS["Low"][0],
                "N/A": MUTED,
            }
            story += _chart_grid([
                _bar_chart("Finding Types", sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))),
                _bar_chart("Severity Distribution", severity_items, color_map=sev_fill_map),
            ])
            rows = [["Type", "Severity", "Parameter", "Payload", "Evidence"]]
            for f in findings:
                rows.append([
                    Paragraph(_plain(f.get("type", "")), S["body"]),
                    Paragraph(_plain(_sev_text(f.get("severity"))), S["bold"]),
                    Paragraph(_plain(f.get("parameter", "")), S["code"]),
                    Paragraph(_plain(f.get("payload", "")[:55]), S["code"]),
                    Paragraph(_plain(f.get("evidence", "")), S["body"]),
                ])
            t = _make_table(rows, [36 * mm, 18 * mm, 24 * mm, 38 * mm, CONTENT_W - 116 * mm])
            _apply_sev_colors(t, findings)
            story.append(KeepTogether(t))

            # ─── Compliance & Standards Section ───
            story.append(Spacer(1, 4 * mm))
            story += _section("Compliance & Standards Mapping", S)

            # Collect OWASP categories
            owasp_counts = _count_by(findings, lambda f: f.get("owasp_category", "Unknown"))
            if owasp_counts:
                rows = [["OWASP Category", "Count"]]
                for owasp, count in sorted(owasp_counts.items(), key=lambda x: -x[1]):
                    rows.append([
                        Paragraph(_plain(owasp), S["body"]),
                        Paragraph(str(count), S["bold"]),
                    ])
                t = _make_table(rows, [CONTENT_W * 0.7, CONTENT_W * 0.3])
                story.append(Paragraph("OWASP Top 10 2021 Mapping:", S["sub_head"]))
                story.append(t)
                story.append(Spacer(1, 2 * mm))

            # Collect CWE IDs
            cwe_counts = _count_by(findings, lambda f: f.get("cwe_id", "Unknown"))
            if cwe_counts:
                rows = [["CWE ID", "Description", "Count"]]
                cwe_descriptions = {
                    "CWE-89": "SQL Injection",
                    "CWE-79": "Cross-site Scripting",
                    "CWE-352": "Cross-Site Request Forgery",
                    "CWE-918": "Server-Side Request Forgery",
                    "CWE-639": "Authorization Issues",
                    "CWE-434": "Unrestricted Upload of File",
                    "CWE-22": "Path Traversal",
                    "CWE-287": "Improper Authentication",
                    "CWE-327": "Use of Broken Cryptography",
                    "CWE-200": "Exposure of Sensitive Information",
                    "CWE-16": "Configuration",
                    "CWE-502": "Deserialization of Untrusted Data",
                    "CWE-840": "Business Logic",
                    "CWE-770": "Allocation of Resources",
                }
                for cwe, count in sorted(cwe_counts.items(), key=lambda x: -x[1])[:10]:
                    desc = cwe_descriptions.get(cwe, "")
                    rows.append([
                        Paragraph(_plain(cwe), S["code"]),
                        Paragraph(_plain(desc), S["body"]),
                        Paragraph(str(count), S["bold"]),
                    ])
                t = _make_table(rows, [18 * mm, CONTENT_W - 40 * mm, 22 * mm])
                story.append(Paragraph("CWE (Common Weakness Enumeration) References:", S["sub_head"]))
                story.append(t)
                story.append(Spacer(1, 2 * mm))

            # Collect compliance frameworks
            compliance_frameworks = set()
            for f in findings:
                if f.get("compliance_impact"):
                    if isinstance(f["compliance_impact"], list):
                        compliance_frameworks.update(f["compliance_impact"])
                    else:
                        compliance_frameworks.add(f["compliance_impact"])

            if compliance_frameworks:
                frameworks_text = ", ".join(sorted(compliance_frameworks))
                story.append(Paragraph("Affected Compliance Frameworks:", S["sub_head"]))
                story.append(Paragraph(_plain(frameworks_text), S["body"]))
                story.append(Spacer(1, 2 * mm))

            # CVSS Score Distribution
            cvss_scores = [f.get("cvss_score", 0) for f in findings if f.get("cvss_score")]
            if cvss_scores:
                avg_cvss = sum(cvss_scores) / len(cvss_scores)
                story.append(Paragraph("CVSS v3.1 Scoring:", S["sub_head"]))
                cvss_row = [[
                    f"Average CVSS Score: {avg_cvss:.1f}/10.0",
                    f"Highest: {max(cvss_scores):.1f}",
                    f"Lowest: {min(cvss_scores):.1f}",
                ]]
                t = Table(cvss_row, colWidths=[CONTENT_W / 3] * 3)
                t.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (0, 0), (-1, -1), BG_ROW),
                    ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
                ]))
                story.append(t)
        else:
            story.append(Paragraph("No web vulnerabilities detected.", S["muted"]))
        story.append(Spacer(1, 4 * mm))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
