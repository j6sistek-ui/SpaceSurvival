"""Check that a ready PR explains documentation freshness and the owner handoff.

Checks the review record plus canonical checklist counts and navigation; prose accuracy still needs review.
PR body text is parsed only as data; it is never evaluated or executed.
"""
import argparse
import json
from pathlib import Path
import re
import sys


LABELS = ("State", "Solutions", "Start/run", "System/evidence", "Storage/release", "Owner handoff")
STATUSES = ("Updated", "Reviewed unchanged")
PLACEHOLDERS = re.compile(
    r"<[^>]+>|\{\{.*?\}\}|\b(?:TBD|TODO|FIXME)\b|"
    r"(?:files\s*/\s*reason|reason here|describe here|fill (?:this|in)|replace (?:this|with))",
    re.IGNORECASE,
)


def visible_text(body):
    """Ignore commented instructions and code examples when locating declarations."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    lines = []
    fence = None
    for line in body.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = (marker.group(1)[0], len(marker.group(1)))
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1]:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)


def substantive(value):
    """A small placeholder filter; human review still establishes accuracy."""
    value = value.strip()
    if PLACEHOLDERS.search(value):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z0-9_/.-]*", value)
    return len(value) >= 16 and len(words) >= 3


def section(text, title, errors):
    headings = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    matches = [heading for heading in headings if heading.group(1) == title]
    if len(matches) != 1:
        errors.append(f"Expected exactly one '## {title}' section.")
        return ""
    match = matches[0]
    end = next((heading.start() for heading in headings if heading.start() > match.start()), len(text))
    return text[match.end():end].strip()


def validate_body(body):
    errors = []
    text = visible_text(body)
    for label in LABELS:
        # Count unchecked and malformed declarations too: duplicates cannot hide.
        rows = re.findall(
            rf"^\s*-\s+(?:\[[^\]]*\]\s*)?{re.escape(label)}:\s*([^\n]*)$",
            text,
            re.MULTILINE,
        )
        checked = re.findall(
            rf"^\s*-\s+\[[xX]\]\s+{re.escape(label)}:\s*([^\n]*)$",
            text,
            re.MULTILINE,
        )
        if len(rows) != 1 or len(checked) != 1:
            errors.append(f"{label}: require exactly one checked declaration.")
            continue
        status = re.fullmatch(r"(Updated|Reviewed unchanged)\s+—\s+(.+)", checked[0])
        if not status or not substantive(status.group(2)):
            errors.append(f"{label}: use Updated or Reviewed unchanged, an em dash, and a specific explanation.")

    owner = section(text, "Owner review", errors)
    for field in ("Open", "Check", "Still open"):
        values = re.findall(rf"^\s*-\s+{re.escape(field)}:\s*([^\n]*)$", owner, re.MULTILINE)
        if len(values) != 1 or not substantive(values[0]):
            errors.append(f"Owner review: require one substantive '{field}' field.")

    validation = section(text, "Validation", errors)
    if not substantive(validation):
        errors.append("Validation: describe checks and results, or explain why a check is not applicable.")
    return errors


def validate_event(event):
    if not isinstance(event, dict) or not isinstance(event.get("pull_request"), dict):
        return False, ["Event must contain a pull_request object."]
    pr = event["pull_request"]
    draft = pr.get("draft", False)
    if not isinstance(draft, bool):
        return False, ["pull_request.draft must be a boolean."]
    if draft:
        return True, []
    body = pr.get("body") or ""
    if not isinstance(body, str):
        return False, ["pull_request.body must be text."]
    return False, validate_body(body)



def validate_repository(root):
    """Check the single checklist's counts and navigation, without guessing prose truth."""
    errors = []
    files = (
        "docs/KNOWN_ISSUES.md", "README.md", "PROJECT_STATE.md",
        "docs/PROJECT_STATE.md", "docs/PLAYTEST_TOMORROW.md",
    )
    texts = {}
    for name in files:
        try:
            texts[name] = visible_text((root / name).read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            errors.append(f"{name}: required readable UTF-8 document is missing.")
    checklist = re.compile(r"^\s*(\d+)[.)]\s+\[([ xX])\]\s+", re.MULTILINE)
    known = texts.get("docs/KNOWN_ISSUES.md", "")
    cases = checklist.findall(known)
    summaries = re.findall(r"\*\*(\d+) open / (\d+) passed\*\*", known)
    if not cases:
        errors.append("docs/KNOWN_ISSUES.md: numbered acceptance cases are missing.")
    if len(summaries) != 1:
        errors.append("docs/KNOWN_ISSUES.md: require one '**N open / N passed**' summary.")
    else:
        opened = sum(mark == " " for _, mark in cases)
        passed = len(cases) - opened
        if tuple(map(int, summaries[0])) != (opened, passed):
            errors.append(f"docs/KNOWN_ISSUES.md: summary differs from cases ({opened} open / {passed} passed).")
    numbers = [int(number) for number, _ in cases]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("docs/KNOWN_ISSUES.md: case numbers must be unique and consecutive from 1.")
    for name in files[1:]:
        if checklist.search(texts.get(name, "")):
            errors.append(f"{name}: numbered acceptance cases belong only in docs/KNOWN_ISSUES.md.")

    links = {
        "README.md": ("docs/KNOWN_ISSUES.md",),
        "PROJECT_STATE.md": ("docs/PROJECT_STATE.md", "docs/KNOWN_ISSUES.md"),
        "docs/PLAYTEST_TOMORROW.md": ("KNOWN_ISSUES.md", "PROJECT_STATE.md"),
    }
    for name, targets in links.items():
        destinations = re.findall(r"\]\(([^)\s]+)\)", texts.get(name, ""))
        destinations = {destination.split("#", 1)[0] for destination in destinations}
        for target in targets:
            if target not in destinations:
                errors.append(f"{name}: require a Markdown link to {target}.")
    return errors
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, help="GitHub pull_request event JSON")
    parser.add_argument("--repo", type=Path, help="Repository root for checklist and navigation consistency")
    args = parser.parse_args(argv)
    if not args.event and not args.repo:
        parser.error("provide --repo, --event, or both")
    errors = validate_repository(args.repo) if args.repo else []
    draft = False
    if args.event:
        try:
            event = json.loads(args.event.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append("Cannot read a valid UTF-8 PR event JSON.")
        else:
            draft, event_errors = validate_event(event)
            errors.extend(event_errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    if args.repo:
        print("PASS: Canonical acceptance counts, checklist location and navigation agree.")
    if args.event:
        if draft:
            print("PENDING: Draft PR; complete documentation review before marking ready.")
        else:
            print("PASS: Documentation review declarations and owner handoff are present; accuracy still needs review.")
    return 0

if __name__ == "__main__":
    sys.exit(main())