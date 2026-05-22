# SeaBridge AI Sustainability Toolkit

**Physical climate risk · Transition risk · Nature risk · ISSB IFRS S2 disclosure**

An MVP AI Sustainability Toolkit for real-asset climate and nature risk assessment, aligned to ISSB IFRS S2, TCFD, and TNFD frameworks.

---

## Architecture

```
toolkit/
├── backend/          FastAPI + LangGraph AI agent
│   ├── app/
│   │   ├── models/       Pydantic v2 data models
│   │   ├── api/          FastAPI route handlers
│   │   ├── hazards/      6 physical hazard modules
│   │   ├── transition/   Transition risk engine
│   │   ├── nature/       Nature risk (TNFD LEAP)
│   │   ├── opportunities/ Climate opportunities
│   │   ├── agents/       LangGraph workflow
│   │   └── disclosure/   ISSB/TCFD/TNFD report generator
│   └── tests/            pytest test suite
└── frontend/         Next.js 15 + TypeScript UI
```

---

## Quick Start

### Backend

```bash
cd toolkit/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY if using AI features
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd toolkit/frontend
npm install
npm run dev   # runs on port 3001
```

### Seed demo data

```bash
cd toolkit/backend
python -m scripts.seed_demo
```

### Docker Compose

```bash
cd toolkit
docker-compose up
```

---

## Physical Risk Hazards

| Hazard | Key Features | Primary Data Sources |
|--------|-------------|---------------------|
| Wildfire | Climate aridity, vegetation fuel, slope, state risk, smoke/AQI | LANDFIRE, NIFC, EPA AQS |
| Inland Flood | FEMA flood zone, elevation, river proximity, precipitation, impervious surface | FEMA NFHL, USGS 3DEP, NOAA MRMS |
| Coastal Flood / SLR | Coast distance, SLR exposure, storm surge, FEMA coastal zone, erosion | NOAA Tides, FEMA NFHL, USGS CHP |
| Heat Stress | Projected heat days, UHI, historical heatwaves, cooling vulnerability, wet-bulb | NASA NEX-GDDP-CMIP6, NLCD |
| Drought / Water Stress | Drought class, precipitation change, water stress basin, soil moisture, demand | US Drought Monitor, WRI Aqueduct |
| Wind / Hurricane | Hurricane tracks, design wind zone, tornado, building vulnerability, coastal amplification | NOAA IBTrACS, HURDAT2, SPC |

### Scoring Method
```
category_score = 0.5 × max_feature_score + 0.5 × avg_remaining_features
overall_score  = (highest_hazard × 2 + all_other_hazards) / (n + 1)

Rating thresholds:
  0–20  → Very Low
 21–40  → Low
 41–60  → Moderate
 61–80  → High
 81–100 → Very High
```

---

## AI Agent Workflow (LangGraph)

```
validate_request
  → load_company
  → load_properties
  → geocode_or_validate_coordinates
  → enrich_building_context
  → score_physical_risk
  → run_transition_risk_agent
  → run_climate_opportunities_agent
  → run_nature_risk_agent
  → validate_evidence
  → check_confidence
      → [confidence < 0.70 OR high-risk disclosure] → await_human_review
      → [else] → generate_disclosure_summary
```

Human review is triggered when:
- Confidence < 0.70
- Missing evidence for a material claim
- High/Very High risk score affects disclosure language

---

## Disclosure Output (ISSB IFRS S2 / TCFD / TNFD)

1. **Executive Summary** — top risks, opportunities, data gaps
2. **Governance** — oversight recommendations (ISSB S2 §6–9)
3. **Strategy** — scenario analysis, portfolio exposure, resilience (ISSB S2 §10–24)
4. **Risk Management** — methodology, sources, controls (ISSB S2 §25–31)
5. **Metrics and Targets** — hazard scores, emissions/energy, adaptation (ISSB S2 §29–41)
6. **Appendix** — sources, assumptions, confidence, limitations

---

## Data Quality Guardrails

Every output includes:
- `data_source_type`: `observed | modeled | scenario_assumption | ai_generated | user_provided | missing`
- `source_name` + `source_url`
- `scenario` + `time_horizon`
- `confidence` level
- `data_gaps` list

The system **never**:
- Fabricates property values, hazard data, or financial losses
- Presents AI narrative as measured data
- Hides missing data
- Calls paid/live APIs unless explicitly enabled
- Treats screening results as engineering-grade loss modelling

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Enables LLM-enhanced agent narrative | No (AI features degrade gracefully) |
| `MAPBOX_TOKEN` | Satellite map tiles in frontend | No (list view used as fallback) |
| `ENABLE_PAID_PROVIDERS` | Gates commercial data API calls | No (default: false) |
| `MONGODB_URL` | Production database | No (in-memory store for MVP) |

---

## Running Tests

```bash
cd toolkit/backend
pytest tests/ -v
```

---

## Framework Alignment

| Framework | Coverage |
|-----------|---------|
| ISSB IFRS S2 | Governance, Strategy, Risk Management, Metrics (§6–41) |
| TCFD | All 4 pillars |
| TNFD | LEAP process (Locate, Evaluate, Assess, Prepare) |
| SASB | Real Estate energy/water/GHG metrics referenced |
| NGFS | Net Zero 2050, Delayed Transition, Hot House scenarios |
| NASA NEX-GDDP-CMIP6 | SSP1-2.6, SSP2-4.5, SSP5-8.5 |

---

*This toolkit is at screening/indicative tier. Replace open-access proxies with site-specific data and detailed catastrophe modelling before using outputs in formal regulatory disclosures.*
