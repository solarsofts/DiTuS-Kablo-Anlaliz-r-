from __future__ import annotations

from dataclasses import dataclass
from math import log10

from ucd.calculations.bonding_accessories import resolve_bonding_accessory_plan
from ucd.models.project import BondingSystemData, SvlCandidate, SvlSystemData


REFERENCE = (
    "IEEE Std 575-2014 Clauses 6.9, 7.5-7.6 / CIGRE TB 797 insulation-coordination "
    "engineering preselection; frequency-dependent EMT validation remains required"
)


class SvlInputError(ValueError):
    pass


@dataclass(frozen=True)
class SvlCandidateCheck:
    candidate_id: str
    display_name: str
    continuous_required_rms_v: float
    mcov_rms_v: float
    continuous_margin_v: float
    continuous_ok: bool
    tov_required_rms_v: float
    tov_duration_s: float
    tov_withstand_rms_v: float | None
    tov_ok: bool | None
    lead_inductive_drop_peak_v: float
    residual_voltage_peak_v: float
    protective_level_peak_v: float
    protected_limit_peak_v: float | None
    protection_ok: bool | None
    required_energy_kj: float
    energy_capacity_kj: float
    energy_ok: bool | None
    required_discharge_current_ka: float
    nominal_discharge_current_ka: float
    discharge_current_ok: bool | None
    connection_ok: bool
    failed_checks: tuple[str, ...]
    pending_checks: tuple[str, ...]
    status: str
    score: float


@dataclass(frozen=True)
class SvlSelectionResult:
    reference: str
    recommended_candidate_id: str
    recommended_display_name: str
    normal_standing_voltage_rms_v: float
    emergency_standing_voltage_rms_v: float
    continuous_required_rms_v: float
    worst_bonding_lead_length_m: float
    checks: tuple[SvlCandidateCheck, ...]
    notes: tuple[str, ...]
    trace: tuple[str, ...]

    @property
    def has_recommendation(self) -> bool:
        return bool(self.recommended_candidate_id)

    def trace_lines(self) -> list[str]:
        lines = [
            f"Referans durumu: {self.reference}",
            f"Normal standing voltage = {self.normal_standing_voltage_rms_v:.3f} V rms",
            f"Acil standing voltage = {self.emergency_standing_voltage_rms_v:.3f} V rms",
            f"Sürekli uygulanan tasarım gerilimi = {self.continuous_required_rms_v:.3f} V rms",
            f"En uzun bonding lead = {self.worst_bonding_lead_length_m:.3f} m",
        ]
        for check in self.checks:
            lines.extend([
                f"Aday {check.display_name} [{check.candidate_id}] — {check.status}",
                f"  MCOV: gereken={check.continuous_required_rms_v:.3f} V, aday={check.mcov_rms_v:.3f} V, "
                f"marj={check.continuous_margin_v:.3f} V ({'PASS' if check.continuous_ok else 'FAIL'})",
                "  TOV: " + (
                    f"gereken={check.tov_required_rms_v:.3f} V / {check.tov_duration_s:.3f} s, "
                    f"aday={check.tov_withstand_rms_v:.3f} V ({'PASS' if check.tov_ok else 'FAIL'})"
                    if check.tov_ok is not None and check.tov_withstand_rms_v is not None
                    else "değerlendirilmedi"
                ),
                f"  Koruma seviyesi: residual={check.residual_voltage_peak_v:.3f} V + "
                f"lead={check.lead_inductive_drop_peak_v:.3f} V = {check.protective_level_peak_v:.3f} V peak; "
                + (
                    f"izin={check.protected_limit_peak_v:.3f} V ({'PASS' if check.protection_ok else 'FAIL'})"
                    if check.protection_ok is not None and check.protected_limit_peak_v is not None
                    else "yalıtım koordinasyonu değerlendirilmedi"
                ),
                "  Enerji: " + (
                    f"gereken={check.required_energy_kj:.3f} kJ, aday={check.energy_capacity_kj:.3f} kJ "
                    f"({'PASS' if check.energy_ok else 'FAIL'})"
                    if check.energy_ok is not None else "değerlendirilmedi"
                ),
                "  Deşarj akımı: " + (
                    f"gereken={check.required_discharge_current_ka:.3f} kA, aday={check.nominal_discharge_current_ka:.3f} kA "
                    f"({'PASS' if check.discharge_current_ok else 'FAIL'})"
                    if check.discharge_current_ok is not None else "değerlendirilmedi"
                ),
            ])
            if check.failed_checks:
                lines.append("  Başarısız: " + "; ".join(check.failed_checks))
            if check.pending_checks:
                lines.append("  Bekleyen: " + "; ".join(check.pending_checks))
        if self.has_recommendation:
            lines.append(f"Önerilen aday = {self.recommended_display_name} [{self.recommended_candidate_id}]")
        else:
            lines.append("Önerilen aday = YOK")
        lines.extend(f"Not: {note}" for note in self.notes)
        return lines


def _positive(name: str, value: float, allow_zero: bool = False) -> float:
    number = float(value)
    if (allow_zero and number < 0) or (not allow_zero and number <= 0):
        raise SvlInputError(f"{name} {'negatif olamaz' if allow_zero else 'sıfırdan büyük olmalı'}: {value}")
    return number


def _tov_withstand(candidate: SvlCandidate, duration_s: float) -> float | None:
    """Log-time interpolation of the user/manufacturer supplied TOV envelope.

    Extrapolation is intentionally not used.  A duration outside the supplied
    envelope is treated as incomplete candidate data.
    """

    points = sorted(
        (
            (float(candidate.tov_1s_rms_v), 1.0),
            (float(candidate.tov_10s_rms_v), 10.0),
            (float(candidate.tov_100s_rms_v), 100.0),
        ),
        key=lambda item: item[1],
    )
    valid = [(voltage, seconds) for voltage, seconds in points if voltage > 0]
    if not valid or duration_s <= 0:
        return None
    if duration_s < valid[0][1] or duration_s > valid[-1][1]:
        if abs(duration_s - valid[0][1]) < 1e-12:
            return valid[0][0]
        if abs(duration_s - valid[-1][1]) < 1e-12:
            return valid[-1][0]
        return None
    for (v1, t1), (v2, t2) in zip(valid, valid[1:]):
        if t1 <= duration_s <= t2:
            if abs(t2 - t1) < 1e-15:
                return min(v1, v2)
            ratio = (log10(duration_s) - log10(t1)) / (log10(t2) - log10(t1))
            return v1 + ratio * (v2 - v1)
    return valid[-1][0]


def _candidate_display(candidate: SvlCandidate) -> str:
    parts = [candidate.manufacturer.strip(), candidate.model.strip()]
    text = " ".join(part for part in parts if part)
    return text or candidate.candidate_id


def solve_svl_selection(
    svl: SvlSystemData,
    bonding: BondingSystemData,
    normal_standing_voltage_rms_v: float,
) -> SvlSelectionResult:
    """Evaluate an editable SVL candidate list against a project duty envelope.

    The routine is a deterministic selection/coordination layer.  It does not
    create lightning/switching energy or fault TOV values.  Those quantities
    must be supplied from a verified fault/EMT study or approved project data.
    """

    normal = _positive("Normal metalik kılıf gerilimi", normal_standing_voltage_rms_v, allow_zero=True)
    emergency_multiplier = _positive("Acil yük standing-voltage çarpanı", svl.emergency_voltage_multiplier)
    emergency = normal * emergency_multiplier
    continuous_margin = 1.0 + _positive(
        "Sürekli gerilim marjı", svl.continuous_voltage_margin_percent, allow_zero=True
    ) / 100.0
    continuous_required = max(normal, emergency) * continuous_margin

    accessory_plan = resolve_bonding_accessory_plan(bonding)
    required_box_ids = {
        item.link_box_id for item in accessory_plan.items
        if item.svl_requirement == "REQUIRED" and item.status == "VALID"
    }
    worst_lead = max(
        (float(box.lead_length_m) for box in bonding.link_boxes if box.link_box_id in required_box_ids),
        default=0.0,
    )
    lead_l_h = _positive("Bonding lead endüktansı", svl.lead_inductance_uh_per_m, allow_zero=True) * 1e-6 * worst_lead
    di_dt_a_s = _positive("Darbe akım yükselme hızı", svl.current_rise_ka_per_us, allow_zero=True) * 1e9
    lead_drop = lead_l_h * di_dt_a_s

    protection_fraction = _positive("Koruyucu seviye kullanım oranı", svl.maximum_protective_level_fraction)
    if protection_fraction > 1.0:
        raise SvlInputError("Koruyucu seviye kullanım oranı 0-1 aralığında olmalı.")
    protected_values = [
        float(svl.joint_interrupt_impulse_withstand_peak_v),
        float(svl.jacket_impulse_withstand_peak_v),
    ]
    protected_values = [value for value in protected_values if value > 0]
    protected_limit = min(protected_values) * protection_fraction if protected_values else None

    energy_required = float(svl.required_energy_kj)
    if energy_required < 0:
        raise SvlInputError("Gerekli SVL enerjisi negatif olamaz.")
    energy_required_with_margin = energy_required * (
        1.0 + _positive("Enerji marjı", svl.energy_margin_percent, allow_zero=True) / 100.0
    )
    discharge_required = float(svl.required_discharge_current_ka)
    if discharge_required < 0:
        raise SvlInputError("Gerekli deşarj akımı negatif olamaz.")

    requested_connection = svl.connection_mode.strip().upper()
    checks: list[SvlCandidateCheck] = []
    for candidate in svl.candidates:
        mcov = _positive(f"{candidate.candidate_id} MCOV", candidate.mcov_rms_v)
        continuous_ok = mcov >= continuous_required
        failed: list[str] = []
        pending: list[str] = []
        if not continuous_ok:
            failed.append("MCOV sürekli/acil standing-voltage gereksiniminin altında")

        tov_required = float(svl.fault_tov_rms_v)
        tov_duration = float(svl.fault_tov_duration_s)
        if tov_required > 0 and tov_duration > 0:
            tov_limit = _tov_withstand(candidate, tov_duration)
            if tov_limit is None:
                tov_ok: bool | None = None
                pending.append("TOV eğrisi gerekli süreyi kapsamıyor")
            else:
                tov_ok = tov_limit >= tov_required
                if not tov_ok:
                    failed.append("50/60 Hz fault-TOV dayanımı yetersiz")
        else:
            tov_limit = None
            tov_ok = None
            pending.append("Fault-TOV gerilim/süre girdisi yok")

        residual = _positive(
            f"{candidate.candidate_id} residual voltage", candidate.residual_voltage_peak_v,
            allow_zero=True,
        )
        protective_level = residual + lead_drop
        if protected_limit is None or residual <= 0 or svl.current_rise_ka_per_us <= 0:
            protection_ok: bool | None = None
            pending.append("Yalıtım koordinasyonu için BIL/residual/di-dt verileri tamamlanmalı")
        else:
            protection_ok = protective_level <= protected_limit
            if not protection_ok:
                failed.append("SVL residual + bonding-lead endüktif gerilimi yalıtım koordinasyon sınırını aşıyor")

        if energy_required > 0:
            energy_ok: bool | None = candidate.energy_capacity_kj >= energy_required_with_margin
            if not energy_ok:
                failed.append("SVL enerji kapasitesi yetersiz")
        else:
            energy_ok = None
            pending.append("EMT kaynaklı enerji gereksinimi girilmedi")

        if discharge_required > 0:
            discharge_ok: bool | None = candidate.nominal_discharge_current_ka >= discharge_required
            if not discharge_ok:
                failed.append("Nominal deşarj akımı yetersiz")
        else:
            discharge_ok = None
            pending.append("Gerekli deşarj akımı girilmedi")

        options = {item.strip().upper() for item in candidate.connection_options.split(",") if item.strip()}
        connection_ok = not options or requested_connection in options
        if not connection_ok:
            failed.append(f"Aday {requested_connection} bağlantısını desteklemiyor")

        if failed:
            status = "FAIL"
        elif pending:
            status = "CONDITIONAL"
        else:
            status = "PASS"

        evaluated_passes = sum([
            1 if continuous_ok else 0,
            1 if tov_ok is True else 0,
            1 if protection_ok is True else 0,
            1 if energy_ok is True else 0,
            1 if discharge_ok is True else 0,
            1 if connection_ok else 0,
        ])
        status_bonus = {"PASS": 1000.0, "CONDITIONAL": 100.0, "FAIL": 0.0}[status]
        oversize_penalty = max(0.0, mcov - continuous_required) / max(continuous_required, 1.0)
        score = status_bonus + 10.0 * evaluated_passes - oversize_penalty

        checks.append(
            SvlCandidateCheck(
                candidate.candidate_id,
                _candidate_display(candidate),
                continuous_required,
                mcov,
                mcov - continuous_required,
                continuous_ok,
                tov_required,
                tov_duration,
                tov_limit,
                tov_ok,
                lead_drop,
                residual,
                protective_level,
                protected_limit,
                protection_ok,
                energy_required_with_margin,
                float(candidate.energy_capacity_kj),
                energy_ok,
                discharge_required,
                float(candidate.nominal_discharge_current_ka),
                discharge_ok,
                connection_ok,
                tuple(failed),
                tuple(pending),
                status,
                score,
            )
        )

    ordered = sorted(checks, key=lambda item: (-item.score, item.mcov_rms_v, item.residual_voltage_peak_v))
    recommended = next((item for item in ordered if item.status == "PASS"), None)
    if recommended is None:
        recommended = next((item for item in ordered if item.status == "CONDITIONAL"), None)

    notes = [
        "SVL aday seçimi, üretici tarafından doğrulanmış MCOV, TOV, residual-voltage, enerji ve deşarj-akımı verileriyle yenilenmelidir.",
        "Fault-TOV ve transient enerji yazılım tarafından uydurulmaz; onaylı kısa-devre/EMT çalışmasından veya proje şartnamesinden alınır.",
        "Bonding lead yüksek frekans gerilim katkısı v=L·di/dt ile en uzun SVL lead'i üzerinden muhafazakâr değerlendirilir.",
        "CONDITIONAL sonucu satın alma/onay anlamına gelmez; bekleyen hesap ve üretici verileri tamamlanmalıdır.",
    ]
    if any(candidate.source.upper().startswith("ILLUSTRATIVE") for candidate in svl.candidates):
        notes.append("ILLUSTRATIVE kaynaklı örnek adaylar yalnız arayüz/test içindir; satın alma seçiminde kullanılamaz.")
    if worst_lead > bonding.maximum_bonding_lead_length_m:
        notes.append(
            f"En uzun SVL bonding lead {worst_lead:.3f} m, bonding proje kriteri "
            f"{bonding.maximum_bonding_lead_length_m:.3f} m üzerinde."
        )

    trace = (
        f"connection_mode={requested_connection}",
        f"candidate_count={len(svl.candidates)}",
        f"normal_standing_voltage={normal:.6f} V",
        f"emergency_multiplier={emergency_multiplier:.6f}",
        f"continuous_margin={continuous_margin:.6f}",
        f"fault_tov={svl.fault_tov_rms_v:.6f} V / {svl.fault_tov_duration_s:.6f} s",
        f"lead_length={worst_lead:.6f} m",
        f"lead_inductance={svl.lead_inductance_uh_per_m:.6f} uH/m",
        f"current_rise={svl.current_rise_ka_per_us:.6f} kA/us",
        f"lead_drop={lead_drop:.6f} V peak",
        f"protected_limit={protected_limit if protected_limit is not None else 'NA'} V peak",
        f"energy_required_with_margin={energy_required_with_margin:.6f} kJ",
    )

    return SvlSelectionResult(
        REFERENCE,
        recommended.candidate_id if recommended else "",
        recommended.display_name if recommended else "",
        normal,
        emergency,
        continuous_required,
        worst_lead,
        tuple(ordered),
        tuple(notes),
        trace,
    )
