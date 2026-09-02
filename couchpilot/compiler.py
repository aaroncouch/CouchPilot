"""Compile canonical CouchPilot assets into per-target installable artifacts.

Reads the folder-derived asset sources under ``couchpilot/assets/`` (see
``couchpilot/FORMAT.md``) and renders them into the files Cursor and Claude
Code expect under their respective home directories. Pure standard library;
no external dependencies, and no filesystem writes outside ``assets_root``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from couchpilot.hosts import FAMILIES, HOST_PROFILES, HostProfile, get_host_profile

TARGETS = tuple(HOST_PROFILES.keys())
FAMILY_FILENAMES = {
    "rule.md": "rule",
    "command.md": "command",
    "agent.md": "agent",
    "skill.md": "skill",
}
CORE_MARKER = "{{core}}"
NAME_PREFIX = "couch-"
_NAMED_FAMILIES = frozenset({"skill", "agent"})

FrontmatterValue = str | bool | list[str]

_KEY_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")
_LEADING_INDICATOR_CHARS = "-?:,[]{}#&*!|>'\"%@`"
_RESERVED_SCALARS = {"true", "false", "null", "~"}


@dataclass(frozen=True)
class ParsedDocument:
    """A single parsed markdown-with-frontmatter source file."""

    frontmatter: dict[str, FrontmatterValue]
    body: str


@dataclass(frozen=True)
class Wrapper:
    """A target-specific wrapper file for one asset."""

    target: str
    family: str
    path: Path
    doc: ParsedDocument


@dataclass(frozen=True)
class Asset:
    """One canonical asset directory: an optional shared core plus wrappers."""

    asset_id: str
    directory: Path
    core: ParsedDocument | None
    core_path: Path | None
    wrappers: list[Wrapper] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedArtifact:
    """A compiled file ready to be written under a target's home directory."""

    asset_id: str
    target: str
    family: str
    relative_path: Path
    content: str


class CompilerError(Exception):
    """Raised when one or more assets fail schema validation."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def parse_document(text: str) -> ParsedDocument:
    """Split ``text`` into frontmatter fields and body.

    Tolerates leading blank lines before the opening ``---``. A document with
    no frontmatter block returns an empty frontmatter dict and the full text
    as the body.
    """
    lines = text.splitlines()
    index = 0
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    if index >= len(lines) or lines[index].strip() != "---":
        return ParsedDocument(frontmatter={}, body=text)

    closing = None
    for candidate in range(index + 1, len(lines)):
        if lines[candidate].strip() == "---":
            closing = candidate
            break
    if closing is None:
        raise ValueError("Unterminated frontmatter block: missing closing '---'")

    frontmatter = _parse_frontmatter_lines(lines[index + 1 : closing])
    body = "\n".join(lines[closing + 1 :])
    return ParsedDocument(frontmatter=frontmatter, body=body)


def _parse_frontmatter_lines(lines: list[str]) -> dict[str, FrontmatterValue]:
    fields: dict[str, FrontmatterValue] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        match = _KEY_LINE.match(line)
        if not match:
            raise ValueError(f"Malformed frontmatter line: {line!r}")
        key, raw_value = match.group(1), match.group(2).strip()
        if raw_value:
            fields[key] = _coerce_scalar(raw_value)
            index += 1
            continue
        items: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip().startswith("-"):
            items.append(_unquote_scalar(lines[index].strip()[1:].strip()))
            index += 1
        fields[key] = items
    return fields


def _coerce_scalar(raw: str) -> FrontmatterValue:
    if raw == "true":
        return True
    if raw == "false":
        return False
    return _unquote_scalar(raw)


def _unquote_scalar(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        inner = raw[1:-1]
        return inner.replace('\\"', '"') if raw[0] == '"' else inner
    return raw


def discover_assets(assets_root: Path) -> list[Asset]:
    """Discover every canonical asset directory under ``assets_root``."""
    assets = []
    for asset_dir in sorted(p for p in assets_root.iterdir() if p.is_dir()):
        core_path = asset_dir / "core.md"
        has_core = core_path.is_file()
        core = parse_document(core_path.read_text(encoding="utf-8")) if has_core else None
        wrappers = []
        for target in TARGETS:
            target_dir = asset_dir / target
            if not target_dir.is_dir():
                continue
            for file_path in sorted(target_dir.iterdir()):
                if not file_path.is_file() or file_path.name not in FAMILY_FILENAMES:
                    continue
                family = FAMILY_FILENAMES[file_path.name]
                doc = parse_document(file_path.read_text(encoding="utf-8"))
                wrappers.append(Wrapper(target=target, family=family, path=file_path, doc=doc))
        if not wrappers and core is not None:
            wrappers = _synthesize_wrappers(asset_dir, core)
        assets.append(
            Asset(
                asset_id=asset_dir.name,
                directory=asset_dir,
                core=core,
                core_path=core_path if has_core else None,
                wrappers=wrappers,
            )
        )
    return assets


def _synthesize_wrappers(asset_dir: Path, core: ParsedDocument) -> list[Wrapper]:
    """Build per-target wrappers from host templates when only ``core.md`` exists."""
    family = core.frontmatter.get("family")
    if not isinstance(family, str) or family not in FAMILIES:
        return []

    wrappers: list[Wrapper] = []
    for target_name, profile in HOST_PROFILES.items():
        template = profile.wrapper_template.get(family)
        if template is None:
            continue
        content = _build_synthetic_wrapper_content(profile, family, template, core)
        doc = parse_document(content)
        wrappers.append(
            Wrapper(
                target=target_name,
                family=family,
                path=asset_dir / target_name / f"{family}.md",
                doc=doc,
            )
        )
    return wrappers


def _globs_from_core(core_frontmatter: dict[str, FrontmatterValue]) -> list[str] | None:
    """Normalize ``globs`` from core frontmatter into a list of glob strings."""
    globs = core_frontmatter.get("globs")
    if globs is None:
        return None
    if isinstance(globs, list):
        return [str(item) for item in globs]
    if isinstance(globs, str):
        if "," in globs:
            return [part.strip() for part in globs.split(",") if part.strip()]
        return [globs]
    return None


def _synthetic_rule_frontmatter(
    target: str,
    core_frontmatter: dict[str, FrontmatterValue],
) -> dict[str, FrontmatterValue]:
    """Build host-native rule frontmatter from canonical ``core.md`` scope fields."""
    globs_list = _globs_from_core(core_frontmatter)
    if target == "cursor":
        if globs_list is None:
            return {"alwaysApply": True}
        return {"alwaysApply": False, "globs": ",".join(globs_list)}
    if globs_list is None:
        return {}
    return {"paths": globs_list}


def _build_synthetic_wrapper_content(
    profile: HostProfile,
    family: str,
    template: str,
    core: ParsedDocument,
) -> str:
    """Render default frontmatter plus a host template body for one family."""
    defaults = dict(profile.default_frontmatter.get(family, {}))
    if family == "rule":
        defaults.update(_synthetic_rule_frontmatter(profile.name, core.frontmatter))
    if not defaults:
        return template
    return render_document(defaults, template)


def validate_asset(asset: Asset) -> list[str]:
    """Return every schema violation found in ``asset``; empty when valid."""
    errors: list[str] = []
    errors.extend(_validate_stray_entries(asset))
    errors.extend(_validate_target_uniqueness(asset))
    errors.extend(_validate_core_markers(asset))
    errors.extend(_validate_description_ownership(asset))
    errors.extend(_validate_required_metadata(asset))
    errors.extend(_validate_synthesis_requirements(asset))
    if not asset.wrappers:
        errors.append(f"{asset.directory}: asset defines no target wrappers")
    return errors


def _validate_stray_entries(asset: Asset) -> list[str]:
    errors = []
    for entry in sorted(asset.directory.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file() and entry.name == "core.md":
            continue
        if entry.is_dir() and entry.name in TARGETS:
            for file_path in sorted(entry.iterdir()):
                if file_path.name.startswith("."):
                    continue
                if file_path.name not in FAMILY_FILENAMES:
                    errors.append(f"{file_path}: unrecognized wrapper filename")
            continue
        errors.append(f"{entry}: unexpected entry in asset directory")
    return errors


def _validate_target_uniqueness(asset: Asset) -> list[str]:
    errors = []
    seen: set[str] = set()
    for wrapper in asset.wrappers:
        if wrapper.target in seen:
            errors.append(f"{asset.directory}: multiple wrapper families found for target '{wrapper.target}'")
        seen.add(wrapper.target)
    return errors


def _validate_core_markers(asset: Asset) -> list[str]:
    errors = []
    for wrapper in asset.wrappers:
        marker_count = wrapper.doc.body.count(CORE_MARKER)
        if asset.core is not None and marker_count != 1:
            errors.append(
                f"{wrapper.path}: expected exactly one {CORE_MARKER} marker, found {marker_count}"
            )
        elif asset.core is None and marker_count != 0:
            errors.append(f"{wrapper.path}: unexpected {CORE_MARKER} marker; asset has no core.md")
    return errors


def _validate_description_ownership(asset: Asset) -> list[str]:
    errors = []
    if asset.core is not None:
        if "description" not in asset.core.frontmatter:
            errors.append(f"{asset.core_path}: core.md must define description")
        for wrapper in asset.wrappers:
            if "description" in wrapper.doc.frontmatter:
                errors.append(f"{wrapper.path}: description must be defined in core.md, not the wrapper")
    else:
        for wrapper in asset.wrappers:
            if "description" not in wrapper.doc.frontmatter:
                errors.append(f"{wrapper.path}: description is required when core.md is absent")
    return errors


def _validate_required_metadata(asset: Asset) -> list[str]:
    errors = []
    for wrapper in asset.wrappers:
        profile = get_host_profile(wrapper.target)
        for message in profile.validate_family_frontmatter(wrapper.family, wrapper.doc.frontmatter):
            errors.append(f"{wrapper.path}: {message}")
    return errors


def _validate_synthesis_requirements(asset: Asset) -> list[str]:
    errors = []
    if asset.wrappers or asset.core is None:
        return errors
    family = asset.core.frontmatter.get("family")
    if not isinstance(family, str) or family not in FAMILIES:
        errors.append(
            f"{asset.directory}: core.md requires a family field "
            f"({', '.join(FAMILIES)}) when no wrapper directories exist"
        )
    return errors


def merge_frontmatter(
    core: ParsedDocument | None,
    wrapper: ParsedDocument,
    *,
    asset_id: str = "",
    family: str = "",
) -> dict[str, FrontmatterValue]:
    """Merge core and wrapper frontmatter; core owns ``description`` when present.

    For ``skill`` and ``agent`` families, injects ``name: couch-<asset_id>`` as the
    first frontmatter key so Cursor/Claude can discover the compiled artifact.
    Rules and commands keep filename-derived identity and do not get a ``name`` key.
    """
    merged: dict[str, FrontmatterValue] = {}
    if family in _NAMED_FAMILIES and asset_id:
        merged["name"] = f"{NAME_PREFIX}{asset_id}"
    if core is not None and "description" in core.frontmatter:
        merged["description"] = core.frontmatter["description"]
    for key, value in wrapper.frontmatter.items():
        merged[key] = value
    return merged


def substitute_core(core: ParsedDocument | None, wrapper: ParsedDocument) -> str:
    """Replace the ``{{core}}`` marker in the wrapper body with the core body."""
    if core is None:
        return wrapper.body
    return wrapper.body.replace(CORE_MARKER, core.body.strip("\n"))


def render_document(fields: dict[str, FrontmatterValue], body: str) -> str:
    """Render merged frontmatter and body back into a single markdown file."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {_render_scalar(item)}" for item in value)
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {_render_scalar(value)}")
    lines.append("---")
    frontmatter_block = "\n".join(lines)
    return f"{frontmatter_block}\n\n{body.strip(chr(10))}\n"


def _render_scalar(value: str) -> str:
    if _needs_quote(value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _needs_quote(value: str) -> bool:
    """Decide whether ``value`` needs quoting to stay a valid YAML plain scalar.

    Only the ambiguous cases: a leading indicator character (e.g. a glob's
    leading ``*``), a reserved word, or a colon/hash that would be read as a
    mapping or comment. Punctuation such as an apostrophe elsewhere in the
    string is valid unquoted and should not be escaped.
    """
    if value == "" or value != value.strip():
        return True
    if value in _RESERVED_SCALARS:
        return True
    if value[0] in _LEADING_INDICATOR_CHARS:
        return True
    if ": " in value or value.endswith(":") or " #" in value:
        return True
    return False


def destination_for(target: str, family: str, asset_id: str) -> Path:
    """Return the destination path for one artifact, relative to the target home dir."""
    profile = get_host_profile(target)
    if family not in profile.family_directories:
        raise KeyError(f"no destination mapping for target={target!r} family={family!r}")
    name = f"{NAME_PREFIX}{asset_id}"
    target_dir = profile.family_directories[family]
    if family == "skill":
        return Path(target_dir) / name / "SKILL.md"
    extension = profile.extensions[family]
    return Path(target_dir) / f"{name}.{extension}"


def compile_assets(assets_root: Path) -> list[RenderedArtifact]:
    """Discover, validate, and render every asset under ``assets_root``.

    Raises:
        CompilerError: when any asset fails schema validation. Carries every
            violation found across every asset, not just the first.
    """
    assets = discover_assets(assets_root)
    errors: list[str] = []
    for asset in assets:
        errors.extend(validate_asset(asset))
    if errors:
        raise CompilerError(errors)

    artifacts = []
    for asset in assets:
        for wrapper in asset.wrappers:
            fields = merge_frontmatter(
                asset.core,
                wrapper.doc,
                asset_id=asset.asset_id,
                family=wrapper.family,
            )
            body = substitute_core(asset.core, wrapper.doc)
            content = render_document(fields, body)
            relative_path = destination_for(wrapper.target, wrapper.family, asset.asset_id)
            artifacts.append(
                RenderedArtifact(
                    asset_id=asset.asset_id,
                    target=wrapper.target,
                    family=wrapper.family,
                    relative_path=relative_path,
                    content=content,
                )
            )
    return artifacts
