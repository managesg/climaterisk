"""Tests for hazard base scoring utilities."""
import pytest
from app.hazards.base import normalize, normalize_inverse, hazard_category_score


def test_normalize_midpoint():
    assert normalize(50, 0, 100) == 50.0


def test_normalize_at_lower():
    assert normalize(0, 0, 100) == 0.0


def test_normalize_at_upper():
    assert normalize(100, 0, 100) == 100.0


def test_normalize_clips_above():
    assert normalize(150, 0, 100) == 100.0


def test_normalize_clips_below():
    assert normalize(-10, 0, 100) == 0.0


def test_normalize_no_clip():
    result = normalize(150, 0, 100, clip=False)
    assert result == 150.0


def test_normalize_equal_lo_hi():
    assert normalize(50, 50, 50) == 0.0


def test_category_score_single():
    result = hazard_category_score([80.0])
    assert result == 80.0


def test_category_score_two_features():
    # max=80, remaining=[20], avg_remaining=20
    # 0.5*80 + 0.5*20 = 50
    result = hazard_category_score([80.0, 20.0])
    assert result == pytest.approx(50.0)


def test_category_score_multiple():
    scores = [90.0, 60.0, 30.0, 10.0]
    # max=90, avg_remaining = (60+30+10)/3 = 33.33
    # 0.5*90 + 0.5*33.33 = 61.67
    result = hazard_category_score(scores)
    assert result == pytest.approx(61.67, abs=0.1)


def test_category_score_empty():
    assert hazard_category_score([]) == 0.0


def test_category_score_uniform():
    result = hazard_category_score([50.0, 50.0, 50.0])
    assert result == pytest.approx(50.0)
