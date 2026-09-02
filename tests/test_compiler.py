"""Tests for couchpilot.compiler: discovery, validation, rendering, path mapping."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from couchpilot.hosts import (
    ClaudeHostProfile,
    CursorHostProfile,
    HOST_PROFILES,
    create_default_profiles,
    find_wsl_windows_cursor_dir,
    get_host_profile,
    load_host_profiles,
    resolve_install_dir,
)
from couchpilot.compiler import (
    CompilerError,
    compile_assets,
    destination_for,
    discover_assets,
    merge_frontmatter,
    parse_document,
    render_document,
    substitute_core,
    validate_asset,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TempAssetsRoot:
    """Builds a synthetic ``couchpilot/assets``-shaped tree for one test."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()

    def add_shared_asset(
        self,
        asset_id: str,
        *,
        core_description: str = "Shared description.",
        cursor_extra: str = "alwaysApply: true\n",
        claude_extra: str = "",
    ) -> None:
        asset_dir = self.root / asset_id
        _write(
            asset_dir / "core.md",
            f"---\ndescription: {core_description}\n---\n\n# Core\n\nShared body.\n",
        )
        _write(
            asset_dir / "cursor" / "rule.md",
            f"---\n{cursor_extra}---\n\n# Cursor wrapper\n\n{{{{core}}}}\n",
        )
        _write(
            asset_dir / "claude" / "rule.md",
            f"---\n{claude_extra}---\n\n{{{{core}}}}\n" if claude_extra else "{{core}}\n",
        )

    def add_single_platform_asset(self, asset_id: str) -> None:
        _write(
            self.root / asset_id / "cursor" / "agent.md",
            "---\ndescription: Solo agent.\nmodel: inherit\n---\n\n# Solo agent\n\nBody.\n",
        )


class ParseDocumentTests(unittest.TestCase):
    def test_parses_scalar_and_boolean_fields(self) -> None:
        doc = parse_document("---\ndescription: Do the thing.\nalwaysApply: false\n---\n\nBody text.\n")
        self.assertEqual(doc.frontmatter["description"], "Do the thing.")
        self.assertIs(doc.frontmatter["alwaysApply"], False)
        self.assertEqual(doc.body.strip(), "Body text.")

    def test_parses_list_field(self) -> None:
        doc = parse_document('---\npaths:\n  - "**/*.py"\n  - "**/*.pyi"\n---\n\nBody.\n')
        self.assertEqual(doc.frontmatter["paths"], ["**/*.py", "**/*.pyi"])

    def test_tolerates_leading_blank_lines_before_frontmatter(self) -> None:
        doc = parse_document("\n\n---\ndescription: x\n---\n\nBody.\n")
        self.assertEqual(doc.frontmatter["description"], "x")

    def test_no_frontmatter_returns_full_text_as_body(self) -> None:
        doc = parse_document("# Just a wrapper\n\n{{core}}\n")
        self.assertEqual(doc.frontmatter, {})
        self.assertIn("{{core}}", doc.body)

    def test_unterminated_frontmatter_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_document("---\ndescription: x\n\nBody without closing marker.\n")


class DiscoverAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = TempAssetsRoot()
        self.addCleanup(self.assets.close)

    def test_discovers_wrappers_for_each_target(self) -> None:
        self.assets.add_shared_asset("widget")
        discovered = discover_assets(self.assets.root)
        self.assertEqual(len(discovered), 1)
        asset = discovered[0]
        self.assertEqual(asset.asset_id, "widget")
        self.assertIsNotNone(asset.core)
        targets = sorted(w.target for w in asset.wrappers)
        self.assertEqual(targets, ["claude", "cursor"])

    def test_discovers_single_platform_asset_without_core(self) -> None:
        self.assets.add_single_platform_asset("solo")
        discovered = discover_assets(self.assets.root)
        asset = discovered[0]
        self.assertIsNone(asset.core)
        self.assertEqual(len(asset.wrappers), 1)
        self.assertEqual(asset.wrappers[0].family, "agent")


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = TempAssetsRoot()
        self.addCleanup(self.assets.close)

    def _errors_for(self, asset_id: str) -> list[str]:
        asset = next(a for a in discover_assets(self.assets.root) if a.asset_id == asset_id)
        return validate_asset(asset)

    def test_valid_shared_asset_has_no_errors(self) -> None:
        self.assets.add_shared_asset("widget")
        self.assertEqual(self._errors_for("widget"), [])

    def test_valid_single_platform_asset_has_no_errors(self) -> None:
        self.assets.add_single_platform_asset("solo")
        self.assertEqual(self._errors_for("solo"), [])

    def test_missing_core_marker_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(
            self.assets.root / "widget" / "cursor" / "rule.md",
            "---\nalwaysApply: true\n---\n\n# No marker here\n",
        )
        errors = self._errors_for("widget")
        self.assertTrue(any("{{core}}" in e and "found 0" in e for e in errors))

    def test_extra_core_marker_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(
            self.assets.root / "widget" / "cursor" / "rule.md",
            "---\nalwaysApply: true\n---\n\n{{core}}\n\n{{core}}\n",
        )
        errors = self._errors_for("widget")
        self.assertTrue(any("found 2" in e for e in errors))

    def test_core_marker_without_core_md_is_an_error(self) -> None:
        self.assets.add_single_platform_asset("solo")
        _write(
            self.assets.root / "solo" / "cursor" / "agent.md",
            "---\ndescription: Solo agent.\nmodel: inherit\n---\n\n{{core}}\n",
        )
        errors = self._errors_for("solo")
        self.assertTrue(any("unexpected" in e and "{{core}}" in e for e in errors))

    def test_wrapper_description_when_core_exists_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget", cursor_extra="description: duplicate\nalwaysApply: true\n")
        errors = self._errors_for("widget")
        self.assertTrue(any("description must be defined in core.md" in e for e in errors))

    def test_missing_description_without_core_is_an_error(self) -> None:
        _write(
            self.assets.root / "solo" / "cursor" / "agent.md",
            "---\nmodel: inherit\n---\n\n# Solo\n\nBody.\n",
        )
        errors = self._errors_for("solo")
        self.assertTrue(any("description is required" in e for e in errors))

    def test_cursor_agent_without_model_is_an_error(self) -> None:
        _write(
            self.assets.root / "solo" / "cursor" / "agent.md",
            "---\ndescription: Solo agent.\n---\n\n# Solo\n\nBody.\n",
        )
        errors = self._errors_for("solo")
        self.assertTrue(any("require a model field" in e for e in errors))

    def test_cursor_rule_without_alwaysapply_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget", cursor_extra="")
        errors = self._errors_for("widget")
        self.assertTrue(any("require an alwaysApply field" in e for e in errors))

    def test_claude_skill_without_disable_model_invocation_is_an_error(self) -> None:
        _write(
            self.assets.root / "widget" / "core.md",
            "---\ndescription: Shared.\n---\n\nBody.\n",
        )
        _write(
            self.assets.root / "widget" / "claude" / "skill.md",
            "---\n---\n\n{{core}}\n",
        )
        errors = self._errors_for("widget")
        self.assertTrue(any("disable-model-invocation: true" in e for e in errors))

    def test_duplicate_target_wrappers_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(
            self.assets.root / "widget" / "cursor" / "command.md",
            "# Extra cursor wrapper\n\n{{core}}\n",
        )
        errors = self._errors_for("widget")
        self.assertTrue(any("multiple wrapper families" in e for e in errors))

    def test_unrecognized_wrapper_filename_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(self.assets.root / "widget" / "cursor" / "typo.md", "stray file\n")
        errors = self._errors_for("widget")
        self.assertTrue(any("unrecognized wrapper filename" in e for e in errors))

    def test_unexpected_top_level_entry_is_an_error(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(self.assets.root / "widget" / "notes.txt", "stray\n")
        errors = self._errors_for("widget")
        self.assertTrue(any("unexpected entry" in e for e in errors))

    def test_asset_with_no_wrappers_is_an_error(self) -> None:
        _write(self.assets.root / "empty" / "core.md", "---\ndescription: x\n---\n\nBody.\n")
        errors = self._errors_for("empty")
        self.assertTrue(any("defines no target wrappers" in e for e in errors))


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = TempAssetsRoot()
        self.addCleanup(self.assets.close)

    def test_merge_frontmatter_core_description_wins_and_wrapper_fields_follow(self) -> None:
        self.assets.add_shared_asset("widget", core_description="Core description.")
        asset = discover_assets(self.assets.root)[0]
        cursor_wrapper = next(w for w in asset.wrappers if w.target == "cursor")
        merged = merge_frontmatter(asset.core, cursor_wrapper.doc)
        self.assertEqual(list(merged.items()), [("description", "Core description."), ("alwaysApply", True)])

    def test_merge_frontmatter_without_core_uses_wrapper_as_is(self) -> None:
        self.assets.add_single_platform_asset("solo")
        asset = discover_assets(self.assets.root)[0]
        merged = merge_frontmatter(asset.core, asset.wrappers[0].doc)
        self.assertEqual(merged["description"], "Solo agent.")
        self.assertEqual(merged["model"], "inherit")

    def test_merge_frontmatter_injects_name_for_skill_and_agent(self) -> None:
        self.assets.add_single_platform_asset("solo")
        asset = discover_assets(self.assets.root)[0]
        merged = merge_frontmatter(
            asset.core,
            asset.wrappers[0].doc,
            asset_id=asset.asset_id,
            family="agent",
        )
        self.assertEqual(list(merged.items())[0], ("name", "couch-solo"))
        self.assertEqual(merged["description"], "Solo agent.")

        skill_doc = parse_document(
            "---\ndisable-model-invocation: true\n---\n\n{{core}}\n"
        )
        core = parse_document("---\ndescription: A skill.\n---\n\nBody.\n")
        skill_merged = merge_frontmatter(
            core, skill_doc, asset_id="helper", family="skill"
        )
        self.assertEqual(list(skill_merged.items())[0], ("name", "couch-helper"))
        self.assertEqual(skill_merged["description"], "A skill.")

    def test_merge_frontmatter_omits_name_for_rule_and_command(self) -> None:
        self.assets.add_shared_asset("widget", core_description="Core description.")
        asset = discover_assets(self.assets.root)[0]
        cursor_wrapper = next(w for w in asset.wrappers if w.target == "cursor")
        rule_merged = merge_frontmatter(
            asset.core,
            cursor_wrapper.doc,
            asset_id=asset.asset_id,
            family="rule",
        )
        self.assertNotIn("name", rule_merged)

        command_doc = parse_document("---\n---\n\nRun the thing.\n")
        command_merged = merge_frontmatter(
            asset.core,
            command_doc,
            asset_id=asset.asset_id,
            family="command",
        )
        self.assertNotIn("name", command_merged)

    def test_substitute_core_replaces_marker_with_core_body(self) -> None:
        self.assets.add_shared_asset("widget")
        asset = discover_assets(self.assets.root)[0]
        cursor_wrapper = next(w for w in asset.wrappers if w.target == "cursor")
        body = substitute_core(asset.core, cursor_wrapper.doc)
        self.assertIn("Shared body.", body)
        self.assertNotIn("{{core}}", body)

    def test_render_document_quotes_only_ambiguous_scalars(self) -> None:
        fields = {
            "description": "Apply the project's conventions.",
            "globs": "**/*.py",
            "alwaysApply": False,
            "paths": ["**/*.py", "**/*.pyi"],
        }
        rendered = render_document(fields, "Body.\n")
        self.assertIn('description: Apply the project\'s conventions.', rendered)
        self.assertIn('globs: "**/*.py"', rendered)
        self.assertIn("alwaysApply: false", rendered)
        self.assertIn('  - "**/*.py"', rendered)
        self.assertTrue(rendered.startswith("---\n"))


class CompileAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = TempAssetsRoot()
        self.addCleanup(self.assets.close)

    def test_compiles_shared_and_single_platform_assets(self) -> None:
        self.assets.add_shared_asset("widget")
        self.assets.add_single_platform_asset("solo")
        artifacts = compile_assets(self.assets.root)
        by_key = {(a.asset_id, a.target, a.family): a for a in artifacts}
        self.assertEqual(len(artifacts), 3)
        self.assertIn(("widget", "cursor", "rule"), by_key)
        self.assertIn(("widget", "claude", "rule"), by_key)
        self.assertIn(("solo", "cursor", "agent"), by_key)
        self.assertEqual(by_key[("widget", "cursor", "rule")].relative_path, Path("rules/couch-widget.mdc"))
        self.assertEqual(by_key[("widget", "claude", "rule")].relative_path, Path("rules/couch-widget.md"))
        self.assertEqual(by_key[("solo", "cursor", "agent")].relative_path, Path("agents/couch-solo.md"))

    def test_compiled_skill_and_agent_include_name_frontmatter(self) -> None:
        self.assets.add_single_platform_asset("solo")
        _write(
            self.assets.root / "helper" / "core.md",
            "---\ndescription: Helper skill.\n---\n\n# Helper\n\nBody.\n",
        )
        _write(
            self.assets.root / "helper" / "cursor" / "skill.md",
            "---\n---\n\n{{core}}\n",
        )
        _write(
            self.assets.root / "helper" / "claude" / "skill.md",
            "---\ndisable-model-invocation: true\n---\n\n{{core}}\n",
        )
        artifacts = compile_assets(self.assets.root)
        by_key = {(a.asset_id, a.target, a.family): a for a in artifacts}

        agent = by_key[("solo", "cursor", "agent")]
        self.assertTrue(agent.content.startswith("---\nname: couch-solo\n"))
        self.assertIn("description: Solo agent.", agent.content)

        for target in ("cursor", "claude"):
            skill = by_key[("helper", target, "skill")]
            self.assertTrue(skill.content.startswith("---\nname: couch-helper\n"))
            self.assertIn("description: Helper skill.", skill.content)

    def test_compiled_rule_and_command_omit_name_frontmatter(self) -> None:
        self.assets.add_shared_asset("widget")
        _write(
            self.assets.root / "run-it" / "core.md",
            "---\ndescription: Run the command.\n---\n\n# Run\n\nBody.\n",
        )
        _write(
            self.assets.root / "run-it" / "cursor" / "command.md",
            "---\n---\n\n{{core}}\n",
        )
        artifacts = compile_assets(self.assets.root)
        by_key = {(a.asset_id, a.target, a.family): a for a in artifacts}

        for key in (("widget", "cursor", "rule"), ("widget", "claude", "rule")):
            parsed = parse_document(by_key[key].content)
            self.assertNotIn("name", parsed.frontmatter)

        command = by_key[("run-it", "cursor", "command")]
        parsed_command = parse_document(command.content)
        self.assertNotIn("name", parsed_command.frontmatter)
        self.assertEqual(parsed_command.frontmatter["description"], "Run the command.")

    def test_raises_compiler_error_with_every_violation(self) -> None:
        _write(self.assets.root / "broken" / "cursor" / "agent.md", "---\ndescription: x\n---\n\nBody.\n")
        _write(self.assets.root / "also-broken" / "cursor" / "rule.md", "---\ndescription: x\n---\n\nBody.\n")
        with self.assertRaises(CompilerError) as ctx:
            compile_assets(self.assets.root)
        joined = "\n".join(ctx.exception.errors)
        self.assertIn("broken", joined)
        self.assertIn("also-broken", joined)
        self.assertGreaterEqual(len(ctx.exception.errors), 2)


class HostProfileTests(unittest.TestCase):
    def test_registry_contains_cursor_and_claude(self) -> None:
        self.assertEqual(tuple(HOST_PROFILES.keys()), ("cursor", "claude"))

    def test_get_host_profile_returns_profile(self) -> None:
        profile = get_host_profile("cursor")
        self.assertIsInstance(profile, CursorHostProfile)
        self.assertEqual(profile.name, "cursor")
        self.assertEqual(profile.default_install_dir, "~/.cursor")
        self.assertEqual(profile.style_dialect, "universal_xml")

    def test_get_host_profile_unknown_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_host_profile("chatgpt")

    def test_resolve_install_dir_expands_tilde(self) -> None:
        profile = get_host_profile("claude")
        self.assertIsInstance(profile, ClaudeHostProfile)
        resolved = resolve_install_dir(profile, Path("/home/tester"))
        self.assertEqual(resolved, Path("/home/tester/.claude"))

    def test_profile_extensions_and_directories(self) -> None:
        cursor = get_host_profile("cursor")
        claude = get_host_profile("claude")
        self.assertEqual(cursor.extensions["rule"], "mdc")
        self.assertEqual(claude.extensions["rule"], "md")
        self.assertEqual(cursor.family_directories["skill"], "skills")


class PolymorphicHostProfileValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cursor = create_default_profiles()["cursor"]
        self.claude = create_default_profiles()["claude"]

    def test_cursor_agent_requires_model(self) -> None:
        errors = self.cursor.validate_family_frontmatter("agent", {})
        self.assertEqual(errors, ["cursor agent wrappers require a model field"])

    def test_cursor_rule_requires_alwaysapply(self) -> None:
        errors = self.cursor.validate_family_frontmatter("rule", {})
        self.assertEqual(errors, ["cursor rule wrappers require an alwaysApply field"])

    def test_cursor_valid_frontmatter_has_no_errors(self) -> None:
        errors = self.cursor.validate_family_frontmatter(
            "agent",
            {"model": "inherit", "alwaysApply": True},
        )
        self.assertEqual(errors, [])

    def test_claude_skill_requires_disable_model_invocation(self) -> None:
        errors = self.claude.validate_family_frontmatter("skill", {})
        self.assertEqual(errors, ["claude skill wrappers require disable-model-invocation: true"])

    def test_claude_valid_skill_frontmatter_has_no_errors(self) -> None:
        errors = self.claude.validate_family_frontmatter("skill", {"disable-model-invocation": True})
        self.assertEqual(errors, [])


class LoadHostProfilesTests(unittest.TestCase):
    def test_missing_config_path_uses_defaults(self) -> None:
        profiles = load_host_profiles(Path("/nonexistent/couchpilot.json"))
        cursor = profiles["cursor"]
        self.assertIsInstance(cursor, CursorHostProfile)
        self.assertEqual(cursor.default_install_dir, "~/.cursor")
        self.assertEqual(cursor.default_frontmatter["agent"], {"model": "inherit"})

    def test_custom_config_overrides_install_dir_and_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "couchpilot.json"
            config_path.write_text(
                json.dumps(
                    {
                        "hosts": {
                            "cursor": {
                                "install_dir": "~/custom-cursor",
                                "style_dialect": "custom_xml",
                                "default_frontmatter": {
                                    "agent": {"model": "gpt-5"},
                                },
                            },
                            "claude": {
                                "install_dir": "~/custom-claude",
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            profiles = load_host_profiles(config_path)
            cursor = profiles["cursor"]
            claude = profiles["claude"]
            self.assertEqual(cursor.default_install_dir, "~/custom-cursor")
            self.assertEqual(cursor.style_dialect, "custom_xml")
            self.assertEqual(cursor.default_frontmatter["agent"], {"model": "gpt-5"})
            self.assertEqual(claude.default_install_dir, "~/custom-claude")
            self.assertIsInstance(claude, ClaudeHostProfile)

    def test_invalid_json_falls_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "couchpilot.json"
            config_path.write_text("{not valid json", encoding="utf-8")
            profiles = load_host_profiles(config_path)
            self.assertEqual(profiles["cursor"].default_install_dir, "~/.cursor")
            self.assertEqual(profiles["claude"].style_dialect, "anthropic_xml")


class CoreOnlySynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = TempAssetsRoot()
        self.addCleanup(self.assets.close)

    def test_synthesizes_wrappers_for_both_targets_from_core_only_rule(self) -> None:
        _write(
            self.assets.root / "polyglot" / "core.md",
            "---\ndescription: Shared rule.\nfamily: rule\n---\n\n# Shared rule\n\nBody.\n",
        )
        artifacts = compile_assets(self.assets.root)
        by_key = {(a.asset_id, a.target, a.family): a for a in artifacts}
        self.assertEqual(len(artifacts), 2)
        self.assertIn(("polyglot", "cursor", "rule"), by_key)
        self.assertIn(("polyglot", "claude", "rule"), by_key)
        self.assertEqual(by_key[("polyglot", "cursor", "rule")].relative_path, Path("rules/couch-polyglot.mdc"))
        self.assertIn("alwaysApply: true", by_key[("polyglot", "cursor", "rule")].content)

    def test_core_only_without_family_is_an_error(self) -> None:
        _write(
            self.assets.root / "orphan" / "core.md",
            "---\ndescription: Missing family.\n---\n\nBody.\n",
        )
        with self.assertRaises(CompilerError) as ctx:
            compile_assets(self.assets.root)
        self.assertTrue(any("requires a family field" in e for e in ctx.exception.errors))

    def test_synthesized_global_rule_matches_explicit_cursor_wrapper(self) -> None:
        _write(
            self.assets.root / "global-rule" / "core.md",
            "---\ndescription: Global rule.\nfamily: rule\n---\n\n# Global\n\nBody.\n",
        )
        artifacts = compile_assets(self.assets.root)
        cursor = next(a for a in artifacts if a.asset_id == "global-rule" and a.target == "cursor")
        claude = next(a for a in artifacts if a.asset_id == "global-rule" and a.target == "claude")
        self.assertIn("alwaysApply: true", cursor.content)
        self.assertIn("# Global", cursor.content)
        self.assertNotIn("globs:", cursor.content)
        self.assertNotIn("paths:", claude.content)
        self.assertIn("# Global", claude.content)

    def test_synthesized_path_scoped_rule_matches_explicit_wrappers(self) -> None:
        _write(
            self.assets.root / "py-rule" / "core.md",
            '---\ndescription: Python rule.\nfamily: rule\nglobs: "**/*.py"\n---\n\n# Python\n\nBody.\n',
        )
        _write(
            self.assets.root / "test-rule" / "core.md",
            "---\ndescription: Test rule.\nfamily: rule\nglobs:\n"
            '  - "**/tests/**/*.py"\n  - "**/test_*.py"\n  - "**/*_test.py"\n'
            '  - "**/conftest.py"\n---\n\n# Tests\n\nBody.\n',
        )
        artifacts = compile_assets(self.assets.root)
        py_cursor = next(a for a in artifacts if a.asset_id == "py-rule" and a.target == "cursor")
        py_claude = next(a for a in artifacts if a.asset_id == "py-rule" and a.target == "claude")
        test_cursor = next(a for a in artifacts if a.asset_id == "test-rule" and a.target == "cursor")
        test_claude = next(a for a in artifacts if a.asset_id == "test-rule" and a.target == "claude")

        self.assertIn("alwaysApply: false", py_cursor.content)
        self.assertIn('globs: "**/*.py"', py_cursor.content)
        self.assertIn("paths:", py_claude.content)
        self.assertIn('  - "**/*.py"', py_claude.content)

        self.assertIn("alwaysApply: false", test_cursor.content)
        self.assertIn(
            'globs: "**/tests/**/*.py,**/test_*.py,**/*_test.py,**/conftest.py"',
            test_cursor.content,
        )
        self.assertIn('  - "**/tests/**/*.py"', test_claude.content)
        self.assertIn('  - "**/conftest.py"', test_claude.content)


class DestinationForTests(unittest.TestCase):
    def test_cursor_path_table(self) -> None:
        self.assertEqual(destination_for("cursor", "rule", "widget"), Path("rules/couch-widget.mdc"))
        self.assertEqual(destination_for("cursor", "command", "widget"), Path("commands/couch-widget.md"))
        self.assertEqual(destination_for("cursor", "agent", "widget"), Path("agents/couch-widget.md"))
        self.assertEqual(destination_for("cursor", "skill", "widget"), Path("skills/couch-widget/SKILL.md"))

    def test_claude_path_table(self) -> None:
        self.assertEqual(destination_for("claude", "rule", "widget"), Path("rules/couch-widget.md"))
        self.assertEqual(destination_for("claude", "command", "widget"), Path("commands/couch-widget.md"))
        self.assertEqual(destination_for("claude", "agent", "widget"), Path("agents/couch-widget.md"))
        self.assertEqual(destination_for("claude", "skill", "widget"), Path("skills/couch-widget/SKILL.md"))

    def test_unknown_target_or_family_raises(self) -> None:
        with self.assertRaises(KeyError):
            destination_for("chatgpt", "rule", "widget")
        with self.assertRaises(KeyError):
            destination_for("cursor", "workflow", "widget")


class FindWslWindowsCursorDirTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.proc_version = self.root / "proc_version"
        self.users_root = self.root / "Users"
        self.users_root.mkdir()

    def _write_proc(self, text: str) -> None:
        self.proc_version.write_text(text, encoding="utf-8")

    def _add_user_cursor(self, username: str) -> Path:
        cursor_dir = self.users_root / username / ".cursor"
        cursor_dir.mkdir(parents=True)
        return cursor_dir

    def test_returns_windows_cursor_dir_when_proc_version_mentions_microsoft(self) -> None:
        self._write_proc("Linux version 6.6.87-microsoft-standard-WSL2")
        expected = self._add_user_cursor("alice")

        found = find_wsl_windows_cursor_dir(
            proc_version=self.proc_version,
            users_root=self.users_root,
            environ={},
        )

        self.assertEqual(found, expected)

    def test_returns_windows_cursor_dir_when_wsl_distro_name_set(self) -> None:
        self._write_proc("Linux version 6.6.0-generic")
        expected = self._add_user_cursor("bob")

        found = find_wsl_windows_cursor_dir(
            proc_version=self.proc_version,
            users_root=self.users_root,
            environ={"WSL_DISTRO_NAME": "Ubuntu"},
        )

        self.assertEqual(found, expected)

    def test_skips_windows_system_user_directories(self) -> None:
        self._write_proc("Linux version 6.6.87-microsoft-standard-WSL2")
        for system_user in ("Public", "Default", "Default User", "All Users"):
            self._add_user_cursor(system_user)
        expected = self._add_user_cursor("carol")

        found = find_wsl_windows_cursor_dir(
            proc_version=self.proc_version,
            users_root=self.users_root,
            environ={},
        )

        self.assertEqual(found, expected)

    def test_returns_none_when_not_in_wsl(self) -> None:
        self._write_proc("Linux version 6.8.0-generic")
        self._add_user_cursor("dave")

        found = find_wsl_windows_cursor_dir(
            proc_version=self.proc_version,
            users_root=self.users_root,
            environ={},
        )

        self.assertIsNone(found)

    def test_returns_none_when_proc_version_missing(self) -> None:
        self._add_user_cursor("erin")

        found = find_wsl_windows_cursor_dir(
            proc_version=self.root / "missing-proc-version",
            users_root=self.users_root,
            environ={},
        )

        self.assertIsNone(found)

    def test_returns_none_when_no_user_has_cursor(self) -> None:
        self._write_proc("Linux version 6.6.87-microsoft-standard-WSL2")
        (self.users_root / "frank").mkdir()

        found = find_wsl_windows_cursor_dir(
            proc_version=self.proc_version,
            users_root=self.users_root,
            environ={},
        )

        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
