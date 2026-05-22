from ..models.enums import HazardType, RiskRating


def compute_category_score(feature_scores: list[float]) -> float:
    """Compute hazard category score.

    Formula: 0.5 * max_feature + 0.5 * mean(remaining_features)
    When only one feature exists, returns that score directly.
    """
    if not feature_scores:
        return 0.0
    if len(feature_scores) == 1:
        return feature_scores[0]
    max_score = max(feature_scores)
    # Remove one occurrence of the max when computing remaining average
    remaining = feature_scores.copy()
    remaining.remove(max_score)
    avg_remaining = sum(remaining) / len(remaining)
    return 0.5 * max_score + 0.5 * avg_remaining


def rating_from_score(score: float) -> RiskRating:
    if score <= 20:
        return RiskRating.VERY_LOW
    if score <= 40:
        return RiskRating.LOW
    if score <= 60:
        return RiskRating.MODERATE
    if score <= 80:
        return RiskRating.HIGH
    return RiskRating.VERY_HIGH


def compute_overall_physical_risk(hazard_scores: dict[HazardType, float]) -> float:
    """Compute portfolio-level physical risk.

    Weights the highest-scoring hazard twice, then averages across all.
    Excludes hazards with zero score (not applicable).
    """
    applicable = {h: s for h, s in hazard_scores.items() if s > 0}
    if not applicable:
        return 0.0
    scores = list(applicable.values())
    max_score = max(scores)
    total = max_score + sum(scores)    # highest counted twice
    return total / (len(scores) + 1)
