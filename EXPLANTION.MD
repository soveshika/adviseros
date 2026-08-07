# AdviserOS — How It Works

A full-stack platform for UK financial advisers: collect a client profile
through a guided wizard, run an analysis, and produce a PDF suitability
report.

This file explains how the system is built, which parts run, which parts
don't, and what I got wrong along the way.

## Architecture

| Layer | Technology |
|---|---|
| Frontend | React 19, Tailwind, Create React App |
| Backend | FastAPI, async SQLAlchemy 2.0, PostgreSQL |
| Migrations | Alembic |
| PDF | ReportLab |
| AI | Anthropic Claude API (written, never run — see below) |

The React app calls a FastAPI backend over `/api/v1`. The backend owns
five tables (clients, assets, investments, recommendations, reports) and
exposes CRUD routers for each, plus two service-backed endpoints:
`POST /analyse/{id}` and `GET /report/{id}/pdf`.

## What Works

**The data layer.** Async SQLAlchemy with connection pooling and
`pool_pre_ping`, a per-request session dependency that commits on success
and rolls back on exception, and Alembic wired to the same settings
object as the app.

**The schema.** Five tables with foreign keys and explicit cascade rules
(`CASCADE` on client deletion, `RESTRICT` on assets so a held asset can't
be deleted). Computed properties for `cost_basis` and
`unrealized_gain_loss`. Pydantic v2 schemas with real constraints —
`confidence_score` bounded 0–1, quantities `gt=0`, investment horizon
1–50 years.

**The portfolio maths.** Cost basis, current value, gain/loss and
percentage return are calculated from actual investment rows, both for
the report record and for each holding in the PDF table.

**The PDF generator.** Around 400 lines of ReportLab: navy and gold cover
page, eight sections, alternating table row backgrounds, a footer redrawn
on every page with page numbers, and an FSMA 2000 disclaimer covering past
performance, capital risk and tax treatment.

## What Doesn't

The Claude integration is written but has never run. `_build_prompt()`
assembles the client's age, risk profile, income, net worth and every
holding with its return, adds a table of current UK tax allowances (ISA
£20,000, pension £60,000, CGT £3,000, IHT nil-rate band £325,000,
dividend £500, and the income tax bands), and specifies a strict six-key
JSON output schema. `_call_claude()` sends it, strips markdown fences from
the reply, and parses the JSON.

I never obtained an API key, so `anthropic.Anthropic()` would fail on
import. Every demo — including one shown to a working adviser — ran on a
mock version returning a hardcoded analysis, tagged
`generated_by = "Mock/..."`.

This means sections 3 to 8 of every PDF contain identical text regardless
of the client: the same £20,000 ISA headroom, the same £420,000 projected
pension pot, the same five recommendations. Only section 2, the portfolio
overview, is genuinely personalised.

**Lesson:** code that is written is not code that works. Until it runs
against the real dependency, it is a plan, not a feature.

## The Bug I Found Writing This

I built the AI engine as a standalone `ai engine/` folder first, then
moved it into `app/services/`. I left the original in place.

The two copies drifted. One returns mock data; the other calls Claude.
Two `main.py` files exist too — the older one is missing CORS middleware
and the report router entirely, so the frontend could not reach it.

Worse, the mock tag leaked into code that has nothing to do with mocking:

```python
# report_generator.py
.where(Report.generated_by.like("Mock/%"))
