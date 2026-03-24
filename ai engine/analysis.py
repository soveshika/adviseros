"""
AdviserOS — AI Analysis Engine
Fetches client data, builds a UK financial adviser prompt,
calls Claude, parses structured JSON, saves to reports table.
"""

import json
import re
from datetime import date, datetime
from decimal import Decimal

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Client, Investment, Report, ReportType


# ── Anthropic client (reads ANTHROPIC_API_KEY from environment) ───────────────
_claude = anthropic.Anthropic()
MODEL   = "claude-sonnet-4-20250514"


# ── Helper ────────────────────────────────────────────────────────────────────
def _gbp(val) -> str:
    """Format a number as £ with commas."""
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


# ── Step 2 — Build the prompt ─────────────────────────────────────────────────
def _build_prompt(client: Client) -> str:
    # --- Basic profile ---
    age_str = "Unknown age"
    if client.date_of_birth:
        today = date.today()
        age = today.year - client.date_of_birth.year - (
            (today.month, today.day) < (client.date_of_birth.month, client.date_of_birth.day)
        )
        age_str = f"{age} years old"

    # --- Investments ---
    investment_lines = []
    total_cost    = Decimal("0")
    total_current = Decimal("0")

    for inv in client.investments:
        cost    = inv.quantity * inv.purchase_price
        current = inv.current_value or Decimal("0")
        total_cost    += cost
        total_current += current
        asset_name = inv.asset.name if inv.asset else f"Asset #{inv.asset_id}"
        investment_lines.append(
            f"  • {asset_name} | Invested: {_gbp(cost)} on {inv.purchase_date} "
            f"| Current value: {_gbp(current)} | Return: {_pct_change(cost, current)}"
        )

    investments_section = "\n".join(investment_lines) if investment_lines else "  • No investments recorded"
    portfolio_gain_loss = total_current - total_cost

    # --- Parse notes for goals (stored as "Goals: short | medium | long") ---
    notes = client.notes or ""
    goals_section = notes if notes else "No goals recorded"

    prompt = f"""You are a senior UK Chartered Financial Planner with 20+ years of experience.
Analyse the following client profile and produce a detailed, actionable financial analysis.
You MUST respond with ONLY valid JSON — no preamble, no markdown, no explanation outside the JSON.

=== CLIENT PROFILE ===
Name:             {client.first_name} {client.last_name}
Age:              {age_str}
Risk Profile:     {client.risk_profile.value}
Investment Horizon: {client.investment_horizon_years or "Not specified"} years
Annual Income:    {_gbp(client.annual_income)}
Net Worth:        {_gbp(client.net_worth)}

=== PORTFOLIO ===
Total Cost Basis:    {_gbp(total_cost)}
Total Current Value: {_gbp(total_current)}
Overall Gain/Loss:   {_gbp(portfolio_gain_loss)} ({_pct_change(total_cost, total_current)})

Individual Holdings:
{investments_section}

=== GOALS ===
{goals_section}

=== UK TAX ALLOWANCES (current tax year) ===
- ISA allowance:              £20,000/year
- Pension annual allowance:   £60,000/year (or 100% of earnings)
- Capital Gains Tax allowance: £3,000/year
- IHT nil-rate band:          £325,000
- Dividend allowance:         £500/year
- Personal allowance:         £12,570/year
- Basic rate band:            £12,571–£50,270 (20%)
- Higher rate band:           £50,271–£125,140 (40%)
- Additional rate:            above £125,140 (45%)

=== YOUR TASK ===
Produce a structured JSON analysis with EXACTLY these 6 keys:

1. "tax_optimisation" — object with:
   - "isa_headroom": how much ISA allowance remains unused (£ figure + recommendation)
   - "pension_headroom": unused pension allowance (£ figure + recommendation)
   - "cgt_position": CGT exposure or opportunity (£ figure + action)
   - "iht_exposure": IHT liability estimate and mitigation options
   - "dividend_position": dividend income vs allowance
   - "income_tax_band": which band the client is in and any optimisation tips
   - "summary": 2-sentence overall tax summary

2. "investment_review" — array of objects, one per holding:
   - "fund_name": string
   - "status": "performing" | "underperforming" | "review"
   - "return_pct": string (e.g. "+12.3%")
   - "verdict": 1-sentence assessment
   - "action": "hold" | "sell" | "rebalance" | "increase"

3. "risk_alignment" — object with:
   - "stated_risk": client's stated risk profile
   - "actual_risk": your assessment of actual portfolio risk
   - "aligned": true | false
   - "commentary": 2-sentence explanation
   - "suggested_changes": array of strings

4. "retirement_projection" — object with:
   - "current_pension_value": £ figure
   - "target_retirement_age": number
   - "projected_pot_at_retirement": £ figure (estimate)
   - "monthly_income_estimate": £ figure
   - "shortfall_or_surplus": £ figure (negative = shortfall)
   - "recommendation": 2-sentence action plan

5. "protection_gaps" — object with:
   - "life_cover": assessment and recommended cover amount
   - "income_protection": assessment and recommended monthly benefit
   - "critical_illness": brief note
   - "overall_gap_severity": "low" | "medium" | "high"

6. "recommendations" — array of exactly 5 objects, prioritised by impact:
   - "priority": 1–5 (1 = most urgent)
   - "category": e.g. "Tax", "Investment", "Pension", "Protection", "Estate Planning"
   - "action": clear action title (max 10 words)
   - "rationale": 2-sentence explanation
   - "gbp_impact": estimated £ benefit (string, e.g. "£4,000/year tax saving")
   - "urgency": "immediate" | "this_tax_year" | "next_12_months" | "long_term"

Respond ONLY with the JSON object. No other text."""

    return prompt


# ── Step 3 — Call Claude ──────────────────────────────────────────────────────
def _call_claude(prompt: str) -> dict:
    message = _claude.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Strip markdown fences if Claude wraps in ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


# ── Step 4 — Save to reports table ───────────────────────────────────────────
async def _save_report(client: Client, analysis: dict, db: AsyncSession) -> Report:
    # Calculate totals for the report record
    total_current = sum(
        float(inv.current_value or 0) for inv in client.investments
    )
    total_cost = sum(
        float(inv.quantity * inv.purchase_price) for inv in client.investments
    )
    gain_loss     = total_current - total_cost
    gain_loss_pct = ((gain_loss / total_cost) * 100) if total_cost else 0

    # Top recommendation as summary
    top_rec = ""
    recs = analysis.get("recommendations", [])
    if recs:
        top_rec = recs[0].get("action", "")

    report = Report(
        client_id             = client.id,
        report_type           = ReportType.ANNUAL,
        title                 = f"AI Financial Analysis — {client.first_name} {client.last_name}",
        period_start          = date.today(),
        period_end            = date.today(),
        summary               = json.dumps(analysis),   # full JSON stored in summary
        total_portfolio_value = Decimal(str(round(total_current, 2))),
        total_gain_loss       = Decimal(str(round(gain_loss, 2))),
        total_gain_loss_pct   = Decimal(str(round(gain_loss_pct, 4))),
        is_draft              = False,
        generated_by          = f"Claude/{MODEL}",
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


# ── Main public function ──────────────────────────────────────────────────────
async def analyse_client(client_id: int, db: AsyncSession) -> dict:
    """
    Full pipeline:
      1. Fetch client + investments from PostgreSQL
      2. Build detailed UK financial adviser prompt
      3. Call Claude API
      4. Parse structured JSON response
      5. Save report to DB
      6. Return analysis dict + report metadata
    """
    # 1. Fetch
    client = await _fetch_client(client_id, db)

    # 2. Build prompt
    prompt = _build_prompt(client)

    # 3. Call Claude
    analysis = _call_claude(prompt)

    # 4. Save
    report = await _save_report(client, analysis, db)

    # 5. Return
    return {
        "client_id":   client.id,
        "client_name": f"{client.first_name} {client.last_name}",
        "report_id":   report.id,
        "generated_at": datetime.utcnow().isoformat(),
        "model":        MODEL,
        "analysis":     analysis,
    }
