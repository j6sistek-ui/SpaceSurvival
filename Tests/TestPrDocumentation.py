"""Meaningful regression cases for the PR documentation review gate."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pr_documentation", ROOT / "Scripts/CheckPrDocumentation.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def valid_body():
    rows = [
        f"- [x] {label}: Reviewed unchanged — Documentation still describes the current behavior."
        for label in gate.LABELS
    ]
    return "\n".join(rows) + """
## Owner review
- Open: README.md and the local packaged Windows launcher.
- Check: Review the updated documentation and follow the first playtest session.
- Still open: Physical controller testing and the complete natural ten wave run.
## Validation
Python documentation tests passed; no gameplay source changed in this PR.
"""


class DocumentationReviewTests(unittest.TestCase):
    def test_completed_statuses(self):
        for status in gate.STATUSES:
            with self.subTest(status=status):
                body = valid_body().replace("Reviewed unchanged", status)
                self.assertEqual(gate.validate_body(body), [])

    def test_unchecked_template_is_not_a_review(self):
        self.assertTrue(gate.validate_body(valid_body().replace("[x]", "[ ]")))

    def test_each_missing_declaration_fails(self):
        for label in gate.LABELS:
            with self.subTest(label=label):
                body = "\n".join(line for line in valid_body().splitlines() if not line.startswith(f"- [x] {label}:"))
                self.assertTrue(gate.validate_body(body))

    def test_placeholder_and_short_explanations_fail(self):
        explanation = "Documentation still describes the current behavior."
        for placeholder in ("TBD", "TODO add the documentation later", "<files and specific reason>", "files/reason", "No change"):
            with self.subTest(placeholder=placeholder):
                self.assertTrue(gate.validate_body(valid_body().replace(explanation, placeholder)))

    def test_duplicate_declarations_fail_checked_or_unchecked(self):
        for mark in ("x", " "):
            with self.subTest(mark=mark):
                body = valid_body() + f"\n- [{mark}] State: Updated — PROJECT_STATE.md now records this handoff."
                self.assertTrue(gate.validate_body(body))

    def test_status_must_be_recognized(self):
        self.assertTrue(gate.validate_body(valid_body().replace("Reviewed unchanged", "Not applicable")))

    def test_owner_handoff_fields_required_and_unique(self):
        for field in ("Open", "Check", "Still open"):
            with self.subTest(field=field):
                body = "\n".join(line for line in valid_body().splitlines() if not line.startswith(f"- {field}:"))
                self.assertTrue(gate.validate_body(body))
                self.assertTrue(gate.validate_body(valid_body().replace("- " + field + ":", "- " + field + ": TBD\n- Duplicate:")))
                self.assertTrue(gate.validate_body(valid_body().replace("## Validation", f"- {field}: This duplicates the existing owner handoff.\n## Validation")))

    def test_missing_or_duplicate_sections_fail(self):
        for title in ("Owner review", "Validation"):
            with self.subTest(title=title):
                self.assertTrue(gate.validate_body(valid_body().replace("## " + title, "## Removed")))
                self.assertTrue(gate.validate_body(valid_body() + "\n## " + title + "\nRepeated content with more words."))

    def test_validation_placeholder_fails(self):
        body = valid_body().split("## Validation")[0] + "## Validation\nTBD"
        self.assertTrue(gate.validate_body(body))

    def test_comments_and_code_examples_do_not_satisfy_review(self):
        body = valid_body()
        for wrapped in (f"<!--\n{body}\n-->", f"```markdown\n{body}\n```", f"~~~\n{body}\n~~~"):
            with self.subTest(wrapped=wrapped[:10]):
                self.assertTrue(gate.validate_body(wrapped))
        self.assertEqual(gate.validate_body(body + "\n<!--\n" + body + "\n-->"), [])

    def test_draft_is_pending_but_ready_rechecks(self):
        self.assertEqual(gate.validate_event({"pull_request": {"draft": True, "body": None}}), (True, []))
        draft, errors = gate.validate_event({"pull_request": {"draft": False, "body": None}})
        self.assertFalse(draft)
        self.assertTrue(errors)

    def test_invalid_event_types_fail_closed(self):
        for event in (None, [], {}, {"pull_request": []}, {"pull_request": {"draft": "false"}}, {"pull_request": {"body": ["unexpected"]}}):
            with self.subTest(event=event):
                draft, errors = gate.validate_event(event)
                self.assertFalse(draft)
                self.assertTrue(errors)

    def test_cli_and_shell_text_remain_data(self):
        with tempfile.TemporaryDirectory(prefix="spacesurvival-pr-docs-") as temporary:
            folder = Path(temporary)
            marker = folder / "must-not-exist"
            payload = f"$(touch {marker}); `touch {marker}`; powershell -Command Write-Output harmless"
            body = valid_body().replace("Documentation still describes the current behavior.", payload)
            event = folder / "event.json"
            event.write_text(json.dumps({"pull_request": {"draft": False, "body": body}}), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["--event", str(event)]), 0)
            self.assertFalse(marker.exists())

    def test_cli_reports_invalid_json_without_echoing_input(self):
        with tempfile.TemporaryDirectory(prefix="spacesurvival-pr-docs-") as temporary:
            event = Path(temporary) / "event.json"
            event.write_text("private malformed event text", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                self.assertEqual(gate.main(["--event", str(event)]), 1)
            self.assertNotIn("private malformed", output.getvalue())



class RepositoryConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="spacesurvival-doc-consistency-")
        self.root = Path(self.temporary.name)
        (self.root / "docs").mkdir()
        self.put("docs/KNOWN_ISSUES.md", "**2 open / 0 passed**\n1. [ ] First case\n2. [ ] Second case\n")
        self.put("README.md", "[Open work](docs/KNOWN_ISSUES.md)\n")
        self.put("PROJECT_STATE.md", "[State](docs/PROJECT_STATE.md)\n[Open work](docs/KNOWN_ISSUES.md)\n")
        self.put("docs/PROJECT_STATE.md", "Current source, local build and published release summary.\n")
        self.put("docs/PLAYTEST_TOMORROW.md", "[Cases](KNOWN_ISSUES.md#hands-on-acceptance-cases)\n[State](PROJECT_STATE.md)\n")

    def tearDown(self):
        self.temporary.cleanup()

    def put(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def test_canonical_counts_and_redirects_pass(self):
        self.assertEqual(gate.validate_repository(self.root), [])
        self.put("docs/KNOWN_ISSUES.md", "**1 open / 1 passed**\n1. [x] First case\n2. [ ] Second case\n")
        self.assertEqual(gate.validate_repository(self.root), [])

    def test_count_drift_fails(self):
        for content in (
            "**2 open / 0 passed**\n1. [x] First case\n2. [ ] Second case\n",
            "**2 open / 0 passed**\n1. [ ] First case\n",
            "1. [ ] First case\n2. [ ] Second case\n",
            "**2 open / 0 passed**\n**2 open / 0 passed**\n1. [ ] First case\n2. [ ] Second case\n",
        ):
            with self.subTest(content=content):
                self.put("docs/KNOWN_ISSUES.md", content)
                self.assertTrue(gate.validate_repository(self.root))

    def test_duplicate_checklist_copy_fails_in_each_navigation_document(self):
        for name in ("README.md", "PROJECT_STATE.md", "docs/PROJECT_STATE.md", "docs/PLAYTEST_TOMORROW.md"):
            with self.subTest(name=name):
                original = (self.root / name).read_text(encoding="utf-8")
                self.put(name, original + "\n1. [ ] Copied acceptance case\n")
                self.assertTrue(gate.validate_repository(self.root))
                self.put(name, original)

    def test_missing_redirect_fails(self):
        for name in ("README.md", "PROJECT_STATE.md", "docs/PLAYTEST_TOMORROW.md"):
            with self.subTest(name=name):
                original = (self.root / name).read_text(encoding="utf-8")
                self.put(name, "Navigation without the canonical document links.")
                self.assertTrue(gate.validate_repository(self.root))
                self.put(name, original)

    def test_missing_document_or_duplicate_case_number_fails(self):
        (self.root / "docs/PROJECT_STATE.md").unlink()
        self.assertTrue(gate.validate_repository(self.root))
        self.put("docs/PROJECT_STATE.md", "Restored state summary.")
        self.put("docs/KNOWN_ISSUES.md", "**2 open / 0 passed**\n1. [ ] First case\n1. [ ] Duplicate case\n")
        self.assertTrue(gate.validate_repository(self.root))

    def test_draft_does_not_bypass_repository_consistency(self):
        event = self.root / "event.json"
        event.write_text(json.dumps({"pull_request": {"draft": True, "body": None}}), encoding="utf-8")
        self.put("docs/KNOWN_ISSUES.md", "**2 open / 0 passed**\n1. [x] First case\n2. [ ] Second case\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(gate.main(["--repo", str(self.root), "--event", str(event)]), 1)
if __name__ == "__main__":
    unittest.main()