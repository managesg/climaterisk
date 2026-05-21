"""
Disclosure report generator — ISSB IFRS S2 / TCFD / TNFD aligned.
Clearly distinguishes AI-generated narrative from observed/modeled data.
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DISCLOSURE_DISCLAIMER = (
    "IMPORTANT — DATA QUALITY AND LIMITATIONS: This disclosure summary was generated "
    "using open-access screening data and AI-assisted interpretation. It is not a substitute "
    "for site-specific engineering assessment, detailed catastrophe modelling, or professional "
    "climate risk advisory. Financial estimates are not provided unless supported by specific "
    "financial assumptions. AI-generated narrative is clearly labelled. All data sources, "
    "scenarios, and confidence levels are disclosed per ISSB IFRS S2 requirements."
)


class DisclosureGenerator:
    def generate(
        self,
        company: Dict,
        properties: List[Dict],
        physical_risk_results: List[Dict],
        transition_risks: List[Dict],
        nature_risks: List[Dict],
        opportunities: List[Dict],
        scenario: str,
        time_horizon: str,
        confidence: float,
        data_gaps: List[str],
        assumptions: List[str],
    ) -> Dict[str, Any]:
        top_physical = self._top_physical(physical_risk_results)
        top_transition = self._top_transition(transition_risks)
        top_nature = self._top_nature(nature_risks)
        top_opps = self._top_opps(opportunities)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "disclaimer": DISCLOSURE_DISCLAIMER,
            "framework_alignment": ["ISSB IFRS S2", "TCFD", "TNFD"],
            "scenario": scenario,
            "time_horizon": time_horizon,
            "overall_confidence": confidence,

            "1_executive_summary": self._executive_summary(
                company, top_physical, top_transition, top_nature, top_opps, data_gaps
            ),
            "2_governance": self._governance(company),
            "3_strategy": self._strategy(
                company, physical_risk_results, transition_risks, opportunities, scenario
            ),
            "4_risk_management": self._risk_management(physical_risk_results, scenario),
            "5_metrics_and_targets": self._metrics_targets(
                company, properties, physical_risk_results
            ),
            "6_appendix": self._appendix(
                physical_risk_results, scenario, time_horizon, data_gaps, assumptions
            ),
        }

    def _top_physical(self, results):
        top = sorted(results, key=lambda x: x.get("overall_score", 0), reverse=True)
        return top[:3]

    def _top_transition(self, risks):
        order = {"High": 3, "Very High": 4, "Moderate": 2, "Low": 1, "Very Low": 0}
        return sorted(risks, key=lambda x: order.get(x.get("severity", "Low"), 1), reverse=True)[:3]

    def _top_nature(self, risks):
        return risks[:3]

    def _top_opps(self, opps):
        return opps[:3]

    def _executive_summary(self, company, top_physical, top_transition, top_nature, top_opps, data_gaps):
        phys_summary = []
        for r in top_physical:
            phys_summary.append(
                f"{r.get('property_name', r.get('property_id', '?'))}: "
                f"{r.get('overall_rating', '?')} ({r.get('overall_score', 0):.0f}/100) — "
                f"top hazards: {', '.join(r.get('top_hazards', ['N/A']))}"
            )
        return {
            "section": "Executive Summary",
            "data_source_type": "ai_generated",
            "top_physical_risks": phys_summary,
            "top_transition_risks": [
                f"{r.get('category')}: {r.get('risk_driver', '')[:80]}"
                for r in top_transition
            ],
            "top_nature_risks": [
                r.get("dependency_or_impact", "")[:80] for r in top_nature
            ],
            "top_opportunities": [
                o.get("title", "") for o in top_opps
            ],
            "key_data_gaps": list(set(data_gaps))[:8],
            "narrative": (
                f"[AI-GENERATED INTERPRETATION] "
                f"{company.get('name', 'The company')} ({company.get('sector', 'sector unknown')}) "
                f"has undergone open-access physical climate risk screening, transition risk analysis, "
                f"and nature risk screening across {len(top_physical)} properties. "
                f"Physical risk screening identified the following material exposures. "
                f"Transition risks are assessed against scenario {top_physical[0].get('scenario', 'N/A') if top_physical else 'N/A'}. "
                f"Data gaps noted in section 6 should be addressed before using this output for formal disclosure."
            ),
        }

    def _governance(self, company):
        return {
            "section": "Governance (ISSB S2 §6–9 / TCFD Governance)",
            "data_source_type": "ai_generated",
            "oversight_body": "Board-level oversight of climate risk recommended (audit/risk committee or dedicated sustainability committee).",
            "management_role": "Chief Sustainability Officer or equivalent senior role recommended to own climate risk process.",
            "review_cadence": "Annual climate risk review recommended; quarterly monitoring of high-risk assets.",
            "disclosure_recommendations": [
                "Board confirm climate risk is material and board has oversight responsibility",
                "Disclose management-level roles and responsibilities for climate risk",
                "Document how climate risk is integrated into enterprise risk management",
            ],
            "data_gaps_for_governance_disclosure": [
                "Current governance structure not available — user to populate",
                "Board climate competency status not assessed",
            ],
        }

    def _strategy(self, company, physical_results, transition_risks, opportunities, scenario):
        high_risk_props = [r for r in physical_results if r.get("overall_score", 0) > 60]
        return {
            "section": "Strategy (ISSB S2 §10–24 / TCFD Strategy)",
            "data_source_type": "ai_generated",
            "scenario_used": scenario,
            "scenario_source": "NGFS 2023 / NASA NEX-GDDP-CMIP6",
            "portfolio_exposure_summary": (
                f"{len(high_risk_props)} of {len(physical_results)} properties scored High or Very High "
                f"on physical risk screening under scenario {scenario}."
            ),
            "resilience_strategy_recommendations": [
                "Prioritise high-risk assets for detailed site-level assessment",
                "Develop asset-level adaptation plans for properties scoring >60",
                "Integrate physical risk into capital expenditure planning",
                "Review insurance coverage for high-risk assets annually",
            ],
            "opportunity_summary": [
                {
                    "title": o.get("title"),
                    "category": o.get("category"),
                    "time_horizon": o.get("time_horizon"),
                }
                for o in opportunities
            ],
            "financial_resilience_note": (
                "Financial impact of physical and transition risks has not been quantified "
                "as required financial assumptions (asset values, carbon prices, energy costs) "
                "are not available. Quantification is required for ISSB S2 compliance where material."
            ),
        }

    def _risk_management(self, physical_results, scenario):
        sources = set()
        for r in physical_results:
            for h in r.get("hazard_results", []):
                for f in h.get("feature_scores", []):
                    if f.get("source_name"):
                        sources.add(f["source_name"])
        return {
            "section": "Risk Management (ISSB S2 §25–31 / TCFD Risk Management)",
            "methodology": "Open-access screening tier using normalised feature scoring (0–100 per hazard). Category score = 0.5 × max_feature + 0.5 × avg_remaining_features.",
            "hazard_set": ["Wildfire", "Inland Flood", "Coastal Flood / Sea Level Rise", "Heat Stress", "Drought / Water Stress", "Wind / Hurricane / Severe Storm"],
            "scenario_framework": f"Physical: NASA NEX-GDDP-CMIP6 ({scenario}). Transition: NGFS 2023.",
            "data_sources_used": sorted(sources),
            "scoring_guardrails": [
                "No financial losses fabricated",
                "Missing data imputed at median (50/100) and flagged as data gap",
                "All AI-generated content labelled as such",
                "Screening results not presented as engineering-grade modelling",
            ],
            "controls": [
                "Human review required for confidence < 0.70",
                "Human review required for High/Very High risk affecting disclosure language",
                "Evidence validation step in workflow",
            ],
            "data_quality_statement": (
                "This screening uses open-access proxies. "
                "Replace proxy estimates with site-specific data for formal disclosure."
            ),
        }

    def _metrics_targets(self, company, properties, physical_results):
        high_risk = [r for r in physical_results if r.get("overall_score", 0) > 60]
        hazard_scores = {}
        for result in physical_results:
            for h in result.get("hazard_results", []):
                hname = h.get("hazard", "")
                score = h.get("category_score", 0)
                if hname not in hazard_scores or score > hazard_scores[hname]:
                    hazard_scores[hname] = score
        return {
            "section": "Metrics and Targets (ISSB S2 §29–41 / TCFD Metrics)",
            "properties_screened": len(physical_results),
            "high_risk_property_count": len(high_risk),
            "high_risk_property_ids": [r.get("property_id", "") for r in high_risk],
            "peak_hazard_scores": hazard_scores,
            "financial_metrics_note": (
                "High-risk asset value, revenue at risk, and insurance gap not calculated. "
                "Requires asset replacement values and business interruption values."
            ),
            "emissions_metrics": {
                "scope_1_tco2e": company.get("emissions", {}).get("scope_1_tco2e") if company.get("emissions") else None,
                "scope_2_tco2e": company.get("emissions", {}).get("scope_2_tco2e") if company.get("emissions") else None,
                "data_source": "user_provided",
                "note": "Emissions data not provided — required for ISSB S2 Metrics section.",
            },
            "energy_metrics": {
                "energy_use_mwh": company.get("energy_use_mwh"),
                "note": "Energy consumption not provided — required for ISSB S2 energy intensity metrics.",
            },
            "adaptation_actions": [
                "Develop per-asset adaptation plan for high-risk properties",
                "Set EUI reduction target for energy-intensive assets",
                "Engage insurer on risk reduction measures",
            ],
            "recommended_targets": [
                "Reduce portfolio average physical risk score by 10 points by 2030 through adaptation",
                "Commission detailed assessment for all High/Very High risk assets within 12 months",
                "Achieve net-zero Scope 1 & 2 by [year — user to set]",
            ],
        }

    def _appendix(self, physical_results, scenario, time_horizon, data_gaps, assumptions):
        sources = []
        for r in physical_results:
            for h in r.get("hazard_results", []):
                for f in h.get("feature_scores", []):
                    if f.get("source_name") and f.get("source_url"):
                        entry = {
                            "source": f["source_name"],
                            "url": f.get("source_url", ""),
                            "data_type": f.get("data_source_type", ""),
                        }
                        if entry not in sources:
                            sources.append(entry)
        return {
            "section": "Appendix",
            "sources": sources[:30],
            "scenario": scenario,
            "time_horizon": time_horizon,
            "assumptions": assumptions + [
                "All proxy scores are coarse estimates derived from geographic position and user-provided attributes",
                "Missing features imputed at median score (50/100) — conservative approach",
                "Physical hazard scores reflect screening tier only, not catastrophe loss modelling",
                f"Transition risk assessed under {scenario} scenario",
                "Nature risk follows TNFD LEAP framework at a conceptual screening level",
            ],
            "data_gaps": list(set(data_gaps)),
            "limitations": [
                "Open-access screening only — not suitable as standalone disclosure without site-specific validation",
                "Climate projections use coarse spatial proxies, not point-level CMIP6 data",
                "Financial impact of risks not quantified without financial assumptions",
                "Nature risk assessed at sector/industry level, not site-level",
                "This assessment does not constitute legal, financial, or engineering advice",
            ],
            "confidence_statement": (
                "Overall confidence is rated based on data completeness across feature inputs. "
                "Features with missing data are imputed at median and flagged. "
                "Confidence < 0.70 triggers human review requirement."
            ),
        }
