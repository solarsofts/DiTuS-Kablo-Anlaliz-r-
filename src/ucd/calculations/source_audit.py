from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose
from typing import Any

from ucd.models.project import ProjectData, ProjectSourceAuditData, SourceValueRecord


@dataclass
class SourceAuditIssue:
    issue_id: str
    severity: str
    title: str
    parameter_key: str = ""
    source_references: list[str] = field(default_factory=list)
    disposition: str = "UNRESOLVED"
    notes: str = ""


@dataclass
class SourceAuditReport:
    source_name: str
    scope: str
    issue_count: int
    critical_count: int
    high_count: int
    medium_count: int
    missing_data_count: int
    issues: list[SourceAuditIssue] = field(default_factory=list)
    excluded_scopes: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def status(self) -> str:
        if self.critical_count:
            return "CRITICAL_CONFLICTS"
        if self.high_count:
            return "HIGH_CONFLICTS"
        if self.issue_count or self.missing_data_count:
            return "CONDITIONAL"
        return "PASS"


def _canonical_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return text.casefold()
    return value


def _values_equal(left: Any, right: Any) -> bool:
    a = _canonical_value(left)
    b = _canonical_value(right)
    if isinstance(a, float) and isinstance(b, float):
        return isclose(a, b, rel_tol=1.0e-9, abs_tol=1.0e-12)
    return a == b


def _source_refs(records: list[SourceValueRecord]) -> list[str]:
    return sorted({record.source_reference for record in records if record.source_reference})


def audit_source_data(audit: ProjectSourceAuditData) -> SourceAuditReport:
    """Return a deterministic audit without resolving contradictory sources.

    Explicit source conflicts are authoritative.  The automatic pass adds a
    conflict only when the same parameter key contains different values and no
    explicit conflict already covers that key.
    """

    issues: list[SourceAuditIssue] = []
    explicit_keys: set[str] = set()
    record_by_id = {record.record_id: record for record in audit.records}

    for conflict in audit.conflicts:
        explicit_keys.add(conflict.parameter_key)
        records = [record_by_id[item] for item in conflict.record_ids if item in record_by_id]
        issues.append(SourceAuditIssue(
            conflict.conflict_id,
            conflict.severity.upper(),
            conflict.title,
            conflict.parameter_key,
            _source_refs(records),
            conflict.disposition,
            conflict.notes,
        ))

    grouped: dict[str, list[SourceValueRecord]] = {}
    for record in audit.records:
        grouped.setdefault(record.parameter_key, []).append(record)

    for parameter_key, records in sorted(grouped.items()):
        if parameter_key in explicit_keys or len(records) < 2:
            continue
        distinct: list[SourceValueRecord] = []
        for record in records:
            if not any(_values_equal(record.value, prior.value) for prior in distinct):
                distinct.append(record)
        if len(distinct) > 1:
            values = ", ".join(f"{item.value} {item.unit}".strip() for item in distinct)
            issues.append(SourceAuditIssue(
                f"AUTO-{len(issues) + 1:03d}",
                "HIGH",
                f"Aynı parametre için farklı kaynak değerleri: {values}",
                parameter_key,
                _source_refs(records),
                "UNRESOLVED",
                "Program değerlerden birini sessizce seçmez; tasarım girdisi kullanıcı tarafından teyit edilmelidir.",
            ))

    for index, missing in enumerate(audit.missing_required_data, start=1):
        issues.append(SourceAuditIssue(
            f"MISSING-{index:03d}",
            "MEDIUM",
            f"Nihai tasarım için eksik veri: {missing}",
            "missing_required_data",
            [],
            "REQUIRED_FOR_FINAL",
        ))

    critical = sum(issue.severity == "CRITICAL" for issue in issues)
    high = sum(issue.severity == "HIGH" for issue in issues)
    medium = sum(issue.severity == "MEDIUM" for issue in issues)
    missing_count = sum(issue.issue_id.startswith("MISSING-") for issue in issues)
    return SourceAuditReport(
        source_name=audit.source_name,
        scope=audit.scope,
        issue_count=len(issues) - missing_count,
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        missing_data_count=missing_count,
        issues=issues,
        excluded_scopes=list(audit.excluded_scopes),
        notes=audit.notes,
    )


def audit_project_sources(project: ProjectData) -> SourceAuditReport:
    return audit_source_data(project.source_audit)


def render_source_audit(report: SourceAuditReport) -> str:
    lines = [
        f"Kaynak: {report.source_name or 'Tanımlanmamış'}",
        f"Kapsam: {report.scope}",
        f"Durum: {report.status}",
        f"Çelişki: {report.issue_count}  |  Kritik: {report.critical_count}  |  Yüksek: {report.high_count}",
        f"Nihai tasarım eksik verisi: {report.missing_data_count}",
    ]
    if report.excluded_scopes:
        lines.append("Kapsam dışı: " + ", ".join(report.excluded_scopes))
    if report.notes:
        lines.extend(["", report.notes])
    if report.issues:
        lines.append("\nBULGULAR")
    for issue in report.issues:
        refs = f" [{'; '.join(issue.source_references)}]" if issue.source_references else ""
        lines.append(f"• {issue.severity} — {issue.title}{refs}")
        if issue.notes:
            lines.append(f"  {issue.notes}")
    return "\n".join(lines)
