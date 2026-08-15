# DiTuS Kablo Analizör — Calculation Standard Register

Version: 0.16.9.4.34  
Purpose: engineering traceability from clause identifiers to code/test evidence. No licensed standard text is reproduced.

| Standard / clause | Engineering interpretation used by DiTuS | Code / evidence | Status |
|---|---|---|---|
| IEC 60287-1-1 §2.3 | Single-core sheaths bonded at both ends: circulating-current loss is the required sheath-loss component; non-Milliken solid-bonded branch does not require an added λ1″ term. | `sheath_loss_completeness.py`; P0 tests | IMPLEMENTED_AUTHORITY_RULE |
| IEC 60287-1-1 §2.3.5 | Large segmental/Milliken conductor branch requires λ1″ from §2.3.6 with factor `F`; F is not optional provenance. | `sheath_loss_completeness.py`; P0 tests | IMPLEMENTED |
| IEC 60287-1-1 §2.3.6.1 | Sheath eddy-current λ1″ closed forms are applied only inside their single-circuit Trefoil/Flat applicability. For `m <= 0.1`, Δ1/Δ2 are neglected while λ0 remains. | `sheath_loss_completeness.py`; P0 tests | IMPLEMENTED_FAIL_CLOSED |
| IEC 60287-1-1 §2.3.6.1 Note 3 | Wire-screen constructions are treated as eddy-negligible only when the stored construction explicitly supports the note (equalizing strip or thin sheet/foil evidence); wire count alone is insufficient. | `sheath_loss_completeness.py`; P0 tests | IMPLEMENTED_PROVENANCE_RULE |
| IEC 60287-1-1 §2.3.6.1 Note 2 | Large/unusually thick aluminium sheath emits explicit applicability evidence; it is not silently treated as ordinary geometry. | `sheath_loss_completeness.py` | IMPLEMENTED_EVIDENCE |
| IEC 60287-1-1 §2.3.6.2 + IEEE 575-2014 §6.7.3.1 Eq.(1) | Unequal three-minor sectionalized cross-bonding circulating-loss ratio is the same closed form under its ideal applicability assumptions. Fixed points: 1:1:1 → 0; 2:1:2 → 0.04; p=1,q=1.2 → 0.00390625 (~0.004). | `bonding_closed_form_validation.py`; `test_phase6_7_standing_voltage_and_closed_form_oracles.py` | INDEPENDENT_ORACLE |
| IEEE 575-2014 Annex D.4 | Modified sectionalized cross-bonding ideal maximum standing-voltage factor is √3/2; reduction is ~13.4%. | same oracle/test module | INDEPENDENT_ORACLE |
| IEC 60287-1-1 §2.3.4(a) | Where spacing varies within an electrical section, reactance is length-weighted over the spacing sub-lengths. | Route/minor integration tests; bonding route contributions | IMPLEMENTED_BY_NUMERICAL_INTEGRATION |
| IEC 60287-1-1 §2.3.4(c) | At a laid end, the generic spacing allowance may be insufficient; actual/estimated spacing should be represented through the weighted method. | Geometry authority requires route-resolved spacing where available. | TRACEABILITY_RULE |
| IEC 60287-1-1 §2.3.4 Note | The cited +25% spacing allowance is not a generic factor for single-point or cross-bonded systems. | No global +25% bonding multiplier is applied. | NEGATIVE_REQUIREMENT |
| IEC 60287-2-1 §2.2.3.1 | Unequally loaded buried groups use individual cable losses in mutual thermal-rise superposition; the standard indicates an iterative rating procedure. DiTuS fixed-point coupling is an implementation interpretation, not a verbatim prescribed algorithm. | production electrothermal / multiconductor thermal tests | IMPLEMENTATION_INTERPRETATION |
| IEC 60287-2-1 §2.2.3.2 | Equally loaded identical buried groups admit the simplified equal-loading treatment. | analytical group thermal path | IMPLEMENTED |
| IEC 60287-2-1 §2.2.7.3 | Concrete-embedded duct-bank correction uses bank geometry, surrounding-soil/concrete resistivity difference, `u=L_G/r_b`; equivalent-radius formula is applicable for `y/x < 3`. | Planned dedicated `IEC_DUCT_BANK_CONCRETE_CORRECTION`; generic mixed-zone is not labeled as this clause. | VERIFIED_SCOPE_NOT_YET_PRODUCTION |
| IEC 60287-2-1 symbol `L` | Depth of laying is to cable axis or centre of trefoil. | geometry coupling / trefoil depth contract | IMPLEMENTED |

## Authority policy

`geometry_basis`, `material_field_class`, and `result_authority` are orthogonal. A layered/complex physical section may retain an analytical engineering preview for shadow validation, while the authoritative method is nodal. Legacy scalar geometry cannot exceed `DERIVED_FROM_SCALAR` authority. The generic mixed-zone preview is not claimed as a normative IEC layered-soil reduction.

## Sheath-loss provenance

The production primitive/global network computes longitudinal metallic sheath loss from solved branch currents (`Σ|I|²R`). This `network_sheath_loss_ratio` represents the same physical longitudinal/circulating sheath-loss component addressed by IEC λ1′, but through a different route-aware global network model; **no algebraic identity is claimed**. v0.16.9.4.34 adds a separate IEC/applicability-governed λ1″ layer and exposes `lambda1_rating = network_sheath_loss_ratio + lambda1_eddy` with authority/provenance. The independent cross-bonding oracle remains a longitudinal-network validation and is not evidence that the two models are algebraically identical.
