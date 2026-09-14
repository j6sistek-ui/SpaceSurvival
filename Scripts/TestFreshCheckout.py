"""Run portable source validation against exact bytes exported from a Git commit.

The tested validator/helper are the current script files, identified separately.
The asset data comes only from git archive of the resolved immutable commit.
No source generation, Unreal process, asset import or owner save occurs.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPORT_PATHS = ("ContentSource", "Content", "model-rigged.glb")

CANDIDATE_HOOKS = {
    "AuthorSwiftCandidate.py": "ContentSource/SwiftCandidate/Report.json",
    "AuthorStationShell.py": "ContentSource/StationShellCandidate/Report.json",
    "AuthorMilkyWay.py": "ContentSource/ThirdParty/NASA/MilkyWay2020/CheckSource.py",
    "AuthorFieldCandidatesV3.py": "ContentSource/FieldCandidates/V3/SourceReport.json",
}


def require_registered_candidates(author_source, export_root):
    """A committed author hook makes its reviewed candidate input mandatory."""
    literals = {node.value.replace("\\", "/").rsplit("/", 1)[-1]
                for node in ast.walk(ast.parse(author_source))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    required = []
    for hook, relative in CANDIDATE_HOOKS.items():
        if hook in literals:
            assert (export_root / relative).is_file(), "Committed pipeline candidate is missing: " + relative
            required.append(relative)
    return required


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot(root):
    return {path.relative_to(root).as_posix(): {"bytes":path.stat().st_size, "sha256":sha(path)}
            for path in sorted(root.rglob("*")) if path.is_file()}


def run(reference="HEAD"):
    commit = subprocess.check_output(["git", "rev-parse", "--verify", reference + "^{commit}"],
                                     cwd=ROOT, text=True).strip()
    command = ["git", "archive", "--format=tar", commit, "--", *EXPORT_PATHS]
    author_blob = subprocess.check_output(["git", "show", commit + ":Scripts/AuthorContent.py"], cwd=ROOT)
    implementation = {name: {"bytes":(ROOT / name).stat().st_size, "sha256":sha(ROOT / name)}
                      for name in ("Scripts/TestFreshCheckout.py", "Scripts/SourceDigests.py",
                                   "ContentSource/ValidateSources.py")}
    spec = importlib.util.spec_from_file_location("ss_fresh_source_validation", ROOT / "ContentSource/ValidateSources.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    with tempfile.TemporaryDirectory(prefix="SpaceSurvival-GitSource-") as temporary:
        task_root = Path(temporary).resolve()
        archive_path = task_root / "source.tar"
        export_root = task_root / "export"
        export_root.mkdir()
        assert archive_path.resolve().is_relative_to(task_root)
        assert export_root.resolve().is_relative_to(task_root)
        with archive_path.open("wb") as output:
            subprocess.run(command, cwd=ROOT, stdout=output, check=True)
        archive_hash = sha(archive_path)
        with tarfile.open(archive_path, "r:") as archive:
            for member in archive:
                relative = PurePosixPath(member.name)
                assert not relative.is_absolute() and ".." not in relative.parts and "\\" not in member.name
                assert member.isdir() or member.isfile(), "Links and special files are not exported for source QA"
                target = (export_root / member.name).resolve()
                assert target.is_relative_to(export_root)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output)
        before = snapshot(export_root)
        assert before and "ContentSource/Meshes/SM_AcornShip.obj" in before
        # The LF bytes must come from Git, not an in-memory normalization of a
        # working-tree file. This asset is explicitly eol=lf in .gitattributes.
        first_mesh = (export_root / "ContentSource/Meshes/SM_AcornShip.obj").read_bytes()
        assert b"\n" in first_mesh and b"\r" not in first_mesh, "Expected real canonical Git text"
        required_candidates = require_registered_candidates(author_blob.decode("utf-8"), export_root)
        result = validator.validate(export_root / "ContentSource", output_path=None)
        assert before == snapshot(export_root), "Read-only validation modified the Git-exported source data"
        recorded = {
            "status":"FRESH_GIT_EXPORTED_SOURCE_FORMATS_AND_REVIEWED_REFERENCES_PASS_NOT_UNREAL",
            "recorded_utc":datetime.now(timezone.utc).isoformat(),
            "source_commit":commit, "archive_command":command, "archive_sha256":archive_hash,
            "archive_bytes":archive_path.stat().st_size, "exported_files":len(before),
            "exported_bytes":sum(item["bytes"] for item in before.values()),
            "source_manifest_sha256":hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "implementation_files":implementation,
            "committed_author_pipeline_sha256":hashlib.sha256(author_blob).hexdigest(),
            "required_candidate_reports":required_candidates,
            "first_git_mesh":before["ContentSource/Meshes/SM_AcornShip.obj"],
            "first_git_mesh_has_lf_and_no_cr":True,
            "mesh_count":len(result["meshes"]), "audio_count":len(result["audio"]),
            "preserved_hero_sha256":result["preserved_hero_sha256"],
            "reviewed_source_references":result["reviewed_source_references"],
            "all_exported_bytes_unchanged":True,
            "limits":[
                "Current validator/helper implementation is identified independently of the exported asset commit.",
                "This runs portable source format/reference checks; it does not run Unreal authoring, metadata, geometry, shader, native rendering or gameplay tests.",
                "No source regeneration, working-tree asset normalization or historical receipt rewrite.",
            ],
        }
        # The only recursive cleanup is TemporaryDirectory's own newly created
        # root; extracted links were rejected and all target paths checked.
        assert task_root.name.startswith("SpaceSurvival-GitSource-")
    return recorded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    record = run(options.ref)
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("FRESH_GIT_SOURCE_PASS", json.dumps({key:record[key] for key in
          ("source_commit", "exported_files", "mesh_count", "audio_count", "all_exported_bytes_unchanged")}))
