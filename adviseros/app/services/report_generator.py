"""
AdviserOS — Report & Email Generator
Part A: PDF Suitability Report (ReportLab)
Part B: Client Email Draft (Claude mock)

Bug fixes:
  1. Portfolio now fetches investments directly via separate query
  2. Risk profile is consistent — always uses client.risk_profile.value
  3. Investment horizon calculated as (target_retirement_age - current_age)
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Asset, Client, Investment, Report, ReportType

# ── Constants ─────────────────────────────────────────────────────────────────
REPORTS_DIR  = Path("reports")
ADVISER_NAME = "James Anderson CFP"
ADVISER_FIRM = "Anderson Wealth Management"

NAVY  = colors.HexColor("#0B1F3A")
GOLD  = colors.HexColor("#C9A84C")
LIGHT = colors.HexColor("#F5F7FA")
GREY  = colors.HexColor("#6B7280")
GREEN = colors.HexColor("#166534")
RED   = colors.HexColor("#991B1B")
WHITE = colors.white
BLACK = colors.black

DISCLAIMER = (
    "This report has been prepared by {} of {} for the exclusive use of the named client. "
    "It is based on information provided by the client and is confidential. "
    "This document does not constitute regulated financial advice under the Financial Services "
    "and Markets Act 2000. Past performance is not a reliable indicator of future results. "
    "The value of investments may fall as well as rise and you may get back less than you invest. "
    "Tax treatment depends on individual circumstances and may change. "
    "This report is valid as of the date shown on the cover page."
).format(ADVISER_NAME, ADVISER_FIRM)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _gbp(val) -> str:
    if val is None:
        return "£0"
    try:
        return f"£{int(float(val)):,}"
    except Exception:
        return str(val)


def _client_age(client: Client) -> int | None:
    if not client.date_of_birth:
        return None
    today = date.today()
    return today.year - client.date_of_birth.year - (
        (today.month, today.day) < (client.date_of_birth.month, client.date_of_birth.day)
    )


def _investment_horizon(client: Client, analysis: dict) -> str:
    """
    BUG 3 FIX — Calculate horizon as target_retirement_age minus current age.
    Falls back to stored value, then to Not specified.
    """
    target_age = analysis.get("retirement_projection", {}).get("target_retirement_age")
    age = _client_age(client)

    if target_age and age:
        horizon = int(target_age) - age
        if horizon > 0:
            return f"{horizon} years (retire at {target_age})"

    if client.investment_horizon_years:
        return f"{client.investment_horizon_years} years"

    return "Not specified"


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold", fontSize=28,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica", fontSize=13,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Helvetica", fontSize=10,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=3,
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontName="Helvetica-Bold", fontSize=14,
            textColor=NAVY, spaceBefore=14, spaceAfter=6,
        ),
        "sub_heading": ParagraphStyle(
            "sub_heading", fontName="Helvetica-Bold", fontSize=11,
            textColor=NAVY, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=BLACK, leading=15, spaceAfter=4,
        ),
        "body_bold": ParagraphStyle(
            "body_bold", fontName="Helvetica-Bold", fontSize=10,
            textColor=BLACK, leading=15, spaceAfter=4,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", fontName="Helvetica", fontSize=7,
            textColor=GREY, leading=10, alignment=TA_CENTER,
        ),
        "confidential": ParagraphStyle(
            "confidential", fontName="Helvetica-Bold", fontSize=9,
            textColor=RED, alignment=TA_CENTER,
        ),
        "right": ParagraphStyle(
            "right", fontName="Helvetica", fontSize=10,
            textColor=GREY, alignment=TA_RIGHT,
        ),
    }
    return {**{k: base[k] for k in base.byName}, **custom}


def _disclaimer_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(20*mm, 18*mm, w - 20*mm, 18*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    canvas.drawCentredString(w/2, 13*mm, DISCLAIMER[:120] + "…")
    canvas.drawCentredString(w/2, 9*mm, f"{ADVISER_FIRM}  |  Confidential  |  Page {doc.page}")
    canvas.restoreState()


def _section(story, title, styles):
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=3))
    story.append(Paragraph(title, styles["section_heading"]))


def _kv_table(rows, styles):
    data = [[Paragraph(f"<b>{k}</b>", styles["body"]),
             Paragraph(str(v), styles["body"])] for k, v in rows]
    t = Table(data, colWidths=[70*mm, 100*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1),  LIGHT),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [WHITE, LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return t


# ── Fetch helpers ─────────────────────────────────────────────────────────────
async def _fetch_client(client_id: int, db: AsyncSession) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise ValueError(f"Client {client_id} not found")
    return client


async def _fetch_investments(client_id: int, db: AsyncSession) -> list:
    """
    BUG 1 FIX — Fetch investments directly with explicit query,
    ensuring fresh data is always loaded from the database.
    """
    result = await db.execute(
        select(Investment)
        .where(Investment.client_id == client_id)
        .options(selectinload(Investment.asset))
    )
    return list(result.scalars().all())


async def _fetch_latest_analysis(client_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Report)
        .where(Report.client_id == client_id, Report.generated_by.like("Mock/%"))
        .order_by(desc(Report.created_at))
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report or not report.summary:
        raise ValueError("No AI analysis found. Run POST /analyse/{client_id} first.")
    return json.loads(report.summary)


# ══════════════════════════════════════════════════════════════════════════════
# PART A — PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def _build_pdf(client: Client, investments: list, analysis: dict, output_path: Path) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    styles = _styles()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=28*mm,
        title=f"Suitability Report — {client.first_name} {client.last_name}",
        author=ADVISER_NAME,
    )
    story = []
    w = A4[0] - 40*mm

    # ── COVER PAGE ────────────────────────────────────────────────────────────
    cover_firm = Table([[Paragraph(ADVISER_FIRM, styles["cover_sub"])]], colWidths=[w])
    cover_firm.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cover_firm)

    cover_rows = [
        Paragraph("PERSONAL FINANCIAL", styles["cover_title"]),
        Paragraph("SUITABILITY REPORT", styles["cover_title"]),
        Paragraph(" ", styles["cover_meta"]),
        Paragraph(f"Prepared for: {client.first_name} {client.last_name}", styles["cover_sub"]),
        Paragraph(f"Date: {date.today().strftime('%d %B %Y')}", styles["cover_meta"]),
        Paragraph(f"Adviser: {ADVISER_NAME}", styles["cover_meta"]),
        Paragraph(" ", styles["cover_meta"]),
        Paragraph("STRICTLY CONFIDENTIAL", styles["confidential"]),
    ]
    cover_body = Table([[r] for r in cover_rows], colWidths=[w])
    cover_body.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cover_body)
    gold_bar = Table([[""]], colWidths=[w], rowHeights=[8])
    gold_bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD)]))
    story.append(gold_bar)
    story.append(PageBreak())

    # BUG 2 FIX: single source of truth for risk profile
    risk_value = client.risk_profile.value.capitalize()

    # ── CLIENT SUMMARY ────────────────────────────────────────────────────────
    _section(story, "1. Client Summary", styles)
    story.append(_kv_table([
        ("Full Name",          f"{client.first_name} {client.last_name}"),
        ("Email",              client.email),
        ("Risk Profile",       risk_value),                             # BUG 2 FIX
        ("Investment Horizon", _investment_horizon(client, analysis)),  # BUG 3 FIX
        ("Annual Income",      _gbp(client.annual_income)),
        ("Net Worth",          _gbp(client.net_worth)),
    ], styles))

    # ── PORTFOLIO OVERVIEW ────────────────────────────────────────────────────
    # BUG 1 FIX: use directly-fetched investments list
    _section(story, "2. Portfolio Overview", styles)

    total_cost    = sum(float(inv.quantity * inv.purchase_price) for inv in investments)
    total_current = sum(float(inv.current_value or 0) for inv in investments)
    gain_loss     = total_current - total_cost
    gl_pct        = ((gain_loss / total_cost) * 100) if total_cost else 0

    story.append(_kv_table([
        ("Total Cost Basis",    _gbp(total_cost)),
        ("Total Current Value", _gbp(total_current)),
        ("Overall Gain / Loss", f"{_gbp(gain_loss)}  ({gl_pct:+.1f}%)"),
        ("Number of Holdings",  str(len(investments))),
    ], styles))

    if investments:
        story.append(Spacer(1, 4*mm))
        inv_data = [["Fund / Asset", "Invested", "Current Value", "Return"]]
        for inv in investments:
            cost    = float(inv.quantity * inv.purchase_price)
            current = float(inv.current_value or 0)
            ret     = ((current - cost) / cost * 100) if cost else 0
            name    = inv.asset.name if inv.asset else f"Asset #{inv.asset_id}"
            inv_data.append([name, _gbp(cost), _gbp(current), f"{ret:+.1f}%"])

        inv_table = Table(inv_data, colWidths=[80*mm, 35*mm, 40*mm, 25*mm])
        inv_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(inv_table)
    else:
        story.append(Paragraph(
            "No investment holdings recorded for this client.", styles["body"]
        ))

    story.append(PageBreak())

    # ── TAX OPTIMISATION ─────────────────────────────────────────────────────
    _section(story, "3. Tax Optimisation Findings", styles)
    tax = analysis.get("tax_optimisation", {})
    story.append(_kv_table([
        ("ISA Headroom",      tax.get("isa_headroom", "N/A")),
        ("Pension Headroom",  tax.get("pension_headroom", "N/A")),
        ("CGT Position",      tax.get("cgt_position", "N/A")),
        ("IHT Exposure",      tax.get("iht_exposure", "N/A")),
        ("Dividend Position", tax.get("dividend_position", "N/A")),
        ("Income Tax Band",   tax.get("income_tax_band", "N/A")),
    ], styles))
    if tax.get("summary"):
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(f"<b>Summary:</b> {tax['summary']}", styles["body"]))

    # ── INVESTMENT REVIEW ─────────────────────────────────────────────────────
    _section(story, "4. Investment Review", styles)
    for item in analysis.get("investment_review", []):
        story.append(Paragraph(f"<b>{item.get('fund_name', 'N/A')}</b>", styles["sub_heading"]))
        story.append(_kv_table([
            ("Status",  item.get("status", "N/A").upper()),
            ("Return",  item.get("return_pct", "N/A")),
            ("Verdict", item.get("verdict", "N/A")),
            ("Action",  item.get("action", "N/A").upper()),
        ], styles))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ── RISK ALIGNMENT ────────────────────────────────────────────────────────
    # BUG 2 FIX: use same risk_value variable as client summary
    _section(story, "5. Risk Alignment Assessment", styles)
    risk = analysis.get("risk_alignment", {})
    story.append(_kv_table([
        ("Stated Risk Profile",  risk_value),                          # BUG 2 FIX
        ("Actual Portfolio Risk", risk.get("actual_risk", "N/A").capitalize()),
        ("Aligned",              "Yes" if risk.get("aligned") else "No — Action Required"),
    ], styles))
    if risk.get("commentary"):
        story.append(Paragraph(risk["commentary"], styles["body"]))
    if risk.get("suggested_changes"):
        story.append(Paragraph("<b>Suggested Changes:</b>", styles["body_bold"]))
        for change in risk["suggested_changes"]:
            story.append(Paragraph(f"• {change}", styles["body"]))

    # ── RETIREMENT PROJECTION ─────────────────────────────────────────────────
    _section(story, "6. Retirement Projection", styles)
    ret = analysis.get("retirement_projection", {})
    story.append(_kv_table([
        ("Current Pension Value",       ret.get("current_pension_value", "N/A")),
        ("Target Retirement Age",       str(ret.get("target_retirement_age", "N/A"))),
        ("Projected Pot at Retirement", ret.get("projected_pot_at_retirement", "N/A")),
        ("Estimated Monthly Income",    ret.get("monthly_income_estimate", "N/A")),
        ("Shortfall / Surplus",         ret.get("shortfall_or_surplus", "N/A")),
    ], styles))
    if ret.get("recommendation"):
        story.append(Paragraph(ret["recommendation"], styles["body"]))

    story.append(PageBreak())

    # ── PROTECTION GAPS ───────────────────────────────────────────────────────
    _section(story, "7. Protection Gap Analysis", styles)
    prot = analysis.get("protection_gaps", {})
    severity = prot.get("overall_gap_severity", "medium")
    story.append(_kv_table([
        ("Life Cover",          prot.get("life_cover", "N/A")),
        ("Income Protection",   prot.get("income_protection", "N/A")),
        ("Critical Illness",    prot.get("critical_illness", "N/A")),
        ("Overall Gap Severity",severity.upper()),
    ], styles))

    # ── RECOMMENDATIONS ───────────────────────────────────────────────────────
    _section(story, "8. Prioritised Recommendations", styles)
    for rec in sorted(analysis.get("recommendations", []), key=lambda r: r.get("priority", 99)):
        priority = rec.get("priority", "")
        action   = rec.get("action", "")
        category = rec.get("category", "")
        urgency  = rec.get("urgency", "long_term").replace("_", " ").upper()
        impact   = rec.get("gbp_impact", "")
        rationale= rec.get("rationale", "")

        rec_table = Table([[
            Paragraph(f"<b>{priority}. {action}</b>", styles["sub_heading"]),
            Paragraph(f"{category}  |  {urgency}", styles["right"]),
        ]], colWidths=[120*mm, 50*mm])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))
        story.append(rec_table)
        story.append(Paragraph(rationale, styles["body"]))
        story.append(Paragraph(f"<b>Estimated Impact:</b> {impact}", styles["body_bold"]))
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())

    # ── DISCLAIMER ────────────────────────────────────────────────────────────
    _section(story, "Important Information & Disclaimer", styles)
    story.append(Paragraph(DISCLAIMER, styles["body"]))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f"Report generated: {datetime.now().strftime('%d %B %Y at %H:%M')}  |  "
        f"Adviser: {ADVISER_NAME}  |  Firm: {ADVISER_FIRM}",
        styles["disclaimer"],
    ))

    doc.build(story, onFirstPage=_disclaimer_footer, onLaterPages=_disclaimer_footer)
    return output_path


async def generate_report(client_id: int, db: AsyncSession) -> dict:
    client      = await _fetch_client(client_id, db)
    investments = await _fetch_investments(client_id, db)   # BUG 1 FIX
    analysis    = await _fetch_latest_analysis(client_id, db)

    filename    = f"report_{client_id}_{date.today().isoformat()}.pdf"
    output_path = REPORTS_DIR / filename
    _build_pdf(client, investments, analysis, output_path)

    return {
        "client_id":    client_id,
        "client_name":  f"{client.first_name} {client.last_name}",
        "pdf_path":     str(output_path),
        "filename":     filename,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PART B — EMAIL DRAFT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def _generate_email_mock(client: Client, investments: list, analysis: dict) -> str:
    recs  = analysis.get("recommendations", [])
    top3  = sorted(recs, key=lambda r: r.get("priority", 99))[:3]
    tax   = analysis.get("tax_optimisation", {})
    ret   = analysis.get("retirement_projection", {})
    total_current = sum(float(inv.current_value or 0) for inv in investments)

    rec_lines = "\n".join(
        f"  {i+1}. {r.get('action','')}: {r.get('rationale','').split('.')[0]}."
        for i, r in enumerate(top3)
    )

    email = f"""Subject: Your Personal Financial Review — {client.first_name} {client.last_name}

Dear {client.first_name},

I hope this message finds you well. Following our recent review, I have completed a thorough analysis of your financial position and I'm pleased to share the key findings with you.

WHAT WE FOUND

Your portfolio is currently valued at {_gbp(total_current)}, and overall your financial position is in reasonably good shape. However, there are some important opportunities we should act on — particularly around tax efficiency and long-term financial security.

Here are the three most important findings:

1. Tax Allowances Going Unused
{tax.get('summary', 'There are unused tax allowances that could be working harder for you.')}

2. Retirement Planning Gap
{ret.get('recommendation', 'Your current pension contributions may not be sufficient to meet your retirement income goals.')}

3. Protection Review Needed
Based on your current circumstances, there are gaps in your financial protection that we should address to safeguard your family's future.

TOP RECOMMENDATIONS FOR YOU

{rec_lines}

NEXT STEPS

I would strongly recommend we arrange a follow-up meeting to discuss these findings in detail and put a clear action plan in place. Even small changes made now can have a significant impact on your long-term financial wellbeing.

Please reply to this email or call our office to arrange a convenient time. I look forward to speaking with you soon.

Kind regards,

{ADVISER_NAME}
{ADVISER_FIRM}

---
This email is intended solely for the named recipient. The content is based on information you have provided and does not constitute regulated financial advice. Please refer to your full Suitability Report for complete details and important risk information.
"""
    return email.strip()


async def generate_email(client_id: int, db: AsyncSession) -> dict:
    client      = await _fetch_client(client_id, db)
    investments = await _fetch_investments(client_id, db)   # BUG 1 FIX
    analysis    = await _fetch_latest_analysis(client_id, db)

    email_text = _generate_email_mock(client, investments, analysis)

    report = Report(
        client_id    = client_id,
        report_type  = ReportType.PORTFOLIO_SUMMARY,
        title        = f"Email Draft — {client.first_name} {client.last_name}",
        period_start = date.today(),
        period_end   = date.today(),
        summary      = email_text,
        is_draft     = True,
        generated_by = "EmailGenerator/Mock",
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return {
        "client_id":    client_id,
        "client_name":  f"{client.first_name} {client.last_name}",
        "report_id":    report.id,
        "generated_at": datetime.utcnow().isoformat(),
        "email_draft":  email_text,
    }
