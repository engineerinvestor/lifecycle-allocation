"""Tests for YAML profile loading."""

import os
import tempfile

import pytest

from lifecycle_allocation.io.loaders import load_profile


class TestLoadProfile:
    def test_young_saver(self) -> None:
        profile, market, curve, constraints = load_profile("examples/profiles/young_saver.yaml")
        assert profile.age == 25
        assert profile.retirement_age == 67
        assert profile.investable_wealth == 25_000
        assert profile.after_tax_income == 70_000
        assert profile.risk_tolerance == 7
        assert profile.income_model.type == "growth"
        assert profile.income_model.g == 0.02
        assert market.mu == 0.05
        assert market.borrowing_spread == 0.015
        assert curve.type == "constant"
        assert curve.rate == 0.02

    def test_mid_career(self) -> None:
        profile, market, curve, constraints = load_profile("examples/profiles/mid_career.yaml")
        assert profile.age == 45
        assert profile.investable_wealth == 500_000
        assert profile.income_model.type == "flat"

    def test_near_retirement(self) -> None:
        profile, market, curve, constraints = load_profile(
            "examples/profiles/near_retirement.yaml"
        )
        assert profile.age == 60
        assert profile.risk_tolerance == 3

    def test_minimal_profile(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("age: 35\ninvestable_wealth: 50000\nrisk_tolerance: 5\n")
            f.flush()
            try:
                profile, market, curve, constraints = load_profile(f.name)
                assert profile.age == 35
                assert profile.retirement_age == 67  # default
                assert market.mu == 0.05  # default
            finally:
                os.unlink(f.name)

    def test_missing_required_field_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("retirement_age: 67\nrisk_tolerance: 5\n")
            f.flush()
            try:
                with pytest.raises((KeyError, TypeError)):
                    load_profile(f.name)
            finally:
                os.unlink(f.name)

    def test_invalid_yaml_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("just a string\n")
            f.flush()
            try:
                with pytest.raises(ValueError, match="YAML mapping"):
                    load_profile(f.name)
            finally:
                os.unlink(f.name)
