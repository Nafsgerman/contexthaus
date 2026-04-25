# ContextHaus

> **The living context engine for property management.**  
> One document per building. Always current. Always traced.

[![Security: Aikido](https://img.shields.io/badge/security-aikido-green?style=flat-square)](https://aikido.dev)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue?style=flat-square)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black?style=flat-square)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)

---

## The Problem

Property managers drown in context. A single building generates dozens of touchpoints every month: ownership-transfer emails, DOMUS ERP exports, PDF maintenance reports, assembly minutes, contractor invoices. Each document lands in a different silo — inbox, drive folder, ERP system — and none of them talk to each other.

When a contractor calls about a boiler at Kastanienallee 88, the manager needs to know: who owns it, who the caretaker is, what the last assembly decided, and whether there's an open ticket. That answer lives across four systems, two languages, and three years of emails.

**ContextHaus solves this by maintaining a single, always-current `PROPERTY.md` per building** — dense, structured, sourced, and surgically updated every time a new document arrives.

---

## Solution Overview

ContextHaus is an ingestion-first context engine. Drop in an email, a PDF, or a German ERP CSV export — ContextHaus classifies it, extracts what matters, and patches only the relevant section of the property's living document. Human edits are preserved. Every fact is traced to its source.

```
Email / PDF / ERP CSV
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     INGEST PIPELINE                         │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  File Parser │───▶│   Pioneer    │───▶│  ERP Schema   │  │
│  │ (email/PDF/  │    │  Classifier  │    │   Resolver    │  │
│  │   ERP CSV)   │    │ (signal/noise│    │ Eigentümer→   │  │
│  └──────────────┘    │  filter)     │    │  owner etc.   │  │
│                      └──────┬───────┘    └───────┬───────┘  │
│                             │ relevant           │           │
│                             ▼                    ▼           │
│                      ┌─────────────────────────────────┐    │
│                      │      Gemini 2.5 Pro/Flash        │    │
│                      │  First ingest → full PROPERTY.md │    │
│                      │  Subsequent → surgical section   │    │
│                      │  patch (Flash, targeted prompt)  │    │
│                      └─────────────┬───────────────────┘    │
│                                    │                         │
│                      ┌─────────────▼───────────────────┐    │
│                      │       Tavily Enrichment          │    │
│                      │  (first ingest only — public     │    │
│                      │   web data appended to Notes)    │    │
│                      └─────────────┬───────────────────┘    │
└────────────────────────────────────┼────────────────────────┘
                                     │
                                     ▼
                          ┌──────────────────┐
                          │   PROPERTY.md    │
                          │  (SQLite, async) │
                          │                  │
                          │ ## Meta          │
                          │ ## Ownership     │
                          │ ## Open Issues   │
                          │ ## Decisions     │
                          │ ## Contractors   │
                          │ ## Notes         │
                          └────────┬─────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │   Next.js 14 UI       │
                        │  Dark mode, live diff │
                        │  Amber flash on update│
                        └──────────────────────┘
```

---

## Three Hard Problems Solved

### 1. Schema Alignment — German ERP Babel

German Hausverwaltung software (DOMUS, Haufe, WEG-Manager) exports CSVs with inconsistent column names depending on version, module, and house. `Eigentümer`, `MietEig`, `Eigentuemer`, and `Kontakt` all mean "owner" — but a naive parser silently drops three of them.

ContextHaus ships a canonical schema map that resolves all known aliases before the LLM ever sees the data:

```
Eigentümer    ──┐
MietEig       ──┼──▶  owner
Eigentuemer   ──┘

MietEig_Kontakt ─┬──▶  owner_contact
Kontakt         ─┘

Heizung_Wartung ────▶  heating_contractor
Letzter_Beschluss ──▶  last_decision
Offene_Tickets ─────▶  open_issues
```

This happens in `backend/app/core/erp_parser.py` before any token is spent on LLM inference. The schema map is extensible — new ERP variants are one line to add.

---

### 2. Surgical Patching — Human Edits Preserved

The naive approach regenerates the entire `PROPERTY.md` on every ingest. This destroys any corrections a property manager made by hand and burns expensive Pro-tier tokens on unchanged sections.

ContextHaus uses a two-phase strategy:

```
First ingest (empty doc)          Subsequent ingest (doc exists)
        │                                    │
        ▼                                    ▼
  Gemini 2.5 Pro                  Pioneer classifies section
  Full generation                  │
  + Tavily enrichment              ▼
  + PROPERTY.md written      Gemini 2.5 Flash
                             targeted PATCH_SECTION prompt
                             only the relevant ## section
                             is rewritten
                                   │
                                   ▼
                             patch_section() regex
                             replaces only that block
                             all other sections unchanged
```

**Before** a maintenance report arrives:

```markdown
## Open Issues
- Roof inspection overdue (noted by manager 2025-03-01)

## Ownership
- owner: Hans Müller   ← manager corrected spelling manually
```

**After** surgical patch (only `Open Issues` touched):

```markdown
## Open Issues
- Roof inspection overdue (noted by manager 2025-03-01)
- URGENT: Water damage reported 2nd floor — contractor dispatched

## Ownership
- owner: Hans Müller   ← untouched
```

The diff engine (`diff_sections`) returns structured change objects — added/updated sections with old and new content — which the frontend uses to drive the amber flash animation.

---

### 3. Signal vs Noise — Pioneer Classifier Gate

Every ingest first passes through a Pioneer (Llama 3.2-3B-Instruct) classifier before spending tokens on Gemini. A newsletter, a spam email, or an unrelated PDF is rejected at the gate with zero LLM cost beyond the classifier call.

The classifier returns structured JSON:

```json
{
  "relevant": false,
  "confidence": 0.94,
  "reason": "marketing newsletter, no property management content"
}
```

Irrelevant documents return `{ "status": "ignored" }` to the caller immediately. The property document is not touched.

Pioneer is called only on documents ingested when a property already has context (first ingest always proceeds to bootstrap the document). This avoids the cold-start problem.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Backend runtime | Python | 3.11 | Async API server |
| API framework | FastAPI | 0.115 | REST endpoints, async handlers |
| Database | SQLite + SQLAlchemy async | 2.0 | Property and source storage |
| ASGI server | uvicorn | 0.34 | Production-grade serving |
| Frontend | Next.js | 14 | React app, SSR |
| Styling | Tailwind CSS | 3.4 | Dark UI, amber diff highlights |
| Language (FE) | TypeScript | 5 | Type-safe API client |
| LLM (generation) | Gemini 2.5 Pro | latest | Full PROPERTY.md generation |
| LLM (patching) | Gemini 2.5 Flash | latest | Surgical section patches |
| Classifier | Pioneer / Llama 3.2-3B | Instruct | Signal/noise gate |
| Enrichment | Tavily Search API | v2 | Public property data |
| PDF parsing | pypdf | 5.x | Text extraction from PDFs |
| Security | Aikido | — | 0 open issues |

---

## Partner Technologies

ContextHaus was built for a hackathon requiring a minimum of three partner technologies. Four are integrated:

### Google DeepMind — Gemini 2.5 Pro + Flash

Two tiers of Gemini serve different purposes:

- **Gemini 2.5 Pro** handles initial document generation (`GENERATE_CONTEXT` prompt). It sees all source documents for a property and produces the full structured `PROPERTY.md`. Used once per property.
- **Gemini 2.5 Flash** handles subsequent surgical patches (`PATCH_SECTION` prompt). It receives only the target section and the new document, minimising cost and latency on every subsequent ingest.

### Tavily — Property Enrichment

After the first ingest generates a `PROPERTY.md`, Tavily enriches it with public web data about the address. Neighbourhood data, planning permits, and local service ratings are appended to the `## Notes` section. This happens automatically and only once per property to avoid stale enrichment.

### Pioneer by Fastino — Signal / Noise Classifier

Pioneer serves `meta-llama/Llama-3.2-3B-Instruct` via an OpenAI-compatible endpoint. ContextHaus uses it as a cheap, fast gate before committing Gemini tokens. The 3B model is sufficient for binary relevance classification of property documents and returns structured JSON classification results in under 500ms.

### Aikido — Security Scanning

Aikido runs continuous security analysis on the codebase. Current status: **0 open issues**. All dependencies are scanned for CVEs; CORS, injection vectors, and secret exposure are monitored.

---

## Architecture

```
contexthaus/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   ├── api/
│   │   │   ├── properties.py    # GET/POST /api/properties
│   │   │   └── ingest.py        # POST /api/ingest/{id}/source
│   │   ├── core/
│   │   │   ├── llm.py           # Gemini Pro/Flash wrappers
│   │   │   ├── patcher.py       # Surgical section patching
│   │   │   ├── classifier.py    # Pioneer relevance gate
│   │   │   ├── enricher.py      # Tavily enrichment
│   │   │   └── erp_parser.py    # German ERP CSV + schema map
│   │   └── db/
│   │       ├── database.py      # SQLite async engine
│   │       └── models.py        # Property, Source, Fact models
│   └── prompts/
│       └── context_generate.py  # SYSTEM, GENERATE_CONTEXT, PATCH_SECTION
└── frontend/
    ├── app/                     # Next.js 14 app router
    ├── components/              # PropertyCard, DiffViewer, UploadPanel
    └── lib/
        └── api.ts               # Typed API client
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`)

### Environment Variables

Create `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
PIONEER_API_KEY=your_pioneer_key
DATABASE_URL=sqlite+aiosqlite:///./contexthaus.db
```

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -e .
uvicorn app.main:app --reload --port 8000
```

Backend starts at `http://localhost:8000`. Visit `/docs` for the interactive API explorer.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at `http://localhost:3000`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/properties/` | List all properties |
| `POST` | `/api/properties/` | Create a new property |
| `GET` | `/api/properties/{id}` | Get a single property with context |
| `POST` | `/api/ingest/{id}/source` | Ingest a file (email/PDF/CSV), returns diff |
| `GET` | `/api/ingest/{id}/context` | Get raw `PROPERTY.md` for a property |
| `GET` | `/api/test-gemini` | Connectivity test for Gemini |

### Ingest Response Schema

```json
{
  "status": "ingested",
  "source_id": "uuid",
  "filename": "domus_export.csv",
  "section_updated": "Ownership",
  "changes": [
    {
      "section": "Ownership",
      "type": "updated",
      "old": "- owner: unknown",
      "new": "- owner: Hans Müller\n- owner_contact: h.mueller@example.com"
    }
  ],
  "context_md": "## Meta\n..."
}
```

When a document is filtered by Pioneer:

```json
{
  "status": "ignored",
  "reason": "marketing newsletter, no property management content",
  "changes": []
}
```

---

## Demo Properties

Three Berlin properties are pre-seeded for demonstration:

| Property | Address | Demo Document | What It Shows |
|---|---|---|---|
| Schönhauser Allee 15 | Schönhauser Allee 15, 10435 Berlin | Ownership transfer email | First ingest → full generation + Tavily enrichment |
| Kastanienallee 88 | Kastanienallee 88, 10435 Berlin | `domus_export.csv` | ERP schema resolution (Eigentümer→owner) |
| Rykestraße 7 | Rykestraße 7, 10405 Berlin | Water damage PDF | Surgical patch of `Open Issues` only, human edits preserved |

---

## How the UI Works

The frontend displays each property's `PROPERTY.md` rendered as structured cards. When an ingest completes:

1. The diff response identifies which sections changed (`added` or `updated`)
2. Changed sections flash **amber** for 2 seconds
3. The document settles back to the dark theme with new content in place

This makes it immediately visible what a document changed — without showing a raw diff or reloading the page.

---

## Security

Scanned by [Aikido](https://aikido.dev) — **0 open issues**.

- No secrets in version control (`.env` excluded via `.gitignore`)
- CORS restricted to `localhost:3000` in development
- All user inputs are passed to LLMs as data, never as executable instructions
- File uploads are size-capped and decoded safely with `errors="ignore"`

---

## License

MIT © 2025 Nafees Ahamed

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
