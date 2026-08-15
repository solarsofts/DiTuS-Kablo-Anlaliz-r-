from __future__ import annotations

from dataclasses import dataclass

from ucd.models.project import CableData

SUPPORTED = "SUPPORTED"
REFERENCE_ONLY = "REFERENCE_ONLY"
BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CableModelApplicability:
    status: str
    production_physics_allowed: bool
    reference_workflow_allowed: bool
    reasons: tuple[str, ...]
    trace: tuple[str, ...]

    @property
    def summary(self) -> str:
        if self.status == SUPPORTED:
            return "Tek damarlı, zırhsız IEC/IEEE üretim fiziği kapsamında."
        return "Üretim fizik motoru kapsamı dışında; katalog/kaynak/rapor/BOQ için REFERENCE_ONLY."


def _armour_present(cable: CableData) -> bool:
    if float(cable.armour_loss_factor) > 1e-12:
        return True
    return any(
        "ARMOUR" in str(layer.layer_type).upper() or "ZIRH" in str(layer.layer_type).upper()
        for layer in cable.layers
    )


def evaluate_cable_model_applicability(cable: CableData) -> CableModelApplicability:
    """Return the single source of truth for FAZ 6.9 cable-model scope.

    Production electrical/thermal/bonding physics in the current branch is
    intentionally limited to single-core, unarmoured MV/HV cable systems.
    Unsupported constructions may remain in the project for traceable catalog
    reference, source capture, reporting and procurement, but must never fall
    through to the production physics as if they were supported.
    """

    reasons: list[str] = []
    trace: list[str] = []
    try:
        n = int(cable.conductors_per_cable)
    except (TypeError, ValueError):
        n = 0
    trace.append(f"conductors_per_cable={n}")
    trace.append(f"construction_type={str(cable.construction_type or '').strip() or 'UNSPECIFIED'}")

    if n < 1:
        reasons.append("Kablo başına iletken sayısı en az 1 olmalıdır.")
        return CableModelApplicability(BLOCKED, False, False, tuple(reasons), tuple(trace))

    if n != 1:
        reasons.append(
            "Çok damarlı kablo için IEC 60287 T1 geometrik faktörü G ve buna bağlı iç termal model uygulanmamıştır."
        )

    armour = _armour_present(cable)
    trace.append(f"armour_present={armour}")
    if armour:
        reasons.append(
            "Zırhlı kablo için fiziksel zırh kayıp/empedans ağı uygulanmamıştır; λ2 tek başına üretim fiziği sayılmaz."
        )

    if reasons:
        return CableModelApplicability(REFERENCE_ONLY, False, True, tuple(reasons), tuple(trace))
    return CableModelApplicability(SUPPORTED, True, True, (), tuple(trace))


def require_production_physics(cable: CableData, *, engine_label: str) -> CableModelApplicability:
    result = evaluate_cable_model_applicability(cable)
    if not result.production_physics_allowed:
        detail = " ".join(result.reasons) or "Kablo modeli üretim fiziği kapsamında değildir."
        raise ValueError(
            f"MODEL_APPLICABILITY_{result.status}: {engine_label} çalıştırılamaz. {detail} "
            "Bu kablo REFERENCE_ONLY olarak katalog/kaynak/rapor/BOQ iş akışında tutulabilir."
        )
    return result
