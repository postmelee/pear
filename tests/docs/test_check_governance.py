"""Exercise the documentation checker's public CLI with synthetic repositories."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/check_governance.py"
ROUTER = "mydocs/skills/pear-apple-tooling/SKILL.md"
INVENTORY = "mydocs/skills/pear-apple-tooling/references/upstream.json"
GUIDE = "docs/development/apple-tooling.md"
REPOSITORY = "https://github.com/apple/game-porting-toolkit"
REVISION = "4f42344c90be22112f46becc3fb9687f423f2f88"
EXPERT_REFERENCES = {
    "using-metal-validation": (),
    "using-gpucapture": (),
    "using-gpudebug": (),
    "debugging-rendering-issues": (
        "references/tier-1-instant-checks.md",
        "references/tier-2-state-inspection.md",
        "references/tier-3-data-inspection.md",
    ),
    "presenting-metal-drawables": (
        "references/frame-pacing.md",
        "references/hdr-colorspace.md",
    ),
    "managing-metal-cpp-lifetimes": (),
}
REQUIRED_MARKDOWN = (
    "README.md", "AGENTS.md", "CLAUDE.md", "host/AGENTS.md",
    "tests/AGENTS.md", "docs/AGENTS.md", ROUTER, GUIDE,
)


def source_inventory(revision=REVISION):
    """Build a finite source-reference fixture, independent of production code."""
    prefix = REPOSITORY + "/blob/" + revision + "/"
    manifest = "game-porting-skills/.codex-plugin/plugin.json"
    skills = []
    for name, references in EXPERT_REFERENCES.items():
        directory = "game-porting-skills/skills/" + name + "/"
        skills.append({
            "name": name,
            "path": directory + "SKILL.md",
            "url": prefix + directory + "SKILL.md",
            "references": [
                {"path": path, "url": prefix + directory + path}
                for path in references
            ],
        })
    return {
        "schema_version": 1,
        "repository": REPOSITORY,
        "revision": revision,
        "reviewed_on": "2026-09-28",
        "plugin": {
            "name": "game-porting-skills",
            "version": "1.0.0-beta.1",
            "manifest_path": manifest,
            "url": prefix + manifest,
        },
        "skills": skills,
        "tools": [
            {"name": "gpucapture", "minimum_macos": "27.0",
             "requirement_skill": "using-gpucapture"},
            {"name": "gpudebug", "minimum_macos": "27.0",
             "requirement_skill": "using-gpudebug"},
        ],
    }


class GovernanceCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="pear-governance-tests-")
        self.addCleanup(temporary.cleanup)
        self.scratch = Path(temporary.name)
        self.root = self.scratch / "repository"
        self.root.mkdir()
        self.unrelated_cwd = self.scratch / "unrelated"
        self.unrelated_cwd.mkdir()
        self.outside = self.scratch / "outside.md"
        self.outside.write_text("# Synthetic outside document\n", encoding="utf-8")
        for name in (*REQUIRED_MARKDOWN, "docs/README.md", "docs/architecture.md",
                     "docs/delivery-plan.md", "docs/contributing.md"):
            self.write(name, "# Synthetic fixture\n")
        self.write("README.md", "# Fixture\n[Documentation](docs/README.md)\n")
        self.write(ROUTER, (
            "# Example routing\n"
            "[Public guide](../../../docs/development/apple-tooling.md)\n"
            "[Pinned inventory](references/upstream.json)\n"
        ))
        self.save_inventory(source_inventory())
        for name in (".agents/skills", ".claude/skills"):
            link = self.root / name
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to("../mydocs/skills", target_is_directory=True)

    def write(self, name, text):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def save_inventory(self, value):
        self.write(INVENTORY, json.dumps(value, indent=2) + "\n")

    def run_checker(self, *arguments, checker=CHECKER):
        return subprocess.run(
            [sys.executable, str(checker), *map(str, arguments)],
            cwd=self.unrelated_cwd, capture_output=True, text=True, timeout=10,
        )

    def check(self):
        return self.run_checker("--root", self.root)

    def assert_passes(self, result=None):
        result = self.check() if result is None else result
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "", result.stderr)
        self.assertTrue(result.stdout.strip(), "A successful check needs a summary")

    def assert_rejected(self, *diagnostic_tokens, result=None):
        result = self.check() if result is None else result
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertTrue(result.stderr.strip(), "Failure needs a diagnostic")
        self.assertNotIn("Traceback", result.stderr)
        for token in diagnostic_tokens:
            self.assertIn(token, result.stderr)

    def test_valid_mini_repository_passes_from_an_unrelated_working_directory(self):
        self.assert_passes()

    def test_default_root_comes_from_script_location_not_working_directory(self):
        copied_checker = self.root / "tools/check_governance.py"
        copied_checker.parent.mkdir()
        shutil.copy2(CHECKER, copied_checker)
        self.assert_passes(self.run_checker(checker=copied_checker))

    def test_missing_root_and_a_file_in_place_of_root_have_clean_errors(self):
        for path in (self.scratch / "missing", self.outside):
            with self.subTest(path=path):
                result = self.run_checker("--root", path)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(str(path), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_help_and_invalid_arguments_follow_cli_exit_conventions(self):
        result = self.run_checker("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--root", result.stdout)
        result = self.run_checker("--not-a-valid-option")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(result.stderr.strip())
        self.assertNotIn("Traceback", result.stderr)

    def test_inline_images_angle_destinations_and_reference_definitions(self):
        self.write("docs/a guide.md", "# Guide\n")
        self.write("docs/picture.svg", "<svg xmlns=\"http://www.w3.org/2000/svg\"/>\n")
        self.write("README.md", (
            "[Plain](docs/README.md)\n"
            "[`Code-formatted label`](docs/README.md)\n"
            "![Image](docs/picture.svg)\n"
            "[Space](<docs/a guide.md>)\n"
            "[Title](docs/README.md \"A title\")\n"
            "[Directory](docs/)\n"
            "[reference]: docs/README.md \"Reference title\"\n"
            "[space-reference]: <docs/a guide.md>\n"
        ))
        self.assert_passes()

    def test_reference_definition_target_is_checked_without_claiming_use_resolution(self):
        self.write("docs/nested/page.md", "[example]: ../../missing-reference.md\n")
        self.assert_rejected("docs/nested/page.md", "missing-reference.md")

    def test_nested_documents_resolve_links_from_their_own_directory(self):
        self.write("docs/nested/page.md", "[Index](../README.md)\n")
        self.assert_passes()
        self.write("docs/nested/page.md", "[Missing](README.md)\n")
        self.assert_rejected("docs/nested/page.md", "README.md")

    def test_url_escaped_paths_query_and_fragments_check_only_file_existence(self):
        self.write("docs/a guide.md", "# Only this heading exists\n")
        self.write("README.md", (
            "[Encoded](docs/a%20guide.md?mode=review#not-a-real-heading)\n"
            "[Same file](#also-not-a-real-heading)\n"
        ))
        self.assert_passes()
        (self.root / "docs/a guide.md").unlink()
        self.assert_rejected("README.md", "a%20guide.md")

    def test_remote_urls_fences_inline_code_and_comments_are_not_local_targets(self):
        self.write("README.md", (
            "[Remote](https://not-contacted.invalid/missing.md)\n"
            "[Protocol relative](//not-contacted.invalid/missing.md)\n"
            "[Email](mailto:fixture@example.invalid)\n"
            "`[Inline example](missing-inline.md)`\n"
            "``[Backtick ` example](missing-double-inline.md)``\n"
            "```markdown\n[Example](missing-fence.md)\n```\n"
            "~~~markdown\n[Example](missing-tilde-fence.md)\n~~~\n"
            "````markdown\n```\n[Example](missing-long-fence.md)\n````\n"
            "<!-- [Hidden](missing-comment.md) -->\n"
            "<!--\n[Hidden](missing-multiline-comment.md)\n-->\n"
        ))
        self.assert_passes()

    def test_code_or_comments_do_not_hide_real_links_on_the_same_line(self):
        examples = (
            "`[Example](missing-example.md)` [Real](missing-real.md)\n",
            "<!-- [Example](missing-example.md) --> [Real](missing-real.md)\n",
            "[`Code label`](missing-real.md)\n",
        )
        for text in examples:
            with self.subTest(markdown=text):
                self.write("README.md", text)
                self.assert_rejected("README.md", "missing-real.md")

    def test_same_line_multibacktick_code_spans_do_not_open_fenced_blocks(self):
        for delimiter in ("```", "````"):
            with self.subTest(delimiter=delimiter):
                self.write("README.md", (
                    delimiter + "inline example" + delimiter + "\n"
                    "[Real link](missing-after-inline.md)\n"
                ))
                self.assert_rejected("README.md", "missing-after-inline.md")

    def test_missing_local_inline_and_image_targets_fail(self):
        for markdown in ("[Missing](docs/no-page.md)\n", "![Missing](docs/no-image.svg)\n"):
            with self.subTest(markdown=markdown):
                self.write("README.md", markdown)
                self.assert_rejected("README.md", "docs/no-")

    def test_missing_required_documents_and_inventory_cannot_disappear_silently(self):
        for name in (*REQUIRED_MARKDOWN, INVENTORY):
            target = self.root / name
            saved = target.read_text(encoding="utf-8")
            with self.subTest(path=name):
                target.unlink()
                self.assert_rejected(name)
                self.write(name, saved)

    def test_excluded_trees_do_not_impose_links_on_the_governed_documents(self):
        for name in ("analysis/private.md", "research/private.md",
                     "mydocs/working/historical.md", "mydocs/_templates/example.md"):
            self.write(name, "[Not a governed input](missing.md)\n")
        self.assert_passes()

    def test_absolute_and_escaping_destinations_fail_even_when_the_target_exists(self):
        destinations = (str(self.outside), "../outside.md",
                        "docs/%2e%2e/%2e%2e/outside.md")
        for destination in destinations:
            with self.subTest(destination=destination):
                self.write("README.md", "[Outside](<" + destination + ">)\n")
                self.assert_rejected("README.md")

    def test_a_link_cannot_escape_through_a_symlink(self):
        (self.root / "docs/outside.md").symlink_to(self.outside)
        self.write("README.md", "[Outside](docs/outside.md)\n")
        self.assert_rejected("README.md", "docs/outside.md")

    def test_windows_drive_absolute_targets_are_not_external_url_schemes(self):
        for target in ("C:/Users/private.md", "<C:/Users/private.md>"):
            with self.subTest(target=target):
                self.write("README.md", "[Absolute file](" + target + ")\n")
                self.assert_rejected("README.md", "C:/Users/private.md")

    def test_escaping_docs_directory_is_rejected_instead_of_silently_skipped(self):
        outside_docs = self.scratch / "outside-docs"
        outside_docs.mkdir()
        (outside_docs / "page.md").write_text("[Missing](absent.md)\n", encoding="utf-8")
        (self.root / "docs/outside").symlink_to(outside_docs, target_is_directory=True)
        self.assert_rejected("docs/outside")

    def test_contained_docs_directory_symlinks_are_followed_with_relative_targets(self):
        self.write("shared-docs/page.md", "[Sibling](sibling.md)\n")
        self.write("shared-docs/sibling.md", "# Shared document\n")
        (self.root / "docs/shared").symlink_to("../shared-docs", target_is_directory=True)
        self.assert_passes()
        self.write("shared-docs/page.md", "[Missing](missing-sibling.md)\n")
        self.assert_rejected("page.md", "missing-sibling.md")

    def test_docs_directory_cycles_have_a_bounded_failure(self):
        (self.root / "docs/loop").symlink_to(".", target_is_directory=True)
        self.assert_rejected("docs/loop")

    def test_both_discovery_paths_must_be_actual_symlinks(self):
        for name in (".agents/skills", ".claude/skills"):
            target = self.root / name
            with self.subTest(path=name):
                target.unlink()
                self.assert_rejected(name)
                target.mkdir()
                self.assert_rejected(name)
                target.rmdir()
                target.symlink_to("../mydocs/skills", target_is_directory=True)

    def test_discovery_symlinks_must_reach_the_shared_skill_directory(self):
        (self.root / "wrong-skills").mkdir()
        outside_skills = self.scratch / "outside-skills"
        outside_skills.mkdir()
        for name in (".agents/skills", ".claude/skills"):
            target = self.root / name
            for wrong in ("../wrong-skills", str(outside_skills), "../missing-skills"):
                with self.subTest(path=name, target=wrong):
                    target.unlink()
                    target.symlink_to(wrong, target_is_directory=True)
                    self.assert_rejected(name)
            target.unlink()
            target.symlink_to("../mydocs/skills", target_is_directory=True)

    def test_router_must_link_to_the_guide_and_inventory_not_merely_name_them(self):
        valid = (self.root / ROUTER).read_text(encoding="utf-8")
        for label, destination in (
                ("Public guide", "../../../docs/development/apple-tooling.md"),
                ("Pinned inventory", "references/upstream.json")):
            with self.subTest(destination=destination):
                self.write(ROUTER, valid.replace(f"[{label}]({destination})", destination))
                self.assert_rejected(ROUTER)

    def test_router_links_to_existing_wrong_documents_are_rejected(self):
        self.write("mydocs/skills/pear-apple-tooling/references/other.json", "{}\n")
        self.write(ROUTER, (
            "[Different guide](../../../docs/architecture.md)\n"
            "[Different inventory](references/other.json)\n"
        ))
        self.assert_rejected(ROUTER)

    def test_malformed_json_and_non_object_inventory_get_clean_diagnostics(self):
        self.write(INVENTORY, "{not valid json\n")
        self.assert_rejected(INVENTORY)
        for value in (None, [], "inventory", 1):
            with self.subTest(value=value):
                self.save_inventory(value)
                self.assert_rejected(INVENTORY)

    def test_required_inventory_fields_and_types_are_checked(self):
        for field in ("schema_version", "repository", "revision", "reviewed_on",
                      "plugin", "skills", "tools"):
            with self.subTest(field=field, mutation="missing"):
                inventory = source_inventory()
                del inventory[field]
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)
        for field, wrong in (("schema_version", True), ("schema_version", "1"),
                             ("schema_version", 2),
                             ("plugin", []), ("skills", {}), ("tools", {})):
            with self.subTest(field=field, value=wrong):
                inventory = source_inventory()
                inventory[field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)

    def test_repository_revision_and_review_date_require_valid_provenance(self):
        cases = (
            ("repository", "https://github.com/example/game-porting-toolkit"),
            ("revision", "main"), ("revision", REVISION[:12]),
            ("revision", "g" * 40),
            ("revision", 42), ("reviewed_on", "yesterday"),
            ("reviewed_on", "2026-02-30"), ("reviewed_on", None),
        )
        for field, wrong in cases:
            with self.subTest(field=field, value=wrong):
                inventory = source_inventory()
                inventory[field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)

    def test_consistent_immutable_revision_checks_format_not_remote_availability(self):
        for revision in ("a" * 40, REVISION.upper()):
            with self.subTest(revision=revision):
                self.save_inventory(source_inventory(revision))
                self.assert_passes()

    def test_plugin_identity_manifest_version_and_url_are_checked(self):
        cases = (
            ("name", "another-plugin"), ("version", ""), ("version", None),
            ("manifest_path", "../plugin.json"),
            ("url", REPOSITORY + "/blob/main/game-porting-skills/.codex-plugin/plugin.json"),
        )
        for field, wrong in cases:
            with self.subTest(field=field, value=wrong):
                inventory = source_inventory()
                inventory["plugin"][field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)

    def test_skills_cannot_be_missing_duplicate_or_malformed(self):
        for mutation in ("missing", "duplicate", "wrong-type"):
            with self.subTest(mutation=mutation):
                inventory = source_inventory()
                if mutation == "missing":
                    inventory["skills"].pop()
                elif mutation == "duplicate":
                    inventory["skills"][-1] = deepcopy(inventory["skills"][0])
                else:
                    inventory["skills"][0] = "not a skill object"
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, "skills")

    def test_skill_paths_urls_and_reference_types_are_checked(self):
        cases = (
            ("path", "game-porting-skills/skills/unrelated/SKILL.md"),
            ("url", REPOSITORY + "/blob/main/game-porting-skills/skills/using-metal-validation/SKILL.md"),
            ("references", {}),
        )
        for field, wrong in cases:
            with self.subTest(field=field):
                inventory = source_inventory()
                inventory["skills"][0][field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)

    def test_required_relative_references_cannot_be_missing_duplicate_or_malformed(self):
        for mutation in ("missing", "duplicate", "wrong-type"):
            with self.subTest(mutation=mutation):
                inventory = source_inventory()
                references = inventory["skills"][3]["references"]
                if mutation == "missing":
                    references.pop()
                elif mutation == "duplicate":
                    references[-1] = deepcopy(references[0])
                else:
                    references[0] = None
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, "references")

    def test_relative_references_use_their_own_skill_and_recorded_revision(self):
        cases = (
            ("path", "../other-skill/SKILL.md"),
            ("url", REPOSITORY + "/blob/main/game-porting-skills/skills/debugging-rendering-issues/references/tier-1-instant-checks.md"),
        )
        for field, wrong in cases:
            with self.subTest(field=field):
                inventory = source_inventory()
                inventory["skills"][3]["references"][0][field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)

    def test_tool_records_cannot_be_missing_duplicate_or_malformed(self):
        for mutation in ("missing", "duplicate", "wrong-type"):
            with self.subTest(mutation=mutation):
                inventory = source_inventory()
                if mutation == "missing":
                    inventory["tools"].pop()
                elif mutation == "duplicate":
                    inventory["tools"][-1] = deepcopy(inventory["tools"][0])
                else:
                    inventory["tools"][0] = []
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, "tools")

    def test_tool_requirements_need_the_reviewed_platform_and_matching_skill(self):
        for field, wrong in (("minimum_macos", "26.0"), ("minimum_macos", 27),
                             ("requirement_skill", "using-metal-validation"),
                             ("requirement_skill", None)):
            with self.subTest(field=field, value=wrong):
                inventory = source_inventory()
                inventory["tools"][0][field] = wrong
                self.save_inventory(inventory)
                self.assert_rejected(INVENTORY, field)


if __name__ == "__main__":
    unittest.main()
