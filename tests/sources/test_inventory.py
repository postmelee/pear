"""Owned fixtures exercise audit content, provenance and fail-closed boundaries."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

MODULE_PATH = Path(__file__).resolve().parents[2] / "tools/sources/validate_inventory.py"
spec = importlib.util.spec_from_file_location("pear_source_inventory", MODULE_PATH)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args, data=None):
    env = {k: value for k, value in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
               GIT_AUTHOR_DATE="2000-01-01T00:00:00Z", GIT_COMMITTER_DATE="2000-01-01T00:00:00Z")
    return subprocess.check_output(["git", "-C", str(repo), *args], input=data, env=env, stderr=subprocess.DEVNULL)


def make_repo(root):
    repo = root / "cache/source/repo.git"
    repo.parent.mkdir(parents=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", "--object-format=sha1", str(repo)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    content = b"Owned source fixture.\n"
    blob = git(repo, "hash-object", "-w", "--stdin", data=content).decode().strip()
    tree = git(repo, "mktree", data=f"100644 blob {blob}\tfile.txt\n".encode()).decode().strip()
    commit = git(repo, "commit-tree", tree, data=b"Owned initial fixture\n").decode().strip()
    git(repo, "update-ref", "refs/heads/main", commit)
    git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    listing = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    (root / "cache/source/tree-listing.z").write_bytes(listing)
    return repo, content, blob, tree, commit, listing


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = tempfile.TemporaryDirectory(prefix="pear-owned-source-template-")
        root = Path(cls.template.name)
        _, content, blob, tree, commit, listing = make_repo(root)
        cls.base_manifest = {
            "schema_version": 1, "record_kind": "source_audit", "issue": 1, "stage": 3,
            "audit_complete": False, "decision": "unassessed", "source_ready": False,
            "qualification": {"runtime": "unassessed", "game": "unassessed", "distribution": "unassessed"},
            "evidence_document": "evidence.json", "evidence_documents": ["evidence.json"],
            "components": [{"component_id": "source", "role": "fixture-source",
                            "source": {"kind": "git", "url": "https://example.invalid/source.git", "requested_ref": "main",
                                       "object_format": "sha1", "commit_object_id": commit, "tree_object_id": tree},
                            "acquisition": {"status": "acquired", "cache_path": "source/repo.git"},
                            "content_digests": [{"algorithm": "sha256", "scope": "git_tree_listing_bytes",
                                                 "value": sha(listing), "cache_path": "source/tree-listing.z",
                                                 "size_bytes": len(listing)}],
                            "readiness": "unassessed", "terms": {"status": "unassessed"},
                            "patches": {"ordered_series": []}, "evidence_refs": ["source-file"]}],
            "dependencies": [], "patch_inventory": [], "source_requirements": [], "unresolved_inputs": [],
            "requirements": [{"requirement_id": "source-coverage", "status": "partial",
                              "remaining": "Fixture has not been qualified.", "evidence_refs": ["source-file"]}],
            "candidate_toolchain": [{"tool_id": "fixture-tool", "role": "build_time_only", "status": "metadata_observed",
                                     "version": "1.0-fixture", "compatibility": "unverified", "evidence_refs": ["fixture-metadata"]}]}
        cls.base_evidence = {"schema_version": 1, "issue": 1, "records": [
            {"evidence_id": "source-file", "component_id": "source", "commit_object_id": commit,
             "blob_object_id": blob, "path": "file.txt", "size_bytes": len(content), "line_count": 1,
             "digest": {"algorithm": "sha256", "value": sha(content), "scope": "git_blob_bytes"}},
            {"evidence_id": "fixture-metadata", "observed_version": "1.0-fixture", "exit_code": 0, "observation": "Synthetic test metadata; not an installed tool claim."}]}

    @classmethod
    def tearDownClass(cls):
        cls.template.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pear-owned-source-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(Path(self.template.name) / "cache", self.root / "cache")
        self.manifest = copy.deepcopy(self.base_manifest)
        self.evidence = copy.deepcopy(self.base_evidence)
        self.path = self.root / "runtime/sources/manifest.json"
        self.path.parent.mkdir(parents=True)
        self.repo = self.root / "cache/source/repo.git"

    def save(self):
        self.path.write_text(json.dumps(self.manifest))
        (self.root / "evidence.json").write_text(json.dumps(self.evidence))

    def validate(self, **kwargs):
        self.save()
        return v.validate_inventory(self.path, self.root / "cache", **kwargs)

    def invalid(self, code=None):
        result, status = self.validate()
        self.assertEqual(status, 1, result)
        self.assertFalse(result["record_valid"])
        self.assertFalse(result["source_ready"])
        if code:
            self.assertEqual(result["errors"][0]["code"], code, result)
        self.assertNotIn(str(self.root), json.dumps(result))
        return result

    def component(self):
        return self.manifest["components"][0]

    def complete(self, decision="blocked"):
        self.manifest.update(audit_complete=True, decision=decision, source_ready=decision == "go")
        self.manifest["requirements"][0]["status"] = "blocked" if decision == "blocked" else "needs-port"

    def add_archive(self, unsafe=False):
        path = self.root / "cache/archive.tar.gz"
        body = b"Owned archive fixture\n"
        with tarfile.open(path, "w:gz") as archive:
            item = tarfile.TarInfo("../escape" if unsafe else "source.txt")
            item.size = len(body)
            archive.addfile(item, io.BytesIO(body))
        data = path.read_bytes()
        self.manifest["components"].append({"component_id": "archive", "role": "archive-fixture",
            "source": {"kind": "archive", "url": "https://example.invalid/archive.tar.gz", "archive_format": "tar+gzip"},
            "acquisition": {"status": "acquired", "cache_path": "archive.tar.gz"},
            "content_digests": [{"algorithm": "sha256", "value": sha(data), "scope": "downloaded_archive_bytes",
                                 "cache_path": "archive.tar.gz", "size_bytes": len(data)}]})
        self.evidence["vendor_archive_audit"] = {"evidence_id": "archive-evidence", "component_id": "archive",
            "archive_sha256": sha(data), "archive_url": "https://example.invalid/archive.tar.gz",
            "inspection_scope": {"selected_members": [{"path": "source.txt", "sha256": sha(body),
                                                        "size_bytes": len(body), "scope": "archive_member_bytes"}]}}

    def add_patch(self):
        source = self.component()["source"]
        parent = source["commit_object_id"]
        # Empty-tree-change commit is intentional: no borrowed upstream code is used.
        commit = git(self.repo, "commit-tree", source["tree_object_id"], "-p", parent, data=b"Owned patch fixture\n").decode().strip()
        source["commit_object_id"] = commit
        self.evidence["records"][0]["commit_object_id"] = commit
        git(self.repo, "update-ref", "refs/heads/main", commit)
        patch_bytes = git(self.repo, "show", "--format=email", "--binary", commit)
        (self.root / "cache/fixture.patch").write_bytes(patch_bytes)
        digest = {"algorithm": "sha256", "value": sha(patch_bytes), "scope": "patch_file_bytes"}
        applicability = [{"target": "original-parent", "base_commit": parent, "check_exit_code": 0,
                          "status": "applies", "applied": False}]
        self.manifest["patch_inventory"] = [{"patch_id": "owned-patch", "component_id": "source",
            "source_url": "https://example.invalid/patch", "cache_path": "fixture.patch", "digest": digest,
            "size_bytes": len(patch_bytes), "order": 1, "original_base_commit": parent,
            "applicability": applicability, "evidence_refs": ["patch-evidence"]}]
        self.evidence["records"].append({"evidence_id": "patch-evidence", "patch_id": "owned-patch",
            "origin": {"parent": parent, "commit": commit}, "order": 1, "digest": digest,
            "patch_url": "https://example.invalid/patch", "applicability": applicability,
            "terms_scope": "Owned synthetic fixture data."})

    def add_gitlink(self):
        source = self.component()["source"]
        child = source["commit_object_id"]
        file_blob = self.evidence["records"][0]["blob_object_id"]
        tree = git(self.repo, "mktree", data=f"100644 blob {file_blob}\tfile.txt\n160000 commit {child}\tdep\n".encode()).decode().strip()
        commit = git(self.repo, "commit-tree", tree, data=b"Owned submodule fixture\n").decode().strip()
        git(self.repo, "update-ref", "refs/heads/main", commit)
        source.update(commit_object_id=commit, tree_object_id=tree)
        self.evidence["records"][0]["commit_object_id"] = commit
        data = git(self.repo, "ls-tree", "-r", "-z", "--full-tree", commit)
        (self.root / "cache/source/tree-listing.z").write_bytes(data)
        self.component()["content_digests"][0].update(value=sha(data), size_bytes=len(data))
        self.manifest["components"].append({"component_id": "dep", "role": "unselected-gitlink-input",
            "source": {"kind": "git", "url": "https://example.invalid/dep.git", "object_format": "sha1",
                       "commit_object_id": child, "tree_object_id": None},
            "acquisition": {"status": "not_acquired", "cache_path": None, "reason": "Excluded owned fixture."},
            "content_digests": []})
        self.manifest["dependencies"] = [{"parent": "source", "dependency": "dep", "relationship": "git_submodule",
            "path": "dep", "declared_url": "https://example.invalid/dep.git", "declared_commit_object_id": child,
            "acquisition_status": "not_acquired"}]

    def test_valid_incomplete_record(self):
        result, code = self.validate()
        self.assertEqual(code, 0, result)
        self.assertTrue(result["record_valid"])
        self.assertFalse(result["audit_complete"])
        self.assertEqual(result["checks"]["acquired_git"], 1)
        self.assertEqual(result["checks"]["source_blobs"], 1)

    def test_incomplete_require_complete_refused(self):
        result, code = self.validate(require_complete=True)
        self.assertEqual(code, 3)
        self.assertTrue(result["record_valid"])

    def test_complete_blocked_record_is_valid_and_complete(self):
        self.complete()
        result, code = self.validate(require_complete=True)
        self.assertEqual(code, 0, result)
        result, code = self.validate(require_source_ready=True)
        self.assertEqual(code, 3, result)
        self.assertTrue(result["record_valid"])
        self.assertFalse(result["source_ready"])

    def test_complete_needs_port_record_does_not_become_ready(self):
        self.complete("needs-port")
        result, code = self.validate(require_complete=True)
        self.assertEqual(code, 0, result)
        self.assertEqual(self.validate(require_source_ready=True)[1], 3)

    def test_fully_accounted_positive_fixture(self):
        self.complete("go")
        self.manifest["requirements"][0]["status"] = "verified"
        self.component().update(readiness="verified", terms={"status": "reviewed"})
        self.manifest["candidate_toolchain"][0]["compatibility"] = "verified"
        result, code = self.validate(require_source_ready=True)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["source_ready"])

    def test_ready_flag_cannot_override_unassessed(self):
        self.manifest["source_ready"] = True
        self.invalid("contradictory_readiness")

    def test_go_cannot_ignore_port_gaps(self):
        self.complete("go")
        self.invalid("unresolved_source_prerequisites")

    def test_complete_cannot_hide_unassessed_requirements(self):
        self.manifest.update(audit_complete=True, decision="blocked")
        self.invalid("incomplete_requirement_accounting")

    def test_inventory_cannot_assert_runtime_qualification(self):
        self.manifest["qualification"]["runtime"] = "passed"
        self.invalid("runtime_claim_forbidden")

    def test_duplicate_component_id(self):
        self.manifest["components"].append(copy.deepcopy(self.component()))
        self.invalid("duplicate_id")

    def test_missing_component_id(self):
        del self.component()["component_id"]
        self.invalid("invalid_id")

    def test_unknown_version(self):
        self.manifest["schema_version"] = 2
        self.invalid("invalid_manifest_shape")

    def test_unknown_manifest_field(self):
        self.manifest["trust_everything"] = True
        self.invalid("invalid_manifest_shape")

    def test_mutable_ref_without_commit(self):
        self.component()["source"]["commit_object_id"] = "main"
        self.invalid("invalid_object_identity")

    def test_wrong_tree_identity(self):
        self.component()["source"]["tree_object_id"] = "1" * 40
        self.invalid("git_identity_mismatch")

    def test_missing_commit_object(self):
        self.component()["source"]["commit_object_id"] = "1" * 40
        self.invalid("git_verification_failed")

    def test_wrong_listing_bytes(self):
        (self.root / "cache/source/tree-listing.z").write_bytes(b"wrong")
        self.invalid("content_digest_mismatch")

    def test_rehashed_wrong_listing_does_not_override_git(self):
        data = b"rehashed wrong listing"
        (self.root / "cache/source/tree-listing.z").write_bytes(data)
        self.component()["content_digests"][0].update(value=sha(data), size_bytes=len(data))
        self.invalid("git_listing_mismatch")

    def test_blob_digest_mismatch(self):
        self.evidence["records"][0]["digest"]["value"] = "0" * 64
        self.invalid("evidence_digest_mismatch")

    def test_blob_identity_mismatch(self):
        self.evidence["records"][0]["blob_object_id"] = "0" * 40
        self.invalid("evidence_blob_mismatch")

    def test_invalid_digest_scope(self):
        self.component()["content_digests"][0]["scope"] = "downloaded_archive_bytes"
        self.invalid("invalid_digest_scope")

    def test_git_sha_is_not_file_digest(self):
        self.component()["content_digests"][0]["value"] = self.component()["source"]["commit_object_id"]
        self.invalid("invalid_object_identity")

    def test_broken_evidence_reference(self):
        self.component()["evidence_refs"] = ["absent"]
        self.invalid("broken_evidence_reference")

    def test_duplicate_evidence_definition(self):
        self.evidence["records"].append(copy.deepcopy(self.evidence["records"][0]))
        self.invalid("duplicate_evidence_id")

    def test_evidence_identity_mismatch(self):
        self.evidence["issue"] = 9
        self.invalid("evidence_identity_mismatch")

    def test_unknown_component_in_evidence(self):
        self.evidence["records"][0]["component_id"] = "absent"
        self.invalid("broken_component_reference")

    def test_line_reference_out_of_bounds(self):
        self.manifest["requirements"][0]["sources"] = [{"evidence_id": "source-file", "lines": [1, 100]}]
        self.invalid("invalid_line_reference")

    def test_path_escape(self):
        self.component()["content_digests"][0]["cache_path"] = "../private-secret"
        self.invalid("unsafe_path")

    def test_absolute_path(self):
        self.component()["content_digests"][0]["cache_path"] = str(self.root / "private-secret")
        self.invalid("unsafe_path")

    def test_evidence_path_escape(self):
        self.manifest["evidence_document"] = "../private-secret"
        self.manifest["evidence_documents"] = ["../private-secret"]
        self.invalid("unsafe_path")

    def test_symlink_file_rejected(self):
        path = self.root / "cache/source/tree-listing.z"
        data = path.read_bytes()
        path.unlink()
        (self.root / "sentinel").write_bytes(data)
        path.symlink_to(self.root / "sentinel")
        self.invalid()
        self.assertEqual((self.root / "sentinel").read_bytes(), data)

    def test_symlink_directory_rejected(self):
        (self.root / "cache/source").rename(self.root / "sentinel")
        (self.root / "cache/source").symlink_to(self.root / "sentinel")
        self.invalid()

    def test_fifo_refused_without_blocking(self):
        path = self.root / "cache/source/tree-listing.z"
        path.unlink()
        os.mkfifo(path)
        self.invalid("nonregular_input")

    def test_symlink_inside_git_repo_rejected(self):
        (self.repo / "private-link").symlink_to(self.root / "sentinel")
        self.invalid("unsafe_git_repository")

    def test_git_alternates_refused(self):
        (self.repo / "objects/info/alternates").write_text(str(self.root / "sentinel"))
        self.invalid("external_git_storage")

    def test_git_external_include_refused(self):
        with (self.repo / "config").open("a") as f:
            f.write('\n[include]\n path = /private/sentinel\n')
        self.invalid("unsafe_git_config")

    def test_git_fsck_external_skiplist_refused(self):
        with (self.repo / "config").open("a") as f:
            f.write('\n[fsck]\n skipList = /private/sentinel\n')
        self.invalid("unsafe_git_config")

    def test_git_output_is_bounded(self):
        old = v.MAX_GIT_OUTPUT
        try:
            v.MAX_GIT_OUTPUT = 2
            with self.assertRaises(v.Invalid) as raised:
                v.bounded_git(shutil.which("git"), self.repo, ["rev-parse", "HEAD"])
            self.assertEqual(raised.exception.code, "git_output_limit")
        finally:
            v.MAX_GIT_OUTPUT = old

    def test_git_timeout_reaps_child(self):
        old = v.GIT_TIMEOUT
        try:
            v.GIT_TIMEOUT = 0
            with self.assertRaises(v.Invalid) as raised:
                v.bounded_git(shutil.which("git"), self.repo, ["rev-parse", "HEAD"])
            self.assertEqual(raised.exception.code, "git_timeout")
        finally:
            v.GIT_TIMEOUT = old

    def test_git_promisor_refused(self):
        (self.repo / "objects/pack").mkdir(exist_ok=True)
        (self.repo / "objects/pack/owned.promisor").touch()
        self.invalid("partial_git_repository")

    def test_missing_gitlink_record(self):
        self.add_gitlink()
        self.manifest["dependencies"] = []
        self.invalid("unrecorded_gitlink")

    def test_excluded_gitlink_is_accounted_without_acquisition(self):
        self.add_gitlink()
        result, code = self.validate()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["checks"]["gitlinks"], 1)

    def test_gitlink_id_mismatch(self):
        self.add_gitlink()
        self.manifest["dependencies"][0]["declared_commit_object_id"] = "0" * 40
        self.invalid("gitlink_identity_mismatch")

    def test_missing_gitlink_component(self):
        self.add_gitlink()
        self.manifest["components"].pop()
        self.invalid("broken_component_reference")

    def test_unacquired_input_needs_reason(self):
        self.add_gitlink()
        del self.manifest["components"][1]["acquisition"]["reason"]
        self.invalid("unaccounted_missing_input")

    def test_archive_bytes_verified(self):
        self.add_archive()
        result, code = self.validate()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["checks"]["archive_members"], 1)

    def test_archive_byte_change(self):
        self.add_archive()
        with (self.root / "cache/archive.tar.gz").open("ab") as f:
            f.write(b"corruption")
        self.invalid("content_digest_mismatch")

    def test_archive_member_digest_change(self):
        self.add_archive()
        self.evidence["vendor_archive_audit"]["inspection_scope"]["selected_members"][0]["sha256"] = "0" * 64
        self.invalid("archive_member_mismatch")

    def test_unsafe_archive_member_refused_without_extraction(self):
        self.add_archive(unsafe=True)
        self.invalid("unsafe_path")
        self.assertFalse((self.root / "escape").exists())

    def test_patch_provenance_and_exact_bytes(self):
        self.add_patch()
        result, code = self.validate()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["checks"]["patches"], 1)

    def test_patch_corruption(self):
        self.add_patch()
        (self.root / "cache/fixture.patch").write_bytes(b"changed")
        self.invalid("patch_digest_mismatch")

    def test_patch_missing_provenance(self):
        self.add_patch()
        self.manifest["patch_inventory"][0]["evidence_refs"] = ["source-file"]
        self.invalid("missing_patch_provenance")

    def test_patch_base_mismatch(self):
        self.add_patch()
        self.manifest["patch_inventory"][0]["original_base_commit"] = "0" * 40
        self.invalid("patch_provenance_mismatch")

    def test_patch_missing_terms(self):
        self.add_patch()
        del self.evidence["records"][-1]["terms_scope"]
        self.invalid("patch_provenance_mismatch")

    def test_patch_order_gap(self):
        self.add_patch()
        self.component()["patches"]["candidate_series"] = [{"patch_id": "owned-patch", "order": 2}]
        self.invalid("invalid_patch_series")

    def test_source_url_credentials_not_accepted(self):
        self.component()["source"]["url"] = "https://secret:password@example.invalid/source"
        result = self.invalid("invalid_source_url")
        self.assertNotIn("password", json.dumps(result))

    def test_duplicate_json_key_refused(self):
        self.save()
        self.path.write_bytes(b'{"schema_version":1,"schema_version":1}')
        result, code = v.validate_inventory(self.path, self.root / "cache")
        self.assertEqual(code, 1)
        self.assertEqual(result["errors"][0]["code"], "duplicate_json_key")

    def test_oversized_json_refused(self):
        self.save()
        self.path.write_bytes(b" " * (v.MAX_JSON + 1))
        result, code = v.validate_inventory(self.path, self.root / "cache")
        self.assertEqual(code, 1)
        self.assertEqual(result["errors"][0]["code"], "input_size_limit")

    def test_deep_json_refused(self):
        with self.assertRaises(v.Invalid):
            v.decode_json(b'{"nested":' + b'[' * 100 + b'0' + b']' * 100 + b'}')

    def test_overflowing_json_number_refused(self):
        with self.assertRaises(v.Invalid) as raised:
            v.decode_json(b'{"value":1e9999}')
        self.assertEqual(raised.exception.code, "nonfinite_json")

    def test_boolean_is_not_byte_count(self):
        self.component()["content_digests"][0]["size_bytes"] = True
        self.invalid("invalid_integer_field")

    def test_boolean_is_not_line_count(self):
        self.evidence["records"][0]["line_count"] = True
        self.invalid("invalid_integer_field")

    def test_boolean_is_not_patch_exit_code(self):
        self.add_patch()
        self.manifest["patch_inventory"][0]["applicability"][0]["check_exit_code"] = False
        self.invalid("invalid_integer_field")

    def test_boolean_is_not_patch_order(self):
        self.add_patch()
        self.manifest["patch_inventory"][0]["order"] = True
        self.invalid("invalid_integer_field")

    def test_float_is_not_entry_count(self):
        self.component()["tracked_entries"] = 1.0
        self.invalid("invalid_integer_field")

    def test_boolean_is_not_evidence_schema_version(self):
        self.evidence["schema_version"] = True
        self.invalid("evidence_identity_mismatch")

    def test_boolean_is_not_schema_version(self):
        self.manifest["schema_version"] = True
        self.invalid("invalid_manifest_shape")

    def test_unaccounted_component_cannot_claim_exclusion(self):
        self.component()["role"] = "unselected-gitlink-input"
        self.invalid("unaccounted_excluded_component")

    def test_patch_cannot_self_promote_selected_runtime_series(self):
        self.add_patch()
        self.manifest["patch_inventory"][0]["applied_to_runtime_candidate"] = True
        self.invalid("patch_selection_mismatch")

    def test_nonfinite_json_refused(self):
        with self.assertRaises(v.Invalid):
            v.decode_json(b'{"value":NaN}')

    def test_unknown_unacquired_identity_is_honest_incomplete(self):
        self.manifest["components"].append({"component_id": "unknown-input", "role": "future-source",
            "source": {"kind": "git", "url": "https://example.invalid/unknown", "object_format": "sha1",
                       "commit_object_id": None, "tree_object_id": None, "requested_ref": "main"},
            "acquisition": {"status": "not_acquired", "cache_path": None,
                            "reason": "No immutable resolution is established for this fixture."}, "content_digests": []})
        result, code = self.validate()
        self.assertEqual(code, 0, result)
        self.assertFalse(result["source_ready"])

    def test_installed_tool_version_cannot_drift_from_observation(self):
        self.manifest["candidate_toolchain"][0]["version"] = "999.0"
        self.invalid("tool_metadata_mismatch")

    def test_acquisition_evidence_cannot_claim_different_tree(self):
        self.evidence["records"].append({"evidence_id": "acquisition", "component_id": "source",
            "commit_object_id": self.component()["source"]["commit_object_id"], "tree_object_id": "0" * 40})
        self.invalid("evidence_source_mismatch")

    def test_malformed_nested_record_is_structured_failure(self):
        self.complete("go")
        self.manifest["requirements"][0]["status"] = "verified"
        self.component().update(readiness="verified", terms=[])
        self.invalid()

    def test_cli_error_omits_sensitive_argument(self):
        result = subprocess.run([shutil.which("python3"), str(MODULE_PATH), "--secret-private-path"], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"secret-private-path", result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["code"], "cli_usage")

    def test_cli_misuse_exit_two(self):
        result = subprocess.run([shutil.which("python3"), str(MODULE_PATH)], capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_cli_gate_and_json_output(self):
        self.save()
        result = subprocess.run([shutil.which("python3"), str(MODULE_PATH), "--manifest", str(self.path),
                                 "--cache-root", str(self.root / "cache"), "--require-source-ready"], capture_output=True)
        self.assertEqual(result.returncode, 3)
        self.assertTrue(json.loads(result.stdout)["record_valid"])
        self.assertEqual(result.stderr, b"")


if __name__ == "__main__":
    unittest.main()
