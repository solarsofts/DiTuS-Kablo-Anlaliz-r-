from __future__ import annotations

import json
from pathlib import Path

from ucd.calculations.cable_library import (
    CableLibraryInputError,
    catalog_package_from_dict,
    catalog_package_to_dict,
    merge_builtin_catalogs,
    merge_catalog_library,
)
from ucd.models.project import CableLibraryData


def load_application_cable_database(path: str | Path) -> CableLibraryData:
    """Load the reusable application database with manufacturer-free templates.

    The application database is independent from any active project. DiTuS
    contributes only seven generated generic templates; producer records exist
    only when the user imports or creates them. Project calculations use a
    copied snapshot, never the mutable database row itself.
    """
    target = CableLibraryData(
        package_name="DiTuS uygulama kablo veri tabanı",
        package_revision="0.16.9.4.37",
        package_source="APPLICATION_DATABASE",
    )
    merge_builtin_catalogs(target)
    file_path = Path(path)
    if not file_path.exists():
        return target
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        incoming = catalog_package_from_dict(raw)
    except (OSError, json.JSONDecodeError, CableLibraryInputError):
        # A corrupt user database must not prevent the application from opening;
        # manufacturer-free generic templates remain available. The UI reports save/load errors
        # when the user explicitly manages the database.
        return target
    merge_catalog_library(target, incoming, replace=True)
    return target


def save_application_cable_database(library: CableLibraryData, path: str | Path) -> Path:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = catalog_package_to_dict(library)
    temporary = file_path.with_suffix(file_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(file_path)
    return file_path
