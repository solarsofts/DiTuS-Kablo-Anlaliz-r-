from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ucd.models.project import TransientLoadProfile


@dataclass(frozen=True)
class LoadCycleMetrics:
    """Dimensionless load-cycle metrics relative to the cycle peak current.

    ``current_load_factor`` is the time-average current divided by the peak
    current. ``loss_load_factor_mu`` is the time-average of squared current
    divided by peak-current squared, i.e. the IEC 60853 loss-load factor μ for
    the represented load shape. ``rms_current_factor`` is sqrt(μ).
    """

    duration_h: float
    peak_multiplier: float
    current_load_factor: float
    loss_load_factor_mu: float
    rms_current_factor: float


def _segments(profile: TransientLoadProfile) -> tuple[tuple[float, float, float], ...]:
    points = sorted(profile.points, key=lambda item: float(item.time_h))
    if len(points) < 2:
        raise ValueError(f"{profile.profile_id}: en az iki yük noktası gereklidir.")
    duration = float(profile.duration_h)
    if duration <= 0.0:
        raise ValueError(f"{profile.profile_id}: profil süresi sıfırdan büyük olmalıdır.")
    if abs(float(points[0].time_h)) > 1e-9 or abs(float(points[-1].time_h) - duration) > 1e-9:
        raise ValueError(f"{profile.profile_id}: profil 0 h'den süre sonuna kadar tanımlanmalıdır.")
    segments: list[tuple[float, float, float]] = []
    previous = float(points[0].time_h)
    for left, right in zip(points, points[1:]):
        t0 = float(left.time_h)
        t1 = float(right.time_h)
        if t0 < previous - 1e-12 or t1 <= t0:
            raise ValueError(f"{profile.profile_id}: zaman noktaları artan ve benzersiz olmalıdır.")
        y0 = float(left.current_multiplier)
        y1 = float(right.current_multiplier)
        if y0 < 0.0 or y1 < 0.0:
            raise ValueError(f"{profile.profile_id}: akım çarpanı negatif olamaz.")
        segments.append((t1 - t0, y0, y1))
        previous = t1
    return tuple(segments)


def load_cycle_metrics(profile: TransientLoadProfile) -> LoadCycleMetrics:
    """Return exact time-weighted load and loss-load factors for a profile.

    STEP uses the left-hand ordinate over each interval, matching the transient
    solver's step interpolation. LINEAR integrates the piecewise-linear current
    and current-squared functions analytically. Factors are normalized to the
    maximum current represented by the cycle, not to an arbitrary design-current
    reference multiplier.
    """

    segments = _segments(profile)
    interpolation = str(profile.interpolation or "STEP").upper()
    if interpolation not in {"STEP", "LINEAR"}:
        raise ValueError(f"{profile.profile_id}: interpolation STEP veya LINEAR olmalıdır.")
    duration = float(profile.duration_h)
    peak = max(float(point.current_multiplier) for point in profile.points)
    if peak <= 0.0:
        return LoadCycleMetrics(duration, 0.0, 0.0, 0.0, 0.0)

    current_integral = 0.0
    square_integral = 0.0
    for dt, y0, y1 in segments:
        if interpolation == "STEP":
            current_integral += dt * y0
            square_integral += dt * y0 * y0
        else:
            current_integral += dt * 0.5 * (y0 + y1)
            # Integral of the square of a line joining y0 and y1.
            square_integral += dt * (y0 * y0 + y0 * y1 + y1 * y1) / 3.0
    load_factor = current_integral / (duration * peak)
    mu = square_integral / (duration * peak * peak)
    # Round-off protection only; values outside [0, 1] indicate invalid input.
    load_factor = min(1.0, max(0.0, load_factor))
    mu = min(1.0, max(0.0, mu))
    return LoadCycleMetrics(duration, peak, load_factor, mu, sqrt(mu))
