from __future__ import annotations

from math import sqrt


class PhaseGeometryError(ValueError):
    pass


def normalize_phase_order(phase_order: str) -> str:
    order = str(phase_order or "ABC").strip().upper()
    if len(order) != 3 or sorted(order) != ["A", "B", "C"]:
        raise PhaseGeometryError(f"Faz sırası ABC permütasyonu olmalı: {phase_order}")
    return order


def normalize_arrangement(arrangement: str) -> str:
    key = str(arrangement or "").strip().lower()
    if key in {"trefoil", "üçgen", "ucgen"}:
        return "TREFOIL"
    if key in {"flat", "düz", "duz"}:
        return "FLAT"
    if key in {"vertical", "düşey", "dusey"}:
        return "VERTICAL"
    if key in {"single", "tek", "tek kablo"}:
        return "SINGLE"
    if key in {"custom", "özel", "ozel"}:
        return "CUSTOM"
    if key in {"duct", "duct_bank", "duct bank"}:
        return "DUCT_BANK"
    raise PhaseGeometryError(f"Bilinmeyen faz formasyonu: {arrangement}")


def phase_slot_offsets_m(
    arrangement: str,
    spacing_m: float,
    phase_order: str = "ABC",
) -> dict[str, tuple[float, float]]:
    """Return relative (x, downward-y) phase slot coordinates.

    The first slot is the shallowest slot.  Translation to an absolute burial
    depth is intentionally left to the thermal/installation caller.  Bonding
    uses only relative distances.
    """

    normalized = normalize_arrangement(arrangement)
    order = normalize_phase_order(phase_order)
    spacing = float(spacing_m)
    if spacing <= 0:
        raise PhaseGeometryError(f"Faz eksen aralığı sıfırdan büyük olmalı: {spacing}")

    if normalized == "TREFOIL":
        h = sqrt(3.0) * spacing / 2.0
        slots = ((0.0, 0.0), (-spacing / 2.0, h), (spacing / 2.0, h))
    elif normalized == "FLAT":
        slots = ((-spacing, 0.0), (0.0, 0.0), (spacing, 0.0))
    elif normalized == "VERTICAL":
        slots = ((0.0, 0.0), (0.0, spacing), (0.0, 2.0 * spacing))
    elif normalized == "SINGLE":
        return {order[0]: (0.0, 0.0)}
    elif normalized == "CUSTOM":
        raise PhaseGeometryError("CUSTOM_POSITIONS_REQUIRED: CUSTOM formasyon için açık x-y koordinatları gereklidir.")
    else:  # DUCT_BANK is an installation type, never a phase formation.
        raise PhaseGeometryError(
            "ARRANGEMENT_INSTALLATION_CONFLATION: DUCT_BANK faz formasyonu değildir; "
            "TREFOIL, FLAT, VERTICAL, SINGLE veya CUSTOM kullanın."
        )
    return {phase: slots[index] for index, phase in enumerate(order)}
