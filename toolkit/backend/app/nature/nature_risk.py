"""
Nature risk module following TNFD LEAP process:
L - Locate (where do assets interface with nature?)
E - Evaluate (what are dependencies and impacts?)
A - Assess (material risks and opportunities)
P - Prepare (disclosure and response)
All outputs labelled as AI-generated screening.
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

SECTOR_NATURE_DEPENDENCIES = {
    "Real Estate": ["land use", "water", "soil quality", "biodiversity corridor"],
    "Agriculture": ["soil health", "pollinators", "water", "climate regulation", "biodiversity"],
    "Mining": ["land use change", "water extraction", "tailings/pollution", "biodiversity loss"],
    "Utilities": ["water extraction", "land use", "aquatic ecosystem disruption"],
    "Industrials": ["raw materials", "water", "land use"],
    "Financials": ["financed emissions", "financed land use change"],
}

SECTOR_NATURE_IMPACTS = {
    "Real Estate": ["habitat loss (construction)", "impervious surface (stormwater runoff)", "urban heat island"],
    "Agriculture": ["soil degradation", "water extraction", "pesticide runoff", "deforestation risk"],
    "Mining": ["habitat destruction", "water contamination", "tailings spills"],
    "Utilities": ["fish passage barriers (hydro)", "water temperature changes", "land clearing"],
    "Industrials": ["pollution discharge", "waste generation", "land contamination"],
}


class NatureRiskEngine:
    def assess(
        self,
        sector: str,
        industry: str,
        properties: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        risks = []

        # L — Locate
        risks.append(self._locate_interface(sector, industry, properties))

        # E — Evaluate dependencies
        risks.append(self._evaluate_dependencies(sector, industry))

        # E — Evaluate impacts
        risks.append(self._evaluate_impacts(sector, industry))

        # A — Assess transition risk (regulation, markets)
        risks.append(self._nature_transition_risk(sector, industry))

        # A — Biodiversity proximity
        for prop in properties[:3]:  # limit to first 3 for MVP
            risks.append(self._biodiversity_proximity(prop))

        return risks

    def _locate_interface(self, sector, industry, properties) -> Dict:
        prop_count = len(properties)
        return {
            "category": "TNFD LEAP — Locate",
            "dependency_or_impact": "Geographic interface with nature",
            "description": (
                f"Portfolio of {prop_count} properties screened for nature interface. "
                f"Key nature interfaces for {sector} include: "
                f"{', '.join(SECTOR_NATURE_DEPENDENCIES.get(sector, ['land use', 'water']))}. "
                f"High-sensitivity ecosystems (wetlands, forests, coastal zones) require "
                f"Priority Location assessment per TNFD guidance."
            ),
            "severity": "Moderate",
            "time_horizon": "current",
            "confidence": "low",
            "evidence": [
                "TNFD LEAP Guidance v1.0: https://tnfd.global/",
                "IBAT (Integrated Biodiversity Assessment Tool) recommended for site-level screening",
            ],
            "data_gaps": [
                "Ecosystem type at each property location not available",
                "Protected area proximity not assessed at this screening tier",
            ],
            "tnfd_leap_step": "L — Locate",
            "data_source_type": "ai_generated",
        }

    def _evaluate_dependencies(self, sector, industry) -> Dict:
        deps = SECTOR_NATURE_DEPENDENCIES.get(sector, ["land use", "water"])
        return {
            "category": "TNFD LEAP — Evaluate Dependencies",
            "dependency_or_impact": f"Nature dependencies for {sector}",
            "description": (
                f"{sector} operations depend on ecosystem services including: "
                f"{', '.join(deps)}. Degradation of these services can increase "
                f"operating costs, disrupt supply chains, and affect asset insurability. "
                f"ENCORE database maps these dependencies at sector level."
            ),
            "severity": "Moderate",
            "time_horizon": "2040",
            "confidence": "low",
            "evidence": [
                "ENCORE Nature Dependencies Tool: https://www.encorenature.org/",
                "TNFD LEAP v1.0",
            ],
            "data_gaps": [
                "Site-level ecosystem service valuation not performed",
                "Supplier ecosystem dependency not assessed",
            ],
            "tnfd_leap_step": "E — Evaluate dependencies",
            "data_source_type": "ai_generated",
        }

    def _evaluate_impacts(self, sector, industry) -> Dict:
        impacts = SECTOR_NATURE_IMPACTS.get(sector, ["land use change", "pollution"])
        return {
            "category": "TNFD LEAP — Evaluate Impacts",
            "dependency_or_impact": f"Nature impacts for {sector}",
            "description": (
                f"Material nature impacts for {sector}/{industry} include: "
                f"{', '.join(impacts)}. "
                f"These may attract regulatory action under emerging biodiversity frameworks "
                f"(EU Biodiversity Strategy, EUDR, Kunming-Montreal GBF 30x30 target)."
            ),
            "severity": "Moderate",
            "time_horizon": "2040",
            "confidence": "low",
            "evidence": [
                "Kunming-Montreal Global Biodiversity Framework (30×30 target)",
                "EU Biodiversity Strategy 2030",
                "ENCORE: https://www.encorenature.org/",
            ],
            "data_gaps": [
                "Biodiversity footprint measurement not performed",
                "Supply chain nature impacts not assessed",
            ],
            "tnfd_leap_step": "E — Evaluate impacts",
            "data_source_type": "ai_generated",
        }

    def _nature_transition_risk(self, sector, industry) -> Dict:
        return {
            "category": "Nature Transition Risk",
            "dependency_or_impact": "Regulatory and market exposure to nature loss",
            "description": (
                f"Emerging nature-related regulation (EU EUDR, EU Nature Restoration Law, "
                f"national biodiversity net gain requirements) creates transition risk for "
                f"land-using sectors. Investors are beginning to apply nature risk screens. "
                f"For {sector}, failure to address nature dependencies may affect access to "
                f"sustainability-linked financing."
            ),
            "severity": "Low",
            "time_horizon": "2040",
            "confidence": "very_low",
            "evidence": [
                "TNFD Final Recommendations v1.0: https://tnfd.global/",
                "Kunming-Montreal GBF",
            ],
            "data_gaps": [
                "Nature-related financial disclosure not yet mandatory in most jurisdictions",
                "Quantitative impact metrics not established for this asset class",
            ],
            "tnfd_leap_step": "A — Assess risks",
            "data_source_type": "ai_generated",
        }

    def _biodiversity_proximity(self, prop: Dict) -> Dict:
        lat = prop.get("latitude", 0)
        lon = prop.get("longitude", 0)
        name = prop.get("name", "Unknown property")
        return {
            "category": "Biodiversity Proximity Screening",
            "dependency_or_impact": f"Proximity to protected areas and sensitive habitats — {name}",
            "description": (
                f"Property at ({lat:.4f}, {lon:.4f}) has not been screened for proximity to "
                f"IUCN protected areas, Key Biodiversity Areas (KBAs), or Ramsar wetlands at this tier. "
                f"Site-level biodiversity screening is recommended using IBAT, WDPA, or Protected Planet. "
                f"Proximity to IUCN Category I–IV areas within 1km triggers enhanced due diligence."
            ),
            "severity": "Unknown",
            "time_horizon": "current",
            "confidence": "very_low",
            "evidence": [
                "Protected Planet WDPA: https://www.protectedplanet.net/",
                "IUCN Red List: https://api.iucnredlist.org/",
                "GBIF occurrence data: https://www.gbif.org/",
            ],
            "data_gaps": [
                "WDPA proximity analysis not performed — requires spatial query",
                "KBA proximity not assessed",
                "GBIF species occurrence screening not performed",
            ],
            "tnfd_leap_step": "L — Locate (site-level)",
            "data_source_type": "ai_generated",
        }
