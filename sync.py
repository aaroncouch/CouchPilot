"""Sync CouchPilot Cursor settings into the user-scope ``~/.cursor/`` directory.

Copies the curated ``.cursor/rules``, ``.cursor/skills``, ``.cursor/agents``,
and ``.cursor/commands``
folders from this repository into the user's home ``~/.cursor/...`` directories
so they apply globally to every Cursor workspace on this machine.

Pure standard library; no external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CURSOR_SUBDIRS = ("rules", "skills", "agents", "commands")
HASH_CHUNK_BYTES = 65536


class Action(Enum):
    """How a destination file was affected by a sync step."""

    COPY = "copy"
    OVERWRITE = "overwrite"
    SKIP_IDENTICAL = "skip-identical"


@dataclass(frozen=True)
class SyncStep:
    """A single planned or executed file copy."""

    source: Path
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


class CursorSync:
    """Copy curated Cursor settings from this repo into ``<user_home>/.cursor/``."""

    def __init__(self, repo_root: Path, user_home: Path, *, dry_run: bool = False) -> None:
        if not (repo_root / ".cursor").is_dir():
            raise FileNotFoundError(
                f"Repo root {repo_root} does not contain a .cursor directory; "
                "make sure sync.py is run from the project root."
            )
        self._repo_root = repo_root
        self._user_home = user_home
        self._dry_run = dry_run
        self._report = SyncReport()

    @property
    def report(self) -> SyncReport:
        """Return the accumulated report of actions for this sync."""
        return self._report

    def run(self) -> None:
        """Copy ``.cursor/{rules,skills,agents,commands}`` into ``<user_home>/.cursor/``."""
        for subdir in CURSOR_SUBDIRS:
            source_dir = self._repo_root / ".cursor" / subdir
            destination_dir = self._user_home / ".cursor" / subdir
            self._copy_tree(source_dir, destination_dir)

    def _copy_tree(self, source_dir: Path, destination_dir: Path) -> None:
        """Recursively copy every file under ``source_dir`` into ``destination_dir``."""
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Missing source directory: {source_dir}")
        for source_file in sorted(source_dir.rglob("*")):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_dir)
            destination = destination_dir / relative
            self._copy_file(source_file, destination)

    def _copy_file(self, source: Path, destination: Path) -> None:
        """Classify the operation, perform it (unless dry-run), and record it."""
        action = self._classify(source, destination)
        if not self._dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if action is not Action.SKIP_IDENTICAL:
                shutil.copy2(source, destination)
        self._report.record(SyncStep(source=source, destination=destination, action=action))

    @staticmethod
    def _classify(source: Path, destination: Path) -> Action:
        """Decide whether ``source`` is new, an overwrite, or already identical."""
        if not destination.exists():
            return Action.COPY
        if _file_digest(source) == _file_digest(destination):
            return Action.SKIP_IDENTICAL
        return Action.OVERWRITE


def _file_digest(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _build_argument_parser() -> argparse.ArgumentParser:
    """Return the configured ``argparse.ArgumentParser`` for sync.py."""
    return argparse.ArgumentParser(
        description=(
            "Sync CouchPilot Cursor settings (rules, skills, agents) "
            "including commands into the user-scope ~/.cursor/ so they apply globally."
        ),
    )


def _add_dry_run_flag(parser: argparse.ArgumentParser) -> None:
    """Attach the ``--dry-run`` flag to ``parser``."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing any files.",
    )


def _print_report(report: SyncReport, dry_run: bool) -> None:
    """Print a per-file summary followed by a one-line totals line."""
    for line in report.summary_lines():
        print(line)
    counts = report.counts()
    label = "DRY RUN" if dry_run else "Synced"
    print(
        f"\n{label}: "
        f"{counts[Action.COPY]} new, "
        f"{counts[Action.OVERWRITE]} overwritten, "
        f"{counts[Action.SKIP_IDENTICAL]} unchanged."
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
    print("  2. Ask any synced subagent (`/planner-inherit`, `/planner-codex`,")
    print("     `/planner-gpt55`, `/python-coder-inherit`, `/python-coder-codex`,")
    print("     `/reviewer-inherit`, `/reviewer-codex`, `/reviewer-gpt55`)")
    print("     what rules and skills it sees on entry - each one is")
    print("     instructed to declare its loaded context before doing work.")
    print()
    print("  3. If a command was removed from CouchPilot, delete the matching file")
    print("     under `~/.cursor/commands/` if it is still present (sync does not")
    print("     remove orphans). For example, `dispatch-subagent.md` was retired.")
    print()
    print("Note: glob-scoped rules only attach when a matching file is in")
    print("the chat's context. `python.mdc` won't show up unless a `*.py`")
    print("file is open or attached.")
    print(divider)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run a single ``CursorSync`` session."""
    parser = _build_argument_parser()
    _add_dry_run_flag(parser)
    args = parser.parse_args(argv)
    try:
        sync = CursorSync(
            repo_root=REPO_ROOT,
            user_home=Path.home(),
            dry_run=args.dry_run,
        )
        sync.run()
    except FileNotFoundError as error:
        print(f"sync.py: {error}", file=sys.stderr)
        return 2
    _print_report(sync.report, args.dry_run)
    if not args.dry_run:
        _print_session_cache_notice()
    return 0


if __name__ == "__main__":
    sys.exit(main())
