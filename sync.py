"""Sync CouchPilot Cursor settings into the user-scope ``~/.cursor/`` directory.

Copies the curated ``.cursor/rules``, ``.cursor/skills``, ``.cursor/agents``,
and ``.cursor/commands``
folders from this repository into the user's home ``~/.cursor/...`` directories
so they apply globally to every Cursor workspace on this machine.

Each run records what it installed in a manifest so the next run can report
files CouchPilot placed previously but no longer ships. Files the manifest does
not claim are never touched.

Pure standard library; no external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CURSOR_SUBDIRS = ("rules", "skills", "agents", "commands")
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
    source: Path | None = None


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
    """Record of the files a previous sync installed under ``<user_home>/.cursor``."""

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


class CursorSync:
    """Copy curated Cursor settings from this repo into ``<user_home>/.cursor/``."""

    def __init__(self, repo_root: Path, user_home: Path, options: SyncOptions) -> None:
        if not (repo_root / ".cursor").is_dir():
            raise FileNotFoundError(
                f"Repo root {repo_root} does not contain a .cursor directory; "
                "make sure sync.py is run from the project root."
            )
        self._repo_root = repo_root
        self._cursor_home = user_home / ".cursor"
        self._options = options
        self._report = SyncReport()
        self._manifest = Manifest(self._cursor_home / MANIFEST_NAME)
        self._installed: set[str] = set()
        self._retained: set[str] = set()

    @property
    def report(self) -> SyncReport:
        """Return the accumulated report of actions for this sync."""
        return self._report

    def run(self) -> None:
        """Copy the managed subdirectories, then reconcile against the manifest."""
        previously_installed = self._manifest.read()
        for subdir in CURSOR_SUBDIRS:
            self._copy_tree(self._repo_root / ".cursor" / subdir, self._cursor_home / subdir)
        self._reconcile(previously_installed)
        if not self._options.dry_run:
            # Orphans left in place stay claimed, so a later --prune can still find them.
            self._manifest.write(self._installed | self._retained)

    def _copy_tree(self, source_dir: Path, destination_dir: Path) -> None:
        """Recursively copy every file under ``source_dir`` into ``destination_dir``."""
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Missing source directory: {source_dir}")
        for source_file in sorted(source_dir.rglob("*")):
            if not source_file.is_file():
                continue
            destination = destination_dir / source_file.relative_to(source_dir)
            self._copy_file(source_file, destination)

    def _copy_file(self, source: Path, destination: Path) -> None:
        """Classify the operation, perform it unless dry-run, and record it."""
        action = _classify(source, destination)
        if not self._options.dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if action is not Action.SKIP_IDENTICAL:
                shutil.copy2(source, destination)
        self._installed.add(destination.relative_to(self._cursor_home).as_posix())
        self._report.record(SyncStep(destination=destination, action=action, source=source))

    def _reconcile(self, previously_installed: set[str]) -> None:
        """Report, and optionally remove, files this sync no longer ships."""
        for relative in sorted(previously_installed - self._installed):
            destination = self._cursor_home / relative
            if not destination.exists():
                continue
            if not self._options.prune:
                self._retained.add(relative)
                self._report.record(SyncStep(destination=destination, action=Action.ORPHAN))
                continue
            if not self._options.dry_run:
                destination.unlink()
                _remove_empty_parents(destination.parent, self._cursor_home)
            self._report.record(SyncStep(destination=destination, action=Action.PRUNE))


def _remove_empty_parents(directory: Path, stop_at: Path) -> None:
    """Delete ``directory`` and empty ancestors, never passing ``stop_at``."""
    current = directory
    while current != stop_at and stop_at in current.parents:
        if any(current.iterdir()):
            return
        current.rmdir()
        current = current.parent


def _file_digest(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _classify(source: Path, destination: Path) -> Action:
    """Decide whether ``source`` is new, an overwrite, or already identical."""
    if not destination.exists():
        return Action.COPY
    if _file_digest(source) == _file_digest(destination):
        return Action.SKIP_IDENTICAL
    return Action.OVERWRITE


def _build_argument_parser() -> argparse.ArgumentParser:
    """Return the configured ``argparse.ArgumentParser`` for sync.py."""
    parser = argparse.ArgumentParser(
        description=(
            "Sync CouchPilot Cursor settings (rules, skills, agents, commands) "
            "into the user-scope ~/.cursor/ so they apply globally."
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


def _print_report(report: SyncReport, options: SyncOptions) -> None:
    """Print a per-file summary followed by a one-line totals line."""
    for line in report.summary_lines():
        print(line)
    counts = report.counts()
    label = "DRY RUN" if options.dry_run else "Synced"
    print(
        f"\n{label}: "
        f"{counts[Action.COPY]} new, "
        f"{counts[Action.OVERWRITE]} overwritten, "
        f"{counts[Action.SKIP_IDENTICAL]} unchanged, "
        f"{counts[Action.PRUNE]} pruned, "
        f"{counts[Action.ORPHAN]} orphaned."
    )
    if report.has(Action.ORPHAN):
        print(
            "\nOrphans above were installed by an earlier sync and are no longer "
            "shipped.\nRe-run with --prune to delete them."
        )


def _print_session_cache_notice() -> None:
    """Print the post-sync reminder about Cursor's session-scoped rule cache."""
    divider = "-" * 70
    print()
    print(divider)
    print("Heads up: Cursor caches user-scope rules, skills, subagents, and commands")
    print("per chat session. The files above are on disk, but any open chat")
    print("(and possibly the running IDE) may still hold the previous")
    print("snapshot. To guarantee the new content is picked up:")
    print()
    print("  1. Restart Cursor (recommended), or at minimum open a fresh")
    print("     chat in a new window.")
    print("  2. Dispatch any synced subagent (`/planner`, `/python-coder`,")
    print("     `/reviewer`) and check its loaded-context announcement. Each")
    print("     rule and skill ends with an id token; the announcement must")
    print("     echo the ids it can actually see. A `MISSING` entry means")
    print("     that rule or skill did not reach the subagent.")
    print()
    print("Note: glob-scoped rules only attach when a matching file is in")
    print("the chat's context. `python.mdc` won't show up unless a `*.py`")
    print("file is open or attached.")
    print(divider)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run a single ``CursorSync`` session."""
    args = _build_argument_parser().parse_args(argv)
    options = SyncOptions(dry_run=args.dry_run, prune=args.prune)
    try:
        sync = CursorSync(repo_root=REPO_ROOT, user_home=Path.home(), options=options)
        sync.run()
    except FileNotFoundError as error:
        print(f"sync.py: {error}", file=sys.stderr)
        return 2
    _print_report(sync.report, options)
    if not options.dry_run:
        _print_session_cache_notice()
    return 0


if __name__ == "__main__":
    sys.exit(main())
