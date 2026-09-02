"""Centralized host profile registry for Cursor and Claude Code targets."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

FAMILIES = ("rule", "command", "agent", "skill")

_WINDOWS_SYSTEM_USERS = frozenset({"Public", "Default", "Default User", "All Users"})

_FAMILY_DIRECTORIES = {
    "rule": "rules",
    "command": "commands",
    "agent": "agents",
    "skill": "skills",
}

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "couchpilot.json"

_WRAPPER_TEMPLATE = {
    "rule": "{{core}}\n",
    "command": "{{core}}\n",
    "agent": "{{core}}\n",
    "skill": "{{core}}\n",
}


@dataclass(frozen=True)
class HostProfile:
    """Configuration for one install target (Cursor or Claude Code)."""

    name: str
    default_install_dir: str
    extensions: dict[str, str]
    family_directories: dict[str, str]
    default_frontmatter: dict[str, dict[str, Any]]
    style_dialect: str
    wrapper_template: dict[str, str]

    def validate_family_frontmatter(self, family: str, frontmatter: dict[str, Any]) -> list[str]:
        """Return human-readable violations for ``family`` frontmatter on this host."""
        return []


@dataclass(frozen=True)
class CursorHostProfile(HostProfile):
    """Cursor-specific host profile with Cursor frontmatter validation."""

    def validate_family_frontmatter(self, family: str, frontmatter: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if family == "agent" and "model" not in frontmatter:
            errors.append("cursor agent wrappers require a model field")
        if family == "rule" and "alwaysApply" not in frontmatter:
            errors.append("cursor rule wrappers require an alwaysApply field")
        return errors


@dataclass(frozen=True)
class ClaudeHostProfile(HostProfile):
    """Claude Code-specific host profile with Claude frontmatter validation."""

    def validate_family_frontmatter(self, family: str, frontmatter: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if family == "skill" and frontmatter.get("disable-model-invocation") is not True:
            errors.append("claude skill wrappers require disable-model-invocation: true")
        return errors


def create_default_profiles() -> dict[str, HostProfile]:
    """Return built-in Cursor and Claude profile instances."""
    return {
        "cursor": CursorHostProfile(
            name="cursor",
            default_install_dir="~/.cursor",
            extensions={"rule": "mdc", "command": "md", "agent": "md", "skill": "md"},
            family_directories=dict(_FAMILY_DIRECTORIES),
            default_frontmatter={
                "rule": {"alwaysApply": True},
                "command": {},
                "agent": {"model": "inherit"},
                "skill": {},
            },
            style_dialect="universal_xml",
            wrapper_template=dict(_WRAPPER_TEMPLATE),
        ),
        "claude": ClaudeHostProfile(
            name="claude",
            default_install_dir="~/.claude",
            extensions={"rule": "md", "command": "md", "agent": "md", "skill": "md"},
            family_directories=dict(_FAMILY_DIRECTORIES),
            default_frontmatter={
                "rule": {},
                "command": {},
                "agent": {},
                "skill": {"disable-model-invocation": True},
            },
            style_dialect="anthropic_xml",
            wrapper_template=dict(_WRAPPER_TEMPLATE),
        ),
    }


def _merge_frontmatter(
    base: dict[str, dict[str, Any]],
    override: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged = {family: dict(fields) for family, fields in base.items()}
    for family, fields in override.items():
        if not isinstance(fields, dict):
            continue
        merged.setdefault(family, {})
        merged[family].update(fields)
    return merged


def _apply_host_override(profile: HostProfile, host_config: dict[str, Any]) -> HostProfile:
    updates: dict[str, Any] = {}
    if isinstance(host_config.get("install_dir"), str):
        updates["default_install_dir"] = host_config["install_dir"]
    if isinstance(host_config.get("style_dialect"), str):
        updates["style_dialect"] = host_config["style_dialect"]
    if isinstance(host_config.get("extensions"), dict):
        updates["extensions"] = {**profile.extensions, **host_config["extensions"]}
    if isinstance(host_config.get("family_directories"), dict):
        updates["family_directories"] = {**profile.family_directories, **host_config["family_directories"]}
    if isinstance(host_config.get("wrapper_template"), dict):
        updates["wrapper_template"] = {**profile.wrapper_template, **host_config["wrapper_template"]}
    if isinstance(host_config.get("default_frontmatter"), dict):
        updates["default_frontmatter"] = _merge_frontmatter(
            profile.default_frontmatter,
            host_config["default_frontmatter"],
        )
    if not updates:
        return profile
    return replace(profile, **updates)


def load_host_profiles(config_path: Path | None = None) -> dict[str, HostProfile]:
    """Load built-in profiles and merge optional JSON overrides from ``config_path``."""
    profiles = create_default_profiles()
    resolved_path = config_path if config_path is not None else _DEFAULT_CONFIG_PATH
    if not resolved_path.is_file():
        return profiles

    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return profiles

    hosts = payload.get("hosts")
    if not isinstance(hosts, dict):
        return profiles

    for host_name, host_config in hosts.items():
        if host_name not in profiles or not isinstance(host_config, dict):
            continue
        profiles[host_name] = _apply_host_override(profiles[host_name], host_config)
    return profiles


HOST_PROFILES: dict[str, HostProfile] = load_host_profiles()


def get_host_profile(target: str) -> HostProfile:
    """Return the profile for ``target``; raises ``KeyError`` when unknown."""
    try:
        return HOST_PROFILES[target]
    except KeyError as error:
        raise KeyError(f"unknown host profile: {target!r}") from error


def resolve_install_dir(profile: HostProfile, user_home: Path) -> Path:
    """Resolve ``profile.default_install_dir`` against a user home path."""
    install_dir = profile.default_install_dir
    if install_dir.startswith("~/"):
        return user_home / install_dir[2:]
    return Path(install_dir).expanduser()


def _running_in_wsl(
    proc_version: Path,
    environ: Mapping[str, str],
) -> bool:
    """True when this process appears to be inside a WSL distro."""
    if "WSL_DISTRO_NAME" in environ:
        return True
    if not proc_version.is_file():
        return False
    try:
        text = proc_version.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return "microsoft" in text or "wsl" in text


def find_wsl_windows_cursor_dir(
    proc_version: Path = Path("/proc/version"),
    users_root: Path = Path("/mnt/c/Users"),
    environ: Mapping[str, str] | None = None,
) -> Path | None:
    """Locate the Windows host ``.cursor`` dir when sync runs inside WSL2.

    Cursor on WSL2 is a split client-server setup:

    - Slash commands (``/command``) are registered by the Electron frontend on
      Windows, which reads ``%USERPROFILE%\\.cursor\\commands\\``.
    - Agents, skills, and rules are consumed by the agent engine inside WSL,
      which reads ``~/.cursor/`` on the Linux filesystem.

    When this process is not in WSL, or no Windows user ``.cursor`` directory
    is mounted under ``users_root``, returns ``None`` so callers stay inert on
    macOS and native Linux.

    Args:
        proc_version: Kernel identity file; defaults to ``/proc/version``.
        users_root: Windows users mount; defaults to ``/mnt/c/Users``.
        environ: Process environment used for ``WSL_DISTRO_NAME`` detection.
            Defaults to ``os.environ``.

    Returns:
        Path to the first non-system Windows user ``.cursor`` directory found,
        or ``None`` when not in WSL or no candidate exists.
    """
    env = os.environ if environ is None else environ
    if not _running_in_wsl(proc_version, env):
        return None
    if not users_root.is_dir():
        return None

    try:
        user_dirs = sorted(path for path in users_root.iterdir() if path.is_dir())
    except OSError:
        return None

    for user_dir in user_dirs:
        if user_dir.name in _WINDOWS_SYSTEM_USERS:
            continue
        cursor_dir = user_dir / ".cursor"
        if cursor_dir.is_dir():
            return cursor_dir
    return None
