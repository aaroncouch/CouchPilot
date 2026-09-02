"""Compile and sync CouchPilot assets into user-scope host directories.

Renders the canonical asset sources under ``couchpilot/assets/`` (see
``couchpilot/FORMAT.md``) into installable artifacts for Cursor (``~/.cursor``)
and/or Claude Code (``~/.claude``), then writes them so they apply globally to
every workspace on this machine.

Each run records what it installed in a target-scoped manifest so the next run
can report files CouchPilot placed previously but no longer ships. Files the
manifest does not claim are never touched.

Pure standard library; no external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from couchpilot.compiler import CompilerError, RenderedArtifact, compile_assets
from couchpilot.hosts import HOST_PROFILES, get_host_profile, resolve_install_dir

REPO_ROOT = Path(__file__).resolve().parent
ASSETS_ROOT = REPO_ROOT / "couchpilot" / "assets"
TARGETS = tuple(HOST_PROFILES.keys())
HASH_CHUNK_BYTES = 65536
MANIFEST_NAME = ".couchpilot-manifest.json"
MANIFEST_VERSION = 1


class Action(Enum):
    """How a destination file was affected by a sync step."""

    COPY = "copy"
    OVERWRITE = "overwrite"
    SKIP_IDENTICAL = "skip-identical"
    ORPHAN = "orphan"
    PRUNE = "prune"


@dataclass(frozen=True)
class SyncOptions:
    """Behavior flags for a single sync run."""

    dry_run: bool = False
    prune: bool = False


@dataclass(frozen=True)
class SyncStep:
    """A single planned or executed file operation."""

    destination: Path
    action: Action


@dataclass
class SyncReport:
    """Collect sync steps for a single run and render a summary."""

    steps: list[SyncStep] = field(default_factory=list)

    def record(self, step: SyncStep) -> None:
        """Append a step to the report."""
        self.steps.append(step)

    def summary_lines(self) -> list[str]:
        """Render every step as a one-line ``[action] destination`` string."""
        return [f"[{step.action.value:>15}] {step.destination}" for step in self.steps]

    def counts(self) -> dict[Action, int]:
        """Return how many steps fell into each action bucket."""
        result: dict[Action, int] = {action: 0 for action in Action}
        for step in self.steps:
            result[step.action] += 1
        return result

    def has(self, action: Action) -> bool:
        """Return True when at least one step used ``action``."""
        return any(step.action is action for step in self.steps)


class Manifest:
    """Record of the files a previous sync installed under one target's home dir."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> set[str]:
        """Return relative paths recorded by the previous sync.

        Returns:
            Recorded paths, or an empty set when the manifest is absent or
            unreadable. An empty set is the safe default: nothing is claimed,
            so nothing can be pruned.
        """
        if not self._path.is_file():
            return set()
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        recorded = payload.get("files", [])
        if not isinstance(recorded, list):
            return set()
        return {entry for entry in recorded if isinstance(entry, str)}

    def write(self, relative_paths: Iterable[str]) -> None:
        """Overwrite the manifest so it lists exactly ``relative_paths``."""
        payload = {
            "version": MANIFEST_VERSION,
            "generated_by": "couchpilot sync.py",
            "files": sorted(relative_paths),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class TargetSync:
    """Write a target's rendered artifacts into ``<target_home>/``."""

    def __init__(
        self,
        target_home: Path,
        artifacts: list[RenderedArtifact],
        options: SyncOptions,
    ) -> None:
        self._target_home = target_home
        self._artifacts = artifacts
        self._options = options
        self._report = SyncReport()
        self._manifest = Manifest(target_home / MANIFEST_NAME)
        self._installed: set[str] = set()
        self._retained: set[str] = set()

    @property
    def report(self) -> SyncReport:
        """Return the accumulated report of actions for this sync."""
        return self._report

    def run(self) -> None:
        """Write every artifact, then reconcile against the previous manifest."""
        previously_installed = self._manifest.read()
        for artifact in self._artifacts:
            self._write_artifact(artifact)
        self._reconcile(previously_installed)
        if not self._options.dry_run:
            # Orphans left in place stay claimed, so a later --prune can still find them.
            self._manifest.write(self._installed | self._retained)

    def _write_artifact(self, artifact: RenderedArtifact) -> None:
        """Classify the write, perform it unless dry-run, and record it."""
        destination = self._target_home / artifact.relative_path
        action = _classify(artifact.content, destination)
        if not self._options.dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if action is not Action.SKIP_IDENTICAL:
                destination.write_text(artifact.content, encoding="utf-8")
        relative = artifact.relative_path.as_posix()
        self._installed.add(relative)
        self._report.record(SyncStep(destination=destination, action=action))

    def _reconcile(self, previously_installed: set[str]) -> None:
        """Report, and optionally remove, files this sync no longer ships."""
        for relative in sorted(previously_installed - self._installed):
            destination = self._target_home / relative
            if not destination.exists():
                continue
            if not self._options.prune:
                self._retained.add(relative)
                self._report.record(SyncStep(destination=destination, action=Action.ORPHAN))
                continue
            if not self._options.dry_run:
                destination.unlink()
                _remove_empty_parents(destination.parent, self._target_home)
            self._report.record(SyncStep(destination=destination, action=Action.PRUNE))


def _remove_empty_parents(directory: Path, stop_at: Path) -> None:
    """Delete ``directory`` and empty ancestors, never passing ``stop_at``."""
    current = directory
    while current != stop_at and stop_at in current.parents:
        if any(current.iterdir()):
            return
        current.rmdir()
        current = current.parent


def _content_digest(content: str) -> str:
    """Return the SHA-256 hex digest of ``content`` encoded as UTF-8."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _classify(content: str, destination: Path) -> Action:
    """Decide whether ``content`` is new, an overwrite, or already identical."""
    if not destination.exists():
        return Action.COPY
    if _content_digest(content) == _file_digest(destination):
        return Action.SKIP_IDENTICAL
    return Action.OVERWRITE


def _resolve_targets(requested: str | None, user_home: Path) -> list[str]:
    """Resolve which targets to sync from ``--target``, or autodetect."""
    if requested in HOST_PROFILES:
        return [requested]
    if requested == "all":
        return list(TARGETS)
    detected = [
        target
        for target in TARGETS
        if resolve_install_dir(get_host_profile(target), user_home).is_dir()
    ]
    if not detected:
        install_dirs = ", ".join(
            profile.default_install_dir for profile in HOST_PROFILES.values()
        )
        raise FileNotFoundError(
            f"No host install directories ({install_dirs}) exist under {user_home}; "
            f"pass --target {'|'.join((*TARGETS, 'all'))} to create one."
        )
    return detected


def _build_argument_parser() -> argparse.ArgumentParser:
    """Return the configured ``argparse.ArgumentParser`` for sync.py."""
    parser = argparse.ArgumentParser(
        description=(
            "Compile CouchPilot assets (couchpilot/assets/) and sync the rendered "
            "rules, skills, agents, and commands into the user-scope ~/.cursor "
            "and/or ~/.claude so they apply globally."
        ),
    )
    parser.add_argument(
        "--target",
        choices=(*TARGETS, "all"),
        default=None,
        help=(
            "Which host to sync. Defaults to autodetecting existing host install "
            "directories from the profile registry."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing, deleting, or updating the manifest.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete files a previous sync installed that CouchPilot no longer ships.",
    )
    return parser


def _print_report(target: str, report: SyncReport, options: SyncOptions) -> None:
    """Print a per-file summary followed by a one-line totals line for one target."""
    print(f"\n== {target} ==")
    for line in report.summary_lines():
        print(line)
    counts = report.counts()
    label = "DRY RUN" if options.dry_run else "Synced"
    print(
        f"{label}: "
        f"{counts[Action.COPY]} new, "
        f"{counts[Action.OVERWRITE]} overwritten, "
        f"{counts[Action.SKIP_IDENTICAL]} unchanged, "
        f"{counts[Action.PRUNE]} pruned, "
        f"{counts[Action.ORPHAN]} orphaned."
    )
    if report.has(Action.ORPHAN):
        print(
            f"Orphans above were installed by an earlier sync and are no longer "
            f"shipped under ~/.{target}. Re-run with --prune to delete them."
        )


def _print_session_cache_notice(targets: list[str]) -> None:
    """Print the post-sync reminder about host-side caching of rules/skills/agents."""
    divider = "-" * 70
    print()
    print(divider)
    print("Heads up: Cursor and Claude Code cache user-scope rules, skills,")
    print("subagents, and commands per session. The files above are on disk, but")
    print("any open chat (and possibly the running app) may still hold the")
    print("previous snapshot. To guarantee the new content is picked up:")
    print()
    print("  1. Restart the app(s) you synced (recommended), or at minimum open")
    print("     a fresh session/chat.")
    if "cursor" in targets:
        print("  2. In Cursor, dispatch a synced subagent (`/couch-planner`,")
        print("     `/couch-python-coder`, `/couch-reviewer`) and check its loaded-")
        print("     context announcement. Each rule and skill ends with an id token;")
        print("     the announcement must echo the ids it can actually see. A")
        print("     `MISSING` entry means that rule or skill did not reach it.")
    print()
    print("Note: path-scoped rules only attach when a matching file is in the")
    print("session's context (for example, `couch-python.mdc`/`couch-python.md`")
    print("need a *.py file open or attached).")
    print(divider)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, compile assets, and run one sync per resolved target."""
    args = _build_argument_parser().parse_args(argv)
    options = SyncOptions(dry_run=args.dry_run, prune=args.prune)
    user_home = Path.home()

    try:
        artifacts = compile_assets(ASSETS_ROOT)
    except CompilerError as error:
        print("sync.py: asset validation failed:", file=sys.stderr)
        for issue in error.errors:
            print(f"  - {issue}", file=sys.stderr)
        return 2

    try:
        targets = _resolve_targets(args.target, user_home)
    except FileNotFoundError as error:
        print(f"sync.py: {error}", file=sys.stderr)
        return 2

    for target in targets:
        target_home = resolve_install_dir(get_host_profile(target), user_home)
        target_artifacts = [artifact for artifact in artifacts if artifact.target == target]
        sync = TargetSync(target_home, target_artifacts, options)
        sync.run()
        _print_report(target, sync.report, options)

    if not options.dry_run:
        _print_session_cache_notice(targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
