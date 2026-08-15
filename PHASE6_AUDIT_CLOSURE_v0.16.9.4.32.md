# FAZ 6 Audit Closure — v0.16.9.4.32

Base: v0.16.9.4.31 (FAZ 7.1 baseline).

Closed findings:
- Method authority and geometry provenance are separated into `geometry_basis`, `material_field_class`, analytical `result_authority`, `authoritative_method`, and `analytical_preview_allowed`.
- Layered/complex sections no longer fail the analytical branch solely to enforce nodal authority. Analytical preview remains available for report/shadow comparison; nodal is the production authority.
- Legacy scalar geometry is capped at `DERIVED_FROM_SCALAR` authority.
- `far_field_effective_rho_km_w` was removed from new production projections/persistence. It is neither consumed nor presented as if consumed.
- Groundwater and complex/layered authority downgrades use separate reason codes.
- Negative analytical surface correction remains conservatively clamped to zero and now carries orthogonal raw/clamped evidence.
- FAZ 6.7 has a dedicated regression file covering cumulative complex standing-voltage accumulation and grounded reset.
- IEC/IEEE unequal-minor closed-form loss ratio is implemented only as an independent verification oracle against dual cross/solid primitive-network longitudinal sheath I²R loss.
- IEEE 575 Annex D.4 √3/2 standing-voltage benchmark is locked as an oracle.
- `CALCULATION_STANDARD_REGISTER.md` establishes clause→implementation/test traceability without reproducing licensed standard text.

Not claimed closed as production capability:
- IEC 60287-2-1 §2.2.7.3 concrete duct-bank correction is verified and registered, including `y/x < 3`, but remains a dedicated next implementation item. Generic mixed-zone is explicitly not relabeled as §2.2.7.3.
