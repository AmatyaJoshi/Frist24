"""SBOM parsing: CycloneDX JSON (1.2-1.6, cyclonedx-python-lib) and SPDX JSON 2.2/2.3 (spdx-tools).

Returns a flat list of components with the fields the matcher needs. PURL is the primary key
for matching; components without a PURL are kept (they feed the fuzzy path later).
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from cyclonedx.model.bom import Bom
from packageurl import PackageURL


@dataclass
class ParsedComponent:
    name: str
    version: str | None
    purl: str | None
    ecosystem: str | None
    cpe: str | None = None
    supplier: str | None = None


@dataclass
class ParsedSbom:
    format: str  # cyclonedx | spdx
    spec_version: str | None
    components: list[ParsedComponent] = field(default_factory=list)


class SbomParseError(ValueError):
    pass


def _ecosystem(purl: str | None) -> str | None:
    if not purl:
        return None
    try:
        return PackageURL.from_string(purl).type
    except ValueError:
        return None


def detect_format(data: dict) -> str:
    if data.get("bomFormat") == "CycloneDX" or "specVersion" in data and "components" in data:
        return "cyclonedx"
    if str(data.get("spdxVersion", "")).startswith("SPDX-") or "packages" in data and "SPDXID" in data:
        return "spdx"
    raise SbomParseError("Unrecognised SBOM: expected CycloneDX JSON (bomFormat) or SPDX JSON (spdxVersion)")


def parse_cyclonedx(data: dict) -> ParsedSbom:
    bom = Bom.from_json(data)  # type: ignore[attr-defined]
    out = ParsedSbom(format="cyclonedx", spec_version=str(data.get("specVersion")))
    for c in bom.components:
        purl = str(c.purl) if c.purl else None
        out.components.append(
            ParsedComponent(
                name=str(c.name),
                version=str(c.version) if c.version else None,
                purl=purl,
                ecosystem=_ecosystem(purl),
                cpe=str(c.cpe) if c.cpe else None,
                supplier=str(c.supplier.name) if c.supplier and c.supplier.name else None,
            )
        )
    return out


def parse_spdx(raw: bytes, data: dict) -> ParsedSbom:
    from spdx_tools.spdx.model import ExternalPackageRefCategory
    from spdx_tools.spdx.parser.parse_anything import parse_file

    with tempfile.NamedTemporaryFile("wb", suffix=".spdx.json", delete=False) as fh:
        fh.write(raw)
        tmp = fh.name
    try:
        doc = parse_file(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    out = ParsedSbom(format="spdx", spec_version=str(data.get("spdxVersion", "")).replace("SPDX-", "") or None)
    for p in doc.packages:
        purl = None
        for ref in p.external_references:
            if ref.category == ExternalPackageRefCategory.PACKAGE_MANAGER and ref.reference_type == "purl":
                purl = ref.locator
                break
        cpe = next((r.locator for r in p.external_references if r.reference_type.startswith("cpe")), None)
        supplier = getattr(p.supplier, "name", None) if p.supplier and not isinstance(p.supplier, str) else None
        out.components.append(
            ParsedComponent(name=p.name, version=p.version, purl=purl, ecosystem=_ecosystem(purl), cpe=cpe, supplier=supplier)
        )
    return out


def parse_sbom(raw: bytes) -> ParsedSbom:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SbomParseError(f"SBOM must be UTF-8 JSON: {e}") from e
    if not isinstance(data, dict):
        raise SbomParseError("SBOM JSON root must be an object")
    fmt = detect_format(data)
    try:
        return parse_cyclonedx(data) if fmt == "cyclonedx" else parse_spdx(raw, data)
    except SbomParseError:
        raise
    except Exception as e:  # noqa: BLE001  library-specific validation errors
        raise SbomParseError(f"{fmt} parse failed: {type(e).__name__}: {e}") from e
