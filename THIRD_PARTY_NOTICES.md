# DiTuS Kablo Analizör — Third-Party Notices

This document is informational and does not modify the Apache License, Version 2.0.

## 1. Source distribution model

The DiTuS source distribution is intended to contain the project source code,
project-authored documentation, tests, and project assets. Python dependencies
listed in `requirements.txt` are normally obtained separately from their
respective upstream distributions by the user's package manager; their license
terms are independent of the DiTuS Apache-2.0 license.

A distributor who creates a binary, frozen, installer, container, or otherwise
bundled distribution must re-check the exact licenses and notice obligations of
the dependency versions and binary libraries actually redistributed.

## 2. Qt / PySide6

DiTuS uses PySide6 (Qt for Python). Qt for Python is offered by The Qt Company
under open-source licensing (including LGPLv3/GPLv3 for applicable components)
and commercial licensing. The source package's reference to PySide6 does not
relicense Qt or PySide6 under Apache-2.0.

If Qt/PySide6 binaries or Qt components are redistributed with DiTuS, the
redistributor is responsible for complying with the license option applicable
to those redistributed components, including any required notices, source or
relinking obligations, and third-party component notices.

## 3. Other Python dependencies

The project currently declares direct dependencies such as `ezdxf`, `numpy`,
`scipy`, `networkx`, `matplotlib`, `shapely`, `pyproj`, `pydantic`,
`python-docx`, `reportlab`, `pypdf`, and `XlsxWriter`, plus development/test
packages such as `pytest`, `setuptools`, and `wheel`.

These packages are separate works. Their definitive copyright and license
notices are the notices shipped by the exact versions installed or redistributed.
This file intentionally does not replace those upstream license texts.

## 4. Standards and manufacturer publications

Technical standards, manufacturer catalogues, product names, trademarks, and
external publications are not relicensed by DiTuS. See `STANDARDS_NOTICE.md`
and `SOURCES.md`.

## 5. Asset provenance warning before public release

The current development package contains `assets/ditus_mascot.png`. The asset
provenance note states that it was generated for the project from a
user-supplied visual reference. Until the copyright/trademark/personality-rights
status of that reference and resulting asset is affirmatively cleared, this
file should **not** be treated as licensed for public redistribution under the
project's Apache-2.0 grant.

**Recommended public-release action:** remove or replace the mascot with a
fully original, independently designed asset whose redistribution rights are
clear, and then update this notice accordingly.

## 6. No implied endorsement

Mention of a dependency, standards organization, manufacturer, commercial
software product, or other third party does not imply sponsorship, partnership,
certification, or endorsement.
