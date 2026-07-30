"""
AdviserOS — AI Analysis Engine
Fetches client data, builds a UK financial adviser prompt,
returns structured mock analysis, saves to reports table.
"""

import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Client, Investment, Report, ReportType


MODEL = "claude-sonnet-4-20250514"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _gbp(val) -> str:
    if val is None:
        return "£0"
    return f"£{int(val):,}"


def _pct_change(cost: Decimal, current: Decimal) -> str:
    if not cost or cost == 0:
        return "N/A"
    change = ((current - cost) / cost) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


# ── Step 1 — Fetch full client profile ───────────────────────────────────────
async def _fetch_client(client_id: int, db: AsyncSession) -> Client:
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.investments).selectinload(Investment.asset),
            selectinload(Client.recommendations),
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise ValueError(f"Client {client_id} not found")
    return client


# ── Step 2 — Mock Claude response ────────────────────────────────────────────
def _call_claude(prompt: str) -> dict:
    return {
        "tax_optimisation": {
            "isa_headroom": "£20,000 fully unused — immediate ISA contribution recommended",
            "pension_headroom": "£40,000 remaining pension allowance this tax year",
            "cgt_position": "No CGT liability currently — consider crystallising gains up to £3,000",
            "iht_exposure": "Estate below nil-rate band — no immediate IHT concern",
            "dividend_position": "£500 allowance fully available",
            "income_tax_band": "Basic rate taxpayer — consider salary sacrifice to reduce liability",
            "summary": "Significant tax-free allowances remain unused this year. Priority should be maximising ISA and pension contributions before April."
        },
        "investment_review": [
            {
                "fund_name": "Portfolio Holdings",
                "status": "performing",
                "return_pct": "+12.3%",
                "verdict": "Portfolio is broadly performing above inflation.",
                "action": "hold"
            }
        ],
        "risk_alignment": {
            "stated_risk": "moderate",
            "actual_risk": "moderate",
            "aligned": True,
            "commentary": "Portfolio allocation matches stated risk tolerance well. No immediate rebalancing required.",
            "suggested_changes": ["Consider adding international diversification"]
        },
        "retirement_projection": {
            "current_pension_value": "£85,000",
            "target_retirement_age": 65,
            "projected_pot_at_retirement": "£420,000",
            "monthly_income_estimate": "£1,750",
            "shortfall_or_surplus": "-£280,000",
            "recommendation": "Current pension contributions are insufficient for target retirement income. Increasing monthly contributions by £500 would significantly close the gap."
        },
        "protection_gaps": {
            "life_cover": "No life cover identified — recommend £500,000 level term policy",
            "income_protection": "No income protection — recommend 60% of salary coverage",
            "critical_illness": "Critical illness cover not in place — review urgently",
            "overall_gap_severity": "high"
        },
        "recommendations": [
            {
                "priority": 1,
                "category": "Tax",
                "action": "Maximise ISA allowance before April",
                "rationale": "Full £20,000 ISA allowance is unused this tax year. Tax-free growth opportunity is being missed.",
                "gbp_impact": "£4,000/year tax saving",
                "urgency": "this_tax_year"
            },
            {
                "priority": 2,
                "category": "Protection",
                "action": "Arrange life and income protection cover",
                "rationale": "Significant protection gaps identified. Family financial security is at risk.",
                "gbp_impact": "£500,000 life cover",
                "urgency": "immediate"
            },
            {
                "priority": 3,
                "category": "Pension",
                "action": "Increase monthly pension contributions by £500",
                "rationale": "Current trajectory projects a retirement shortfall. Additional contributions now have maximum compound growth benefit.",
                "gbp_impact": "£85,000 additional pot by retirement",
                "urgency": "next_12_months"
            },
            {
                "priority": 4,
                "category": "Investment",
                "action": "Review and rebalance portfolio allocation",
                "rationale": "Portfolio lacks international diversification. Adding global equity exposure reduces concentration risk.",
                "gbp_impact": "Improved risk-adjusted returns",
                "urgency": "next_12_months"
            },
            {
                "priority": 5,
                "category": "Estate Planning",
                "action": "Draft or update Will and LPA",
                "rationale": "No estate planning documents identified. Essential for protecting family interests.",
                "gbp_impact": "Avoids intestacy complications",
                "urgency": "long_term"
            }
        ]
    }


# ── Step 3 — Save to reports table ───────────────────────────────────────────
async def _save_report(client: Client, analysis: dict, db: AsyncSession) -> Report:
    total_current = sum(float(inv.current_value or 0) for inv in client.investments)
    total_cost    = sum(float(inv.quantity * inv.purchase_price) for inv in client.investments)
    gain_loss     = total_current - total_cost
    gain_loss_pct = ((gain_loss / total_cost) * 100) if total_cost else 0

    report = Report(
        client_id             = client.id,
        report_type           = ReportType.ANNUAL,
        title                 = f"AI Financial Analysis — {client.first_name} {client.last_name}",
        period_start          = date.today(),
        period_end            = date.today(),
        summary               = json.dumps(analysis),
        total_portfolio_value = Decimal(str(round(total_current, 2))),
        total_gain_loss       = Decimal(str(round(gain_loss, 2))),
        total_gain_loss_pct   = Decimal(str(round(gain_loss_pct, 4))),
        is_draft              = False,
        generated_by          = f"Mock/{MODEL}",
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


# ── Main public function ──────────────────────────────────────────────────────
async def analyse_client(client_id: int, db: AsyncSession) -> dict:
    # 1. Fetch client
    client = await _fetch_client(client_id, db)

    # 2. Build prompt (kept for when real API is connected)
    prompt = f"Analyse client: {client.first_name} {client.last_name}"

    # 3. Get analysis
    analysis = _call_claude(prompt)

    # 4. Save report
    report = await _save_report(client, analysis, db)

    # 5. Return
    return {
        "client_id":    client.id,
        "client_name":  f"{client.first_name} {client.last_name}",
        "report_id":    report.id,
        "generated_at": datetime.utcnow().isoformat(),
        "model":        MODEL,
        "analysis":     analysis,
    }