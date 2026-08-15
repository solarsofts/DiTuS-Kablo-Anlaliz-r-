from __future__ import annotations

from math import sqrt
from pathlib import Path

import pytest

from ucd.calculations.electrothermal_coupled import _base_circuit_currents
from ucd.calculations.installation import resolved_physical_cables, validate_installation_design
from ucd.calculations.load_cycle import load_cycle_metrics
from ucd.models.project import LoadProfilePoint, ProjectData, TransientLoadProfile, default_transient_profiles


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_circuit_load_factor_no_longer_scales_resolved_rms_current() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    circuit = section.circuits[0]
    circuit.load_current_a = 300.0
    circuit.load_factor = 0.25
    phase = section.physical_cables[0].phase
    peers = [item for item in section.physical_cables if item.circuit_id == circuit.circuit_id and item.phase == phase and item.active]
    resolved = {item.physical_cable_id: item for item in resolved_physical_cables(section)}
    assert peers
    assert sum(resolved[item.physical_cable_id].current_a for item in peers) == pytest.approx(300.0, abs=1e-9)


def test_legacy_physical_cable_load_factor_no_longer_scales_override() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    cable = section.physical_cables[0]
    cable.current_override_a = 123.0
    cable.load_factor = 0.10
    resolved = {item.physical_cable_id: item for item in resolved_physical_cables(section)}
    assert resolved[cable.physical_cable_id].current_a == pytest.approx(123.0, abs=1e-12)


def test_closed_loop_ampacity_base_current_ignores_legacy_load_factor() -> None:
    project = ProjectData()
    for section in project.installation_design.cross_sections:
        for circuit in section.circuits:
            circuit.load_current_a = 321.0
            circuit.load_factor = 0.10
    currents = _base_circuit_currents(project)
    assert currents
    assert all(value == pytest.approx(321.0, abs=1e-12) for value in currents.values())


def test_step_profile_loss_load_factor_mu_is_time_weighted_i_squared_over_peak_squared() -> None:
    profile = TransientLoadProfile(
        "STEP_TEST", "step", 4.0, "STEP",
        [
            LoadProfilePoint(0.0, 0.5),
            LoadProfilePoint(1.0, 1.0),
            LoadProfilePoint(3.0, 0.5),
            LoadProfilePoint(4.0, 0.5),
        ],
    )
    metrics = load_cycle_metrics(profile)
    # Intervals: 1 h @ 0.5, 2 h @ 1.0, 1 h @ 0.5.
    assert metrics.peak_multiplier == pytest.approx(1.0)
    assert metrics.current_load_factor == pytest.approx(0.75)
    assert metrics.loss_load_factor_mu == pytest.approx(0.625)
    assert metrics.rms_current_factor == pytest.approx(sqrt(0.625))


def test_linear_profile_loss_load_factor_uses_exact_piecewise_linear_square_integral() -> None:
    profile = TransientLoadProfile(
        "LINEAR_TEST", "linear", 2.0, "LINEAR",
        [LoadProfilePoint(0.0, 0.0), LoadProfilePoint(1.0, 1.0), LoadProfilePoint(2.0, 0.0)],
    )
    metrics = load_cycle_metrics(profile)
    assert metrics.current_load_factor == pytest.approx(0.5)
    assert metrics.loss_load_factor_mu == pytest.approx(1.0 / 3.0)


def test_default_daily_profile_exposes_real_iec60853_mu_and_ui_does_not_offer_steady_state_factor() -> None:
    profile = next(item for item in default_transient_profiles() if item.profile_id == "DAILY")
    metrics = load_cycle_metrics(profile)
    assert 0.0 < metrics.current_load_factor < 1.0
    assert metrics.current_load_factor**2 <= metrics.loss_load_factor_mu <= 1.0
    ui = (ROOT / "src/ucd/ui/installation_designer_dialog.py").read_text(encoding="utf-8")
    transient_ui = (ROOT / "src/ucd/ui/main_window.py").read_text(encoding="utf-8")
    assert "Legacy yük katsayısı" in ui
    assert "IEC 60853 kayıp-yük faktörü μ" in transient_ui


def test_non_unity_legacy_fields_are_visible_warnings_not_physics() -> None:
    project = ProjectData()
    section = project.installation_design.cross_sections[0]
    section.circuits[0].load_factor = 0.7
    section.physical_cables[0].load_factor = 0.8
    codes = {item.code for item in validate_installation_design(project.installation_design, cable_outer_diameter_m=max(project.cable.overall_diameter_mm / 1000.0, 0.001))}
    assert "LEGACY_CIRCUIT_LOAD_FACTOR_IGNORED" in codes
    assert "LEGACY_PHYSICAL_CABLE_LOAD_FACTOR_IGNORED" in codes
