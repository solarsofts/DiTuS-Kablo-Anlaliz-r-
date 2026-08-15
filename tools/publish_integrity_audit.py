from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import ipaddress
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from zipfile import BadZipFile, ZipFile

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - exercised by the fail-closed dependency test
    PdfReader = None  # type: ignore[assignment]


AUDIT_SCHEMA_VERSION = "1.0"
RULE_SET_ID = "DITUS_PUBLISH_INTEGRITY_PHASE1_V1"
MAX_TEXT_BYTES = 32 * 1024 * 1024

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".pytest_cache",
    ".release_acceptance",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
}

TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".conf",
    ".css",
    ".csv",
    ".htm",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".rst",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".rtf",
}
OOXML_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
ZIP_XML_EXTENSIONS = {".odt", ".ods", ".odp"}
UNSUPPORTED_DOCUMENT_EXTENSIONS = {".doc", ".xls", ".ppt", ".pages", ".numbers", ".key"}

SENSITIVE_JSON_KEYS = {
    "author",
    "author_name",
    "created_by",
    "creator",
    "email",
    "e_mail",
    "last_modified_by",
    "lastmodifiedby",
    "local_path",
    "manager",
    "phone",
    "prepared_by",
    "preparedby",
    "source_path",
    "tc_kimlik",
    "tckn",
    "telefon",
    "user_name",
    "username",
    "windows_user",
}
SAFE_IDENTITY_METADATA_VALUES = {
    "",
    "(anonymous)",
    "anonymous",
    "(unspecified)",
    "unspecified",
    "python-docx",
    "reportlab",
    "ditus",
    "ditus kablo analizör",
}

# Regression values are stored as normalized SHA-256 fingerprints rather than
# clear-text personal/project identifiers. They supplement general patterns;
# they are not the primary detection mechanism.
REGRESSION_FINGERPRINTS: tuple[tuple[str, int, str], ...] = (
    ("approved_designer_signature", 6, "d3002f32cf8b7900d404cb48abecb00348232eb86a98b104fbb00ef168a1a3b5"),
    ("legacy_person_given_name_ascii", 5, "afed2539bd02b81a291a6a00b99c66b755b2dd21a48ad08eb48e8f068e879766"),
    ("legacy_person_given_name_tr", 5, "2ea4eb3a9754b9972b818e02cd74a17da233f165ee61ac51ab661f7867183d1e"),
    ("legacy_person_full_name_ascii", 10, "34b3bcc6843a3dae41f2337879bf9789856fe2de0654e2cc7c2505e24dcbbd19"),
    ("legacy_person_full_name_tr", 10, "2fe2d9b4c133e7df9ab3725b6be037be35c7213cbbf86a8c999d3e3d1d81c2e6"),
    ("legacy_org_1_tr", 4, "8a3b9a443e6a592ce2962b82ab36774ece878a99042bc27621b11f348d16063a"),
    ("legacy_org_1_ascii", 4, "6e2969af72be8c601e4102c4b7ba857bcfc4bb7833c5026a46a287c3b7651c8a"),
    ("legacy_org_2_tr", 5, "c96867fb585954efd5c4d500dc2898bc25657ed54a5b87216803b0334fd3510b"),
    ("legacy_org_2_ascii", 5, "afe7e62d256e5b456d05d82cba10b7d3d76e5250042cc7b724eac70cf5e25a5f"),
    ("legacy_project_1", 5, "31b9c29efc8ca0a5cc177c75077e4b680df8f25cfdf034d97583b28e8ad9e0a3"),
    ("legacy_project_2", 4, "b3087547f4b048f9e99005a7ce862004bdeb4144751c574c274d66f3e503f6cc"),
)

APPROVED_SIGNATURE_PATHS = {
    "src/ucd/ui/main_window.py",
    "tests/test_ui_full_canvas_contract.py",
    "EVENING_ACCEPTANCE_CHECKLIST_v0.16.9.4.15.md",
    "IDENTITY_SIGNATURE_AUDIT_v0.16.9.4.15.md",
    "RELEASE_NOTES_v0.16.9.4.15.md",
}

EMAIL_RE = re.compile(
    r"(?<![A-Z0-9._%+\-])(?:[A-Z0-9._%+\-]{1,64})@(?:[A-Z0-9\-]{1,63}\.)+[A-Z]{2,63}(?![A-Z0-9\-])",
    re.IGNORECASE,
)
WINDOWS_USER_PATH_RE = re.compile(
    r"(?i)(?<![A-Z0-9_])(?:[A-Z]:\\Users\\[^\\\r\n:*?\"<>|]+(?:\\[^\\\r\n:*?\"<>|]+)*)"
)
WINDOWS_ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?<![A-Z0-9_])(?:[A-Z]:\\(?!\\)(?:[^\\\r\n:*?\"<>|]+\\)*[^\\\r\n:*?\"<>|]*)"
)
UNC_PATH_RE = re.compile(r"(?<!\\)\\\\[A-Za-z0-9.-]{1,63}\\[A-Za-z0-9$ ._-]{1,255}(?:\\[^\r\n]*)?")
POSIX_LOCAL_PATH_RE = re.compile(
    r"(?<![A-Z0-9_])/(?:home|Users|mnt|tmp|var/tmp)/[^\s\"'<>]+",
    re.IGNORECASE,
)
TR_PHONE_RE = re.compile(
    r"(?<!\d)(?:(?:(?:\+|00)90)[\s().-]*|0[\s().-]*)(?:5\d{2}|[234]\d{2})"
    r"[\s().-]*\d{3}[\s().-]*\d{2}[\s().-]*\d{2}(?!\d)"
)
TCKN_CANDIDATE_RE = re.compile(r"(?<![\d.,])[1-9]\d{10}(?!\d)")
IPV4_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    surface: str
    location: str
    fingerprint: str
    redacted_preview: str
    allowed: bool = False
    allowance_reason: str = ""


@dataclass
class ScanStats:
    files_seen: int = 0
    filenames_scanned: int = 0
    text_files_scanned: int = 0
    text_characters_scanned: int = 0
    pdf_files_seen: int = 0
    pdf_files_scanned: int = 0
    pdf_pages_seen: int = 0
    pdf_pages_scanned: int = 0
    pdf_text_characters_scanned: int = 0
    pdf_metadata_fields_scanned: int = 0
    pdf_annotations_scanned: int = 0
    pdf_form_fields_scanned: int = 0
    pdf_attachments_scanned: int = 0
    ooxml_files_scanned: int = 0
    archive_members_scanned: int = 0
    json_identity_fields_scanned: int = 0
    unsupported_binary_files: int = 0
    unscannable_objects: int = 0


@dataclass
class AuditResult:
    schema_version: str
    rule_set_id: str
    root_name: str
    rule_set_sha256: str
    status: str
    stats: ScanStats
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def blocking_findings(self) -> list[Finding]:
        return [item for item in self.findings if not item.allowed]

    @property
    def allowed_findings(self) -> list[Finding]:
        return [item for item in self.findings if item.allowed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "rule_set_id": self.rule_set_id,
            "root_name": self.root_name,
            "rule_set_sha256": self.rule_set_sha256,
            "status": self.status,
            "stats": asdict(self.stats),
            "blocking_finding_count": len(self.blocking_findings),
            "allowed_finding_count": len(self.allowed_findings),
            "finding_counts_by_rule": dict(Counter(item.rule_id for item in self.findings)),
            "findings": [asdict(item) for item in self.findings],
            "errors": list(self.errors),
        }


def _rule_set_sha256() -> str:
    payload = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "rule_set_id": RULE_SET_ID,
        "text_extensions": sorted(TEXT_EXTENSIONS),
        "ooxml_extensions": sorted(OOXML_EXTENSIONS),
        "unsupported_document_extensions": sorted(UNSUPPORTED_DOCUMENT_EXTENSIONS),
        "regression_fingerprints": REGRESSION_FINGERPRINTS,
        "approved_signature_paths": sorted(APPROVED_SIGNATURE_PATHS),
        "sensitive_json_keys": sorted(SENSITIVE_JSON_KEYS),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _fingerprint(value: str) -> str:
    return hashlib.sha256(_normalized(value).encode("utf-8")).hexdigest()


def _redact(value: str) -> str:
    compact = " ".join(value.replace("\x00", " ").split())
    if not compact:
        return "<empty>"
    if len(compact) <= 4:
        return "•" * len(compact)
    return f"{compact[:2]}…{compact[-2:]} (len={len(compact)})"


def _line_location(text: str, start: int) -> str:
    return f"line {text.count(chr(10), 0, max(0, start)) + 1}"


def _is_allowed(rule_id: str, relative_path: str) -> tuple[bool, str]:
    if rule_id == "regression_approved_designer_signature" and relative_path in APPROVED_SIGNATURE_PATHS:
        return True, "Approved application signature, restricted to reviewed source/test/release locations."
    return False, ""


def _finding(rule_id: str, path: str, surface: str, location: str, value: str) -> Finding:
    allowed, reason = _is_allowed(rule_id, path)
    return Finding(
        rule_id=rule_id,
        path=path,
        surface=surface,
        location=location,
        fingerprint=_fingerprint(value),
        redacted_preview=_redact(value),
        allowed=allowed,
        allowance_reason=reason,
    )


def _valid_tckn(value: str) -> bool:
    if len(value) != 11 or not value.isdigit() or value[0] == "0":
        return False
    digits = [int(char) for char in value]
    check_10 = ((sum(digits[0:9:2]) * 7) - sum(digits[1:8:2])) % 10
    check_11 = sum(digits[:10]) % 10
    return digits[9] == check_10 and digits[10] == check_11


def _is_private_or_local_ipv4(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if address.version != 4:
        return False
    networks = (
        ipaddress.ip_network((167772160, 8)),
        ipaddress.ip_network((2886729728, 12)),
        ipaddress.ip_network((3232235520, 16)),
        ipaddress.ip_network((2130706432, 8)),
        ipaddress.ip_network((2851995648, 16)),
    )
    return any(address in network for network in networks)


def _valid_tr_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0090"):
        subscriber = digits[4:]
        explicit_country = True
    elif digits.startswith("90"):
        subscriber = digits[2:]
        explicit_country = value.lstrip().startswith("+")
    elif digits.startswith("0"):
        subscriber = digits[1:]
        explicit_country = False
    else:
        return False
    if len(subscriber) != 10 or subscriber[0] not in "2345":
        return False
    # Local-format numbers must carry human phone separators. This prevents
    # floating-point engineering values from being mistaken for phone numbers.
    return explicit_country or any(char in value for char in " ()-")


def _scan_regression_fingerprints(text: str, path: str, surface: str) -> list[Finding]:
    normalized = _normalized(text)
    expected_by_length: dict[int, list[tuple[str, str]]] = {}
    for identifier, length, expected_hash in REGRESSION_FINGERPRINTS:
        expected_by_length.setdefault(length, []).append((identifier, expected_hash))

    # Regression values are person/organization/project tokens. Hash only
    # token and adjacent-token candidates instead of every character window;
    # this keeps whole-package scans linear in the number of words.
    token_re = re.compile(r"[^\W_]+(?:\.[^\W_]+)?", re.UNICODE)
    tokens = list(token_re.finditer(normalized))
    candidates: list[tuple[int, str]] = [(match.start(), match.group(0)) for match in tokens]
    for left, right in zip(tokens, tokens[1:]):
        candidates.append((left.start(), left.group(0) + " " + right.group(0)))

    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()
    for start, candidate in candidates:
        expected = expected_by_length.get(len(candidate))
        if not expected:
            continue
        candidate_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        for identifier, expected_hash in expected:
            if candidate_hash != expected_hash:
                continue
            key = (identifier, start)
            if key in seen:
                continue
            seen.add(key)
            rule_id = f"regression_{identifier}"
            findings.append(_finding(rule_id, path, surface, _line_location(normalized, start), candidate))
    return findings


def _scan_text_patterns(text: str, path: str, surface: str) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, int, int]] = set()

    def add_matches(rule_id: str, regex: re.Pattern[str], predicate: Any | None = None) -> None:
        for match in regex.finditer(text):
            value = match.group(0)
            if predicate is not None and not predicate(value):
                continue
            key = (rule_id, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            findings.append(_finding(rule_id, path, surface, _line_location(text, match.start()), value))

    add_matches("email_address", EMAIL_RE)
    add_matches("windows_user_path", WINDOWS_USER_PATH_RE)
    add_matches("windows_absolute_path", WINDOWS_ABSOLUTE_PATH_RE)
    add_matches("unc_network_path", UNC_PATH_RE)
    add_matches("posix_local_path", POSIX_LOCAL_PATH_RE)
    add_matches("turkiye_phone_number", TR_PHONE_RE, _valid_tr_phone)
    add_matches("turkiye_identity_number", TCKN_CANDIDATE_RE, _valid_tckn)
    add_matches("private_or_local_ipv4", IPV4_CANDIDATE_RE, _is_private_or_local_ipv4)
    findings.extend(_scan_regression_fingerprints(text, path, surface))
    return findings


def _identity_metadata_is_safe(value: str) -> bool:
    normalized = " ".join(_normalized(value).split())
    if normalized in SAFE_IDENTITY_METADATA_VALUES:
        return True
    if normalized.startswith("reportlab pdf library"):
        return True
    return False


def _scan_identity_metadata(value: Any, path: str, surface: str, location: str) -> list[Finding]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        findings: list[Finding] = []
        for index, item in enumerate(value):
            findings.extend(_scan_identity_metadata(item, path, surface, f"{location}[{index}]"))
        return findings
    text = str(value).strip()
    if _identity_metadata_is_safe(text):
        return []
    return [_finding("identity_metadata", path, surface, location, text)]


def _walk_json_identity_fields(value: Any, path: str, surface: str, stats: ScanStats, prefix: str = "$") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            normalized_key = re.sub(r"[^a-z0-9]+", "_", _normalized(key_text)).strip("_")
            location = f"{prefix}.{key_text}"
            if normalized_key in SENSITIVE_JSON_KEYS:
                stats.json_identity_fields_scanned += 1
                if item not in (None, "", [], {}):
                    findings.extend(_scan_identity_metadata(item, path, surface, location))
            findings.extend(_walk_json_identity_fields(item, path, surface, stats, location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_json_identity_fields(item, path, surface, stats, f"{prefix}[{index}]"))
    return findings


def _decode_text(data: bytes) -> str:
    if len(data) > MAX_TEXT_BYTES:
        raise ValueError(f"text object exceeds {MAX_TEXT_BYTES} bytes")
    for encoding in ("utf-8-sig", "utf-16", "cp1254", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("text decoding failed")


def _scan_json_payload(text: str, path: str, surface: str, stats: ScanStats) -> list[Finding]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    return _walk_json_identity_fields(payload, path, surface, stats)


def _scan_plain_text(data: bytes, path: str, surface: str, suffix: str, stats: ScanStats) -> list[Finding]:
    text = _decode_text(data)
    stats.text_characters_scanned += len(text)
    findings = _scan_text_patterns(text, path, surface)
    if suffix.lower() == ".json" or path.lower().endswith(".ucd.json"):
        findings.extend(_scan_json_payload(text, path, surface, stats))
    return findings


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _scan_ooxml_metadata(xml_bytes: bytes, path: str, member_name: str, stats: ScanStats) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return findings
    identity_tags = {"creator", "lastModifiedBy", "Manager", "Company"}
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag not in identity_tags:
            continue
        stats.json_identity_fields_scanned += 1
        value = (element.text or "").strip()
        if value:
            findings.extend(_scan_identity_metadata(value, path, f"archive:{member_name}", tag))
    return findings


def _scan_archive_bytes(data: bytes, path: str, stats: ScanStats, ooxml: bool) -> list[Finding]:
    findings: list[Finding] = []
    try:
        archive = ZipFile(io.BytesIO(data))
    except BadZipFile as exc:
        stats.unscannable_objects += 1
        return [_finding("unscannable_archive", path, "archive", "open", str(exc))]

    if ooxml:
        stats.ooxml_files_scanned += 1
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            stats.archive_members_scanned += 1
            member_name = str(PurePosixPath(info.filename))
            findings.extend(_scan_text_patterns(member_name, path, f"archive-member-name:{member_name}"))
            member_suffix = PurePosixPath(member_name).suffix.lower()
            member_data = archive.read(info)
            if member_name in {"docProps/core.xml", "docProps/app.xml"}:
                findings.extend(_scan_ooxml_metadata(member_data, path, member_name, stats))
            if member_suffix in TEXT_EXTENSIONS or member_suffix in {".rels"}:
                try:
                    findings.extend(_scan_plain_text(member_data, path, f"archive:{member_name}", member_suffix, stats))
                except ValueError as exc:
                    stats.unscannable_objects += 1
                    findings.append(_finding("unscannable_text_object", path, f"archive:{member_name}", "decode", str(exc)))
    return findings


def _pdf_metadata_items(reader: Any) -> Iterable[tuple[str, Any]]:
    metadata = getattr(reader, "metadata", None)
    if metadata:
        for key, value in dict(metadata).items():
            yield str(key), value
    xmp = getattr(reader, "xmp_metadata", None)
    if xmp:
        for attribute in (
            "dc_creator",
            "dc_contributor",
            "dc_title",
            "dc_description",
            "pdf_keywords",
            "pdf_producer",
            "xmp_creator_tool",
        ):
            try:
                value = getattr(xmp, attribute, None)
            except Exception:
                value = None
            if value not in (None, "", [], {}):
                yield f"XMP:{attribute}", value


def _scan_pdf_bytes(data: bytes, path: str, stats: ScanStats) -> list[Finding]:
    findings: list[Finding] = []
    stats.pdf_files_seen += 1
    if PdfReader is None:
        stats.unscannable_objects += 1
        return [_finding("pdf_reader_dependency_missing", path, "pdf", "import", "pypdf is not installed")]
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
    except Exception as exc:
        stats.unscannable_objects += 1
        return [_finding("unscannable_pdf", path, "pdf", "open", f"{type(exc).__name__}: {exc}")]

    if reader.is_encrypted:
        try:
            decrypted = reader.decrypt("")
        except Exception as exc:
            decrypted = 0
            findings.append(_finding("encrypted_pdf", path, "pdf", "decrypt", f"{type(exc).__name__}: {exc}"))
        if not decrypted:
            stats.unscannable_objects += 1
            if not any(item.rule_id == "encrypted_pdf" for item in findings):
                findings.append(_finding("encrypted_pdf", path, "pdf", "decrypt", "password required"))
            return findings

    stats.pdf_files_scanned += 1
    stats.pdf_pages_seen += len(reader.pages)
    extracted_non_whitespace = 0
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            stats.unscannable_objects += 1
            findings.append(_finding("unscannable_pdf_page", path, "pdf-page", f"page {index}", f"{type(exc).__name__}: {exc}"))
            continue
        stats.pdf_pages_scanned += 1
        stats.pdf_text_characters_scanned += len(text)
        extracted_non_whitespace += len("".join(text.split()))
        findings.extend(_scan_text_patterns(text, path, f"pdf-page:{index}"))

        annotations = page.get("/Annots") or []
        for annotation_index, reference in enumerate(annotations, start=1):
            try:
                annotation = reference.get_object()
            except Exception:
                continue
            stats.pdf_annotations_scanned += 1
            for key in ("/Contents", "/T", "/Subj", "/TU", "/V"):
                value = annotation.get(key)
                if value not in (None, ""):
                    findings.extend(_scan_text_patterns(str(value), path, f"pdf-annotation:{index}:{annotation_index}:{key}"))

    if len(reader.pages) > 0 and extracted_non_whitespace == 0:
        stats.unscannable_objects += 1
        findings.append(_finding("pdf_text_extraction_empty", path, "pdf", "all pages", "no extractable text"))

    for key, value in _pdf_metadata_items(reader):
        stats.pdf_metadata_fields_scanned += 1
        text = str(value)
        findings.extend(_scan_text_patterns(text, path, f"pdf-metadata:{key}"))
        if key in {"/Author", "/Creator", "XMP:dc_creator", "XMP:dc_contributor", "XMP:xmp_creator_tool"}:
            findings.extend(_scan_identity_metadata(value, path, "pdf-metadata", key))

    try:
        fields = reader.get_fields() or {}
    except Exception:
        fields = {}
    for field_name, field in fields.items():
        stats.pdf_form_fields_scanned += 1
        findings.extend(_scan_text_patterns(str(field_name), path, "pdf-form-field-name"))
        if isinstance(field, Mapping):
            for key in ("/V", "/DV", "/TU", "/TM"):
                value = field.get(key)
                if value not in (None, ""):
                    findings.extend(_scan_text_patterns(str(value), path, f"pdf-form-field:{field_name}:{key}"))

    try:
        attachments = reader.attachments
    except Exception:
        attachments = {}
    if attachments:
        for attachment_name, payloads in attachments.items():
            findings.extend(_scan_text_patterns(str(attachment_name), path, "pdf-attachment-name"))
            for attachment_index, payload in enumerate(payloads, start=1):
                stats.pdf_attachments_scanned += 1
                suffix = PurePosixPath(str(attachment_name)).suffix.lower()
                surface = f"pdf-attachment:{attachment_name}:{attachment_index}"
                if suffix in TEXT_EXTENSIONS:
                    try:
                        findings.extend(_scan_plain_text(payload, path, surface, suffix, stats))
                    except ValueError as exc:
                        stats.unscannable_objects += 1
                        findings.append(_finding("unscannable_pdf_attachment", path, surface, "decode", str(exc)))
                elif suffix == ".pdf":
                    findings.extend(_scan_pdf_bytes(payload, path, stats))
                elif suffix in OOXML_EXTENSIONS or suffix in ZIP_XML_EXTENSIONS:
                    findings.extend(_scan_archive_bytes(payload, path, stats, ooxml=suffix in OOXML_EXTENSIONS))
                else:
                    stats.unsupported_binary_files += 1
                    findings.append(_finding("unsupported_pdf_attachment", path, surface, "type", suffix or "no extension"))
    return findings


def _should_ignore(relative: Path, excluded_paths: set[str]) -> bool:
    posix = relative.as_posix()
    if posix in excluded_paths:
        return True
    return any(part in IGNORED_DIR_NAMES for part in relative.parts)


def scan_package(root: Path, excluded_paths: Iterable[str] = ()) -> AuditResult:
    root = root.resolve()
    excluded = {PurePosixPath(item).as_posix() for item in excluded_paths}
    stats = ScanStats()
    findings: list[Finding] = []
    errors: list[str] = []

    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = file_path.relative_to(root)
        if _should_ignore(relative, excluded):
            continue
        rel = relative.as_posix()
        stats.files_seen += 1
        stats.filenames_scanned += 1
        findings.extend(_scan_text_patterns(rel, rel, "package-relative-path"))
        suffix = file_path.suffix.lower()
        try:
            data = file_path.read_bytes()
        except OSError as exc:
            stats.unscannable_objects += 1
            findings.append(_finding("unreadable_file", rel, "file", "read", f"{type(exc).__name__}: {exc}"))
            continue

        if suffix == ".pdf":
            findings.extend(_scan_pdf_bytes(data, rel, stats))
        elif suffix in OOXML_EXTENSIONS:
            findings.extend(_scan_archive_bytes(data, rel, stats, ooxml=True))
        elif suffix in ZIP_XML_EXTENSIONS or suffix == ".zip":
            findings.extend(_scan_archive_bytes(data, rel, stats, ooxml=False))
        elif suffix in TEXT_EXTENSIONS or rel.lower().endswith(".ucd.json"):
            stats.text_files_scanned += 1
            try:
                findings.extend(_scan_plain_text(data, rel, "file-text", suffix, stats))
            except ValueError as exc:
                stats.unscannable_objects += 1
                findings.append(_finding("unscannable_text_file", rel, "file-text", "decode", str(exc)))
        elif suffix in UNSUPPORTED_DOCUMENT_EXTENSIONS:
            stats.unscannable_objects += 1
            findings.append(_finding("unsupported_document_format", rel, "file", "type", suffix))
        else:
            stats.unsupported_binary_files += 1

    blocking = [item for item in findings if not item.allowed]
    status = "PASS" if not blocking and not errors and stats.unscannable_objects == 0 else "FAIL"
    return AuditResult(
        schema_version=AUDIT_SCHEMA_VERSION,
        rule_set_id=RULE_SET_ID,
        root_name=root.name,
        rule_set_sha256=_rule_set_sha256(),
        status=status,
        stats=stats,
        findings=findings,
        errors=errors,
    )


def render_audit_markdown(result: AuditResult, package_version: str) -> str:
    stats = result.stats
    lines = [
        f"# Yayın Veri Bütünlüğü Denetimi — v{package_version}",
        "",
        f"- Sonuç: **{result.status}**",
        f"- Kural seti: `{result.rule_set_id}`",
        f"- Kural seti SHA-256: `{result.rule_set_sha256}`",
        f"- Engelleyici eşleşme: {len(result.blocking_findings)}",
        f"- İzin verilen, konuma bağlı eşleşme: {len(result.allowed_findings)}",
        f"- Taranamayan nesne: {stats.unscannable_objects}",
        "",
        "## Kapsama kanıtı",
        "",
        f"- Dosya adı/yolu: {stats.filenames_scanned}/{stats.files_seen}",
        f"- Metin dosyası: {stats.text_files_scanned}",
        f"- Metin karakteri: {stats.text_characters_scanned}",
        f"- PDF: {stats.pdf_files_scanned}/{stats.pdf_files_seen}",
        f"- PDF sayfası: {stats.pdf_pages_scanned}/{stats.pdf_pages_seen}",
        f"- PDF metin karakteri: {stats.pdf_text_characters_scanned}",
        f"- PDF metadata alanı: {stats.pdf_metadata_fields_scanned}",
        f"- PDF annotation/form/ek: {stats.pdf_annotations_scanned}/{stats.pdf_form_fields_scanned}/{stats.pdf_attachments_scanned}",
        f"- OOXML dosyası: {stats.ooxml_files_scanned}",
        f"- Arşiv üyesi: {stats.archive_members_scanned}",
        "",
        "## Politika",
        "",
        "Genel desenler e-posta, yerel veya mutlak dosya yolu, Türkiye telefon numarası, doğrulanmış T.C. kimlik numarası ve özel/yerel IP sınıflarını kapsar. Kimlik taşıyan metadata alanları ayrıca denetlenir. Geçmiş sızıntılar açık metin kara-listesi yerine SHA-256 regresyon parmak izleriyle korunur. İzinler yalnız tam kural ve tam dosya yolu kapsamındadır.",
        "",
        "PDF denetimi `pypdf` ile sayfa metni, metadata, annotation, form alanı ve gömülü ek yüzeylerini kapsar. Açılamayan, şifreli veya metni çıkarılamayan PDF başarı sayılmaz.",
        "",
        "## Tarihsel düzeltme",
        "",
        "`PACKAGED_TEST_RESULTS_v0.16.9.4.14.txt` ve `PUBLISH_CLEANUP_AUDIT_v0.16.9.4.14.md` içindeki PDF taraması iddiaları bu denetimin kanıtı olarak kullanılmamıştır; doğrulanmamış tarihsel kayıtlardır ve bu otomatik denetim tarafından geçersiz kılınmıştır.",
    ]
    if result.blocking_findings:
        lines.extend(["", "## Engelleyici bulgular", ""])
        for item in result.blocking_findings:
            lines.append(f"- `{item.rule_id}` · `{item.path}` · {item.surface} · {item.location} · `{item.redacted_preview}`")
    if result.allowed_findings:
        lines.extend(["", "## İzin verilen eşleşmeler", ""])
        grouped = Counter((item.rule_id, item.path) for item in result.allowed_findings)
        for (rule_id, path), count in sorted(grouped.items()):
            lines.append(f"- `{rule_id}` · `{path}` · {count} eşleşme · konuma bağlı onay")
    return "\n".join(lines) + "\n"


def render_audit_text(result: AuditResult, package_version: str) -> str:
    stats = result.stats
    return "\n".join(
        [
            f"DiTuS Kablo Analizör v{package_version}",
            "Yayın veri bütünlüğü otomatik test sonucu",
            "",
            f"SONUÇ: {result.status}",
            f"Kural seti: {result.rule_set_id}",
            f"Kural seti SHA-256: {result.rule_set_sha256}",
            f"Engelleyici eşleşme: {len(result.blocking_findings)}",
            f"İzin verilen eşleşme: {len(result.allowed_findings)}",
            f"Taranamayan nesne: {stats.unscannable_objects}",
            f"Dosya/yol taraması: {stats.filenames_scanned}/{stats.files_seen}",
            f"PDF taraması: {stats.pdf_files_scanned}/{stats.pdf_files_seen}",
            f"PDF sayfa taraması: {stats.pdf_pages_scanned}/{stats.pdf_pages_seen}",
            f"PDF metin karakteri: {stats.pdf_text_characters_scanned}",
            f"PDF metadata alanı: {stats.pdf_metadata_fields_scanned}",
            f"OOXML dosyası: {stats.ooxml_files_scanned}",
            "",
            "Bu belge elle yazılmamıştır; yapılandırılmış denetim sonucundan üretilmiştir.",
            "v0.16.9.4.14 PDF PASS iddiası bu sonuç için kanıt kabul edilmemiştir.",
        ]
    ) + "\n"


def write_audit_outputs(result: AuditResult, package_version: str, json_path: Path, text_path: Path, markdown_path: Path) -> None:
    payload = result.to_dict()
    payload["package_version"] = package_version
    payload["historical_correction"] = {
        "superseded_documents": [
            "PACKAGED_TEST_RESULTS_v0.16.9.4.14.txt",
            "PUBLISH_CLEANUP_AUDIT_v0.16.9.4.14.md",
        ],
        "reason": "The earlier PDF scan claim was not verified by a PDF text extractor.",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_path.write_text(render_audit_text(result, package_version), encoding="utf-8")
    markdown_path.write_text(render_audit_markdown(result, package_version), encoding="utf-8")


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed DiTuS publication integrity audit")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--version", required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--text", dest="text_path", type=Path, required=True)
    parser.add_argument("--markdown", dest="markdown_path", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    outputs = [args.json_path, args.text_path, args.markdown_path]
    excluded = []
    for output in outputs:
        output = output if output.is_absolute() else root / output
        try:
            excluded.append(output.resolve().relative_to(root).as_posix())
        except ValueError:
            pass
    result = scan_package(root, excluded_paths=excluded)
    resolved_outputs = [output if output.is_absolute() else root / output for output in outputs]
    for output in resolved_outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
    write_audit_outputs(result, args.version, *resolved_outputs)
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
