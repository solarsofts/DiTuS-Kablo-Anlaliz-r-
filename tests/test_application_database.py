from pathlib import Path

from ucd.calculations.application_database import (
    load_application_cable_database,
    save_application_cable_database,
)
from ucd.models.project import CableCatalogRecord


def test_application_cable_database_persists_independently_from_project(tmp_path: Path) -> None:
    path = tmp_path / "cable_database.ditus-cable-catalog.json"
    library = load_application_cable_database(path)
    builtin_count = len(library.records)
    library.records.append(
        CableCatalogRecord(
            record_id="USER-TEST-001",
            manufacturer="User",
            series="Project-independent",
            model="1x500/50 Al",
            voltage_class="20.3/35 kV",
            conductor_material="Al",
            conductor_area_mm2=500.0,
        )
    )
    save_application_cable_database(library, path)

    loaded = load_application_cable_database(path)
    assert len(loaded.records) >= builtin_count + 1
    assert any(record.record_id == "USER-TEST-001" for record in loaded.records)
    assert loaded.package_source == "APPLICATION_DATABASE"
