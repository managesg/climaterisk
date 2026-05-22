"""ISSB IFRS S2 / TCFD / TNFD disclosure report generator."""

from datetime import date
from typing import Any


class DisclosureGenerator:
    """Generates a structured disclosure report from agent state.

    Every claim is tagged with: source, scenario, time_horizon, confidence, data_type.
    Output is markdown suitable for inclusion in sustainability reports.
    """

    def generate(self, state: dict[str, Any]) -> str:
        company = state.get("company") or {}
        physical = state.get("physical_risk_results") or {}
        transition = state.get("transition_risk") or {}
        opportunities = state.get("opportunities") or {}
        nature_risk = state.get("nature_risk") or {}
        data_gaps = state.get("data_gaps") or []
        confidence = state.get("confidence", 0.0)
        scenario = state.get("scenario", "ssp245")
        year = state.get("year", 2050)
        assumptions = state.get("assumptions") or []

        sections = [
            self._header(company, scenario, year),
            self._executive_summary(company, physical, transition, opportunities, data_gaps, confidence),
            self._governance(),
            self._strategy(company, physical, transition, opportunities, scenario, year),
            self._risk_management(scenario),
            self._metrics_and_targets(physical, company),
            self._appendix(data_gaps, assumptions, confidence, scenario, year),
        ]
        return "\n\n---\n\n".join(sections)

    # ─────────────────────────────── sections ────────────────────────────────

    def _header(self, company: dict, scenario: str, year: int) -> str:
        name = company.get("name", "Organisation")
        today = date.today().isoformat()
        return f"""# Climate Risk & Nature Risk Disclosure
## {name}
*Generated: {today} | Framework: ISSB IFRS S2 / TCFD / TNFD | Scenario: {scenario.upper()} | Horizon: {year}*

> **Data integrity notice:** This report distinguishes between observed data, modelled data,
> scenario assumptions, AI-generated interpretation, user-provided information, and missing data.
> Each material claim is tagged accordingly. This report represents a **screening-level assessment**,
> not engineering-grade loss modelling."""

    def _executive_summary(
        self,
        company: dict,
        physical: dict,
        transition: dict,
        opportunities: dict,
        data_gaps: list[str],
        confidence: float,
    ) -> str:
        name = company.get("name", "the organisation")
        n_props = len(physical)
        top_risks = self._top_physical_risks(physical)
        n_trans = len(transition.get("categories", []))
        n_opp = len(opportunities.get("opportunities", []))
        n_gaps = len(data_gaps)

        return f"""## 1. Executive Summary

**Organisation:** {name}
**Properties assessed:** {n_props}
**Overall screening confidence:** {confidence:.0%}
*(Data type: AI-generated interpretation of modelled and observed inputs)*

### Top Physical Risks
{top_risks}

### Transition Risk Summary
{n_trans} transition risk categories analysed across Policy/Legal, Market, Technology,
Reputation, Insurance, Utilities, and Capital Access.
*(Data type: AI-generated | Scenario-based)*

### Climate Opportunities
{n_opp} opportunities identified across resource efficiency, energy transition,
products/services, markets, resilience, and green finance.
*(Data type: AI-generated)*

### Data Gaps
{n_gaps} data items could not be sourced from available open-access providers.
Key gaps: {', '.join(data_gaps[:5]) if data_gaps else 'None identified'}.
See Appendix for full data gap register.

> **Limitation:** This is a preliminary screening. Results should not be used as a substitute
> for site-specific engineering assessment or catastrophe modelling."""

    def _governance(self) -> str:
        return """## 2. Governance
*(Framework: ISSB IFRS S2 §§ 6–9 | TCFD: Governance)*

### Board Oversight
This disclosure recommends that the Board or appropriate sub-committee receive annual briefings
on material climate and nature risks identified in this report. Oversight should include:
- Review of physical and transition risk scores at least annually
- Approval of climate-related targets and adaptation investments
- Integration of climate risk into enterprise risk management

### Management Responsibility
A named senior executive (e.g. Chief Sustainability Officer or equivalent) should own
the climate risk register, commission updates to this assessment when material changes occur,
and report to the Board on progress against targets.

### Review Cadence
- **Annual:** Full physical risk re-run with updated scenario projections
- **Quarterly:** Transition risk policy/market monitoring
- **On event:** Re-assessment following significant climate events affecting assets

*Note: Governance recommendations are AI-generated guidance based on ISSB S2 requirements.
They do not constitute legal or regulatory advice.*
*(Data type: AI-generated)*"""

    def _strategy(
        self,
        company: dict,
        physical: dict,
        transition: dict,
        opportunities: dict,
        scenario: str,
        year: int,
    ) -> str:
        sector = company.get("sector", "unknown")
        n_props = len(physical)
        n_trans_cats = len(transition.get("categories", [])) if isinstance(transition, dict) else 0

        cats_text = ""
        if isinstance(transition, dict) and transition.get("categories"):
            for cat in transition["categories"][:3]:
                if isinstance(cat, dict):
                    cats_text += f"\n- **{cat.get('risk_driver', 'Unknown')}**: {cat.get('explanation', '')[:200]}"

        opp_text = ""
        if isinstance(opportunities, dict) and opportunities.get("opportunities"):
            for opp in opportunities["opportunities"][:3]:
                if isinstance(opp, dict):
                    opp_text += f"\n- **{opp.get('title', 'Opportunity')}**: {opp.get('description', '')[:200]}"

        return f"""## 3. Strategy
*(Framework: ISSB IFRS S2 §§ 10–30 | TCFD: Strategy)*

### Scenario Analysis
This assessment evaluates climate risks and opportunities under **{scenario.upper()}**
(Scenario data source: NASA NEX-GDDP-CMIP6 ensemble median; time horizon: {year}).

Three scenarios are supported:
- **SSP1-2.6** (low emissions, strong policy action): lower physical risk, higher transition risk
- **SSP2-4.5** (intermediate): balanced physical and transition risk profile
- **SSP5-8.5** (high emissions, limited policy action): highest physical risk, lower near-term transition risk

### Portfolio Exposure Summary
- **Properties assessed:** {n_props}
- **Sector:** {sector}
- **Primary exposure:** See physical risk scorecard in Section 5

### Transition Risk Strategy
{n_trans_cats} transition risk drivers identified. Key drivers:
{cats_text if cats_text else "*(Requires ANTHROPIC_API_KEY for AI-generated transition risk analysis)*"}

*(Data type: AI-generated | Scenario: {scenario} | Year: {year})*

### Climate Opportunity Strategy
Identified opportunities:
{opp_text if opp_text else "*(Requires ANTHROPIC_API_KEY for AI-generated opportunity analysis)*"}

### Resilience Assessment
The organisation's portfolio should be evaluated for:
1. **Physical resilience:** Adaptation measures at high-risk properties (score > 60)
2. **Transition resilience:** Decarbonisation roadmap aligned to IEA NZE / NGFS scenarios
3. **Nature resilience:** Biodiversity and ecosystem service dependencies per TNFD LEAP

*(Data type: AI-generated)*"""

    def _risk_management(self, scenario: str) -> str:
        return f"""## 4. Risk Management
*(Framework: ISSB IFRS S2 §§ 31–38 | TCFD: Risk Management)*

### Methodology
Physical climate risk is scored using a **deterministic feature-based approach**:

1. Raw indicators collected from open-access data sources (FEMA, USGS, NOAA, NASA, WRI)
2. Each indicator normalised to 0–100 scale using calibrated bounds
3. Hazard category score: `0.5 × max(features) + 0.5 × mean(remaining features)`
4. Overall physical risk: highest hazard weighted ×2, averaged across all applicable hazards
5. Rating: Very Low (0–20) | Low (21–40) | Moderate (41–60) | High (61–80) | Very High (81–100)

### Data Sources
| Hazard | Primary Sources | Data Type |
|--------|----------------|-----------|
| Wildfire | NASA FIRMS, LANDFIRE, NASA NEX-GDDP | Observed + Scenario |
| Inland Flood | FEMA NFHL, USGS 3DEP, NASA NEX-GDDP | Observed + Scenario |
| Coastal Flood | USGS 3DEP, NOAA SLR, FEMA NFHL | Observed |
| Heat Stress | NASA NEX-GDDP-CMIP6 | Scenario |
| Drought | US Drought Monitor, WRI Aqueduct | Observed + Modelled |
| Wind/Hurricane | NOAA IBTrACS, NOAA Storm Events | Observed |

Scenario used: **{scenario.upper()}** (CMIP6 multi-model median)

### Controls and Validation
- All stub providers explicitly flagged with `DataType.MISSING`
- Evidence tags applied to every material claim
- Human review triggered when overall confidence < 70% or physical risk score > 60
- Financial estimates only generated when explicit financial assumptions are provided

### Scope Limitation
This screening assessment is **not** a substitute for:
- Site-level engineering or geotechnical assessment
- Catastrophe (CAT) modelling
- Insurance underwriting surveys
- Certified flood elevation certificates"""

    def _metrics_and_targets(self, physical: dict, company: dict) -> str:
        scores_text = ""
        for pid, result in physical.items():
            if isinstance(result, dict):
                scores_text += f"\n| {pid[:12]}... | {result.get('overall_score', 'N/A'):.1f} |" if isinstance(result.get('overall_score'), float) else f"\n| {pid[:12]}... | N/A |"

        emissions = company.get("emissions")
        energy = company.get("energy_use")
        water = company.get("water_use")

        metrics_text = ""
        if emissions:
            metrics_text += f"\n- **GHG Emissions:** {emissions:,.0f} tCO₂e/yr *(Data type: User-provided)*"
        else:
            metrics_text += "\n- **GHG Emissions:** Not provided *(Data gap)*"
        if energy:
            metrics_text += f"\n- **Energy Use:** {energy:,.0f} MWh/yr *(Data type: User-provided)*"
        else:
            metrics_text += "\n- **Energy Use:** Not provided *(Data gap)*"
        if water:
            metrics_text += f"\n- **Water Use:** {water:,.0f} m³/yr *(Data type: User-provided)*"
        else:
            metrics_text += "\n- **Water Use:** Not provided *(Data gap)*"

        return f"""## 5. Metrics and Targets
*(Framework: ISSB IFRS S2 §§ 39–50 | TCFD: Metrics & Targets)*

### Physical Risk Scores
| Property ID | Overall Score (0–100) |
|-------------|----------------------|{scores_text}

### Operational Metrics
{metrics_text}

### Targets
*No formal climate targets have been entered. To include targets, provide:*
- *Base year and baseline emissions/energy/water*
- *Target year and reduction %*
- *Alignment to SBTi, Paris Agreement, or national standards*

### Adaptation Actions
For properties with score > 60, recommended next steps include:
- Commission site-level hazard engineering assessment
- Engage with insurance market for climate-informed coverage review
- Evaluate capital expenditure on resilience retrofits"""

    def _appendix(
        self,
        data_gaps: list[str],
        assumptions: list[str],
        confidence: float,
        scenario: str,
        year: int,
    ) -> str:
        gaps_text = "\n".join(f"- {g}" for g in data_gaps[:20]) if data_gaps else "- None identified"
        assumptions_text = "\n".join(f"- {a}" for a in assumptions) if assumptions else "- Standard defaults applied"

        return f"""## 6. Appendix

### A. Data Source Registry
All data sources are open-access unless noted. See individual hazard scorers for per-feature citations.

| Source | URL | Data Type |
|--------|-----|-----------|
| NASA NEX-GDDP-CMIP6 | https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/ | Scenario/Modelled |
| FEMA NFHL | https://www.fema.gov/flood-maps | Observed |
| USGS 3DEP | https://www.usgs.gov/3d-elevation-program | Observed |
| NOAA Tides & Currents | https://www.tidesandcurrents.noaa.gov/sltrends/ | Observed |
| US Drought Monitor | https://www.drought.gov/ | Observed |
| WRI Aqueduct | https://www.wri.org/aqueduct | Modelled |
| NASA FIRMS | https://firms.modaps.eosdis.nasa.gov/ | Observed |
| NOAA IBTrACS | https://www.ncei.noaa.gov/products/international-best-track-archive | Observed |
| GBIF | https://www.gbif.org/ | Observed |

### B. Assumptions
{assumptions_text}

### C. Data Gaps
{gaps_text}

### D. Confidence
**Overall assessment confidence:** {confidence:.0%}

Confidence is the weighted average of feature-level confidences across all scored properties.
Features from stub providers contribute zero confidence. A score below 70% triggers human review.

### E. Limitations
1. This is a **screening-level** assessment — not engineering-grade loss modelling.
2. Feature normalization bounds are calibrated for representative US building stock. Non-US
   properties require local calibration.
3. Scenario projections are ensemble medians; actual outcomes may vary significantly.
4. Nature risk analysis requires GBIF, IUCN, ENCORE, and WDPA data integrations
   (currently stubs) for full TNFD LEAP alignment.
5. Financial impact estimates are not provided where financial assumptions are absent.

*Scenario: {scenario.upper()} | Time horizon: {year}*
*Standards: ISSB IFRS S2, TCFD, TNFD LEAP*"""

    # ──────────────────────────── helpers ────────────────────────────────────

    def _top_physical_risks(self, physical: dict) -> str:
        if not physical:
            return "No physical risk results available."
        rows = []
        for pid, r in physical.items():
            if isinstance(r, dict) and isinstance(r.get("overall_score"), float):
                rows.append((pid, r["overall_score"]))
        rows.sort(key=lambda x: x[1], reverse=True)
        if not rows:
            return "Physical risk scores not yet available."
        lines = []
        for pid, score in rows[:5]:
            lines.append(f"- Property `{pid[:12]}...`: Overall score {score:.1f}/100 *(Data type: Modelled)*")
        return "\n".join(lines)
