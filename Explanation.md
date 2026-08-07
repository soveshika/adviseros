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
be deleted). Computed properties for cost basis and unrealised gain/loss.
Pydantic v2 schemas with real constraints — confidence score bounded 0–1,
quantities greater than zero, investment horizon 1–50 years.

**The portfolio maths.** Cost basis, current value, gain/loss and
percentage return are calculated from actual investment rows, both for
the report record and for each holding in the PDF table.

**The PDF generator.** Around 400 lines of ReportLab: navy and gold cover
page, eight sections, alternating table row backgrounds, a footer redrawn
on every page with page numbers, and an FSMA 2000 disclaimer covering
past performance, capital risk and tax treatment.

## What Doesn't

The Claude integration is written but has never run. The prompt builder
assembles the client's age, risk profile, income, net worth and every
holding with its return, adds a table of current UK tax allowances (ISA
£20,000, pension £60,000, CGT £3,000, IHT nil-rate band £325,000,
dividend £500, and the income tax bands), and specifies a strict six-key
JSON output schema. The API call sends it, strips markdown fences from
the reply, and parses the JSON.

I never obtained an API key, so the Anthropic client would fail on
import. Every demo — including one shown to a working adviser — ran on a
mock version returning a hardcoded analysis, tagged in the database as
mock-generated.

This means sections 3 to 8 of every PDF contain identical text
regardless of the client: the same £20,000 ISA headroom, the same
£420,000 projected pension pot, the same five recommendations. Only
section 2, the portfolio overview, is genuinely personalised.

**Lesson:** code that is written is not code that works. Until it runs
against the real dependency, it is a plan, not a feature.

## The Bug I Found Writing This

I built the AI engine as a standalone folder first, then moved it into
the backend services directory. I left the original in place.

The two copies drifted. One returns mock data; the other calls Claude.
Two entry-point files exist too — the older one is missing CORS
middleware and the report router entirely, so the frontend could not
reach it.

Worse, the mock tag leaked into code that has nothing to do with
mocking. Both the PDF lookup query and the dashboard's report counter
filter on reports whose generator name begins with "Mock/". If the real
analysis ever runs, reports are tagged "Claude/..." instead, so the PDF
lookup finds nothing and returns "No AI analysis found" — right after a
successful analysis.

**Lesson:** a temporary value used as a lookup key stops being
temporary. The mock tag became load-bearing in two files that should
never have known the mock existed.

## Data Collected And Discarded

The onboarding wizard has five steps and collects roughly thirty fields —
property value, mortgage outstanding, ISA balance, pension value, other
loans, monthly expenses, debt repayments, individual fund holdings with
dates, and three separate goal horizons.

The submit payload sends seven: first name, last name, email, risk
profile, net worth, annual income, and notes.

Net worth is savings plus pension plus ISA added together. Everything
else — property, mortgage, expenses, every individual investment row —
is discarded in the browser. The investments table exists and is fully
modelled, but the wizard never writes to it.

**Lesson:** I built the form and the schema separately and never checked
that one fed the other. The gap was invisible because the app still
appeared to work.

## Other Things I'd Fix

- **Email addresses are synthesised** from the client's first and last
  name. Combined with the unique constraint on the email column, two
  clients with the same name collide and the wizard reports "Email
  already registered".
- **The secret key defaults to a placeholder** and there is no
  authentication on any endpoint. Anyone who can reach the API can read
  every client record.
- **Tables are created at startup** even though Alembic is configured.
  Convenient locally, wrong anywhere else.
- **The default Create React App test was never updated**, so the test
  suite fails against the rewritten app.
- **CORS is hardcoded** to localhost.

## What This Is And Isn't

It is a working full-stack application with a real database schema, a
functioning onboarding UI, correct portfolio arithmetic, and a genuinely
good PDF generator — built against a brief from a UK adviser with 40
years in the profession.

It is not production software. It has no authentication, no tests, an
external integration that has never executed, and a duplicated service
folder I only found by writing this document.
