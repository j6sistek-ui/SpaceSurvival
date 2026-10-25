"""Build a bounded v5 comparison from explicit, matching native evidence.

Default output is a separate pending report. --publish additionally requires
lead acceptance, matching owner adoption and a fresh owner smoke check, then
archives the previous report.
This tool does not launch Unreal, edit images, or author visual acceptance.
"""
from datetime import datetime, timezone
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import struct
from urllib.parse import unquote

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
STAGE = WORK / "CryoStage"
PREFIX = "Content/SpaceSurvival/CryoComparison/"
MIB = 1024 * 1024
ANGLES = dict(front="Front", front_left="Front left", left="Left", back_left="Back left",
              back="Rear", back_right="Back right", right="Right", front_right="Front right", top="Top",
              console_detail="Console close-up", status_detail="Status close-up", glass_detail="Glass close-up")
EXTRA_CONSOLES = dict(console_other_detail="Other console close-up", console_rear_detail="Rear console close-up")
FREEZE = dict(jet_start="Jets start", full_frost="Full frost", hold="Cold hold", restored="Restored",
              frozen_left="Frozen left", frozen_back="Frozen rear", frozen_right="Frozen right")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * MIB), b""):
            digest.update(block)
    return digest.hexdigest()


def normal(mapping):
    return {key.replace("\\", "/"): value for key, value in mapping.items()}


def local(path):
    return Path(path).resolve().relative_to(OUT.resolve()).as_posix()


def evidence(path):
    if path is None:
        return None
    path = Path(path).resolve()
    digest = sha(path)
    destination = OUT / "evidence" / (path.stem + "_" + digest[:12] + ".json")
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == path.read_bytes(), "Evidence collision"
    else:
        shutil.copyfile(path, destination)
    return {"file": local(destination), "sha256": digest}


def bc_bytes(width, height, block_bytes):
    total = 0
    while True:
        total += max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block_bytes
        if width == height == 1:
            return total
        width, height = max(1, width // 2), max(1, height // 2)


def package(asset):
    return STAGE / ("Content/" + asset.split(".")[0][len("/Game/"):] + ".uasset")


def static_costs(manifest, baseline, applied):
    prior = {row["id"]: row for row in baseline["models"]}
    shared = []
    for role in ("frost", "mist"):
        row = baseline["common"]["shared_images"][role]
        assert sha(manifest["shared"][role]) == row["sha256"], "Shared source changed"
        width, height = row["estimate_build_dimensions"]
        amount = bc_bytes(width, height, 16)
        assert amount == row["estimated_standard_bc_full_mips"]["bytes"]
        shared.append({"role": role, "build_dimensions": [width, height], "BC_format": "BC3",
                       "full_mip_bytes": amount, "source_sha256": row["sha256"]})
    native = normal(applied["native_after_hashes"]) if applied else {}
    models = []
    for model in manifest["models"]:
        old = prior[model["id"]]
        assert model["source_sha256"] == old["original"]["sha256"] == sha(model["source"])
        for row in old["pbr_source_images"].values():
            assert sha(row["path"]) == row["sha256"], "Original body texture changed"
        paths = {Path(row["path"]).resolve() for row in old["native_uncooked"]["meshes"]["files"]}
        if applied:
            for row in applied["changes"]:
                if row["model_id"] != model["id"]:
                    continue
                if not row["new_actor"]:
                    previous = package(row["previous_mesh"]).resolve()
                    assert previous in paths, "V5 replacement is absent from prior active mesh list"
                    paths.remove(previous)
                paths.add(package(row["asset"]).resolve())
            assert len(paths) == len(model["components"]) == 21
            paths.update(Path(row["path"]).resolve() for row in old["native_uncooked"]["body_textures"]["files"])
            # Body material name comes from the recorded prior ownership list.
            paths.update(Path(row["path"]).resolve() for row in old["native_uncooked"]["model_owned_total"]["files"]
                         if "/Materials/" in row["path"].replace("\\", "/"))
            assert all(native[p.relative_to(STAGE.resolve()).as_posix()] == sha(p) for p in paths)
        models.append({"id": model["id"], "label": model["label"],
                       "triangles": sum(row["triangles"] for row in model["components"]),
                       "components": len(model["components"]),
                       "added_triangles_from_v4_4": sum(row["triangles"] for row in model["components"]) - old["finished_geometry"]["triangles"],
                       "body_texture_bytes_estimate": old["estimated_body_texture_gpu_full_mips"]["bytes"],
                       "original_download_bytes": old["original"]["glb_file_bytes"],
                       "model_native_bytes": sum(p.stat().st_size for p in paths) if applied else None,
                       "source_sha256": model["source_sha256"],
                       "finished_glb": local(model["finished_glb"]), "editable_blend": local(model["editable_blend"])})
    stored = [STAGE / key for key in native if key.startswith(PREFIX)]
    return {"status": "STATIC_ESTIMATES_NOT_RUNTIME_BENCHMARK", "models": models,
            "active_shared_textures": shared, "shared_texture_bytes_estimate_once": sum(x["full_mip_bytes"] for x in shared),
            "all_body_plus_shared_bytes_estimate": sum(x["body_texture_bytes_estimate"] for x in models) + sum(x["full_mip_bytes"] for x in shared),
            "namespace_stored_files": len(stored) if applied else None,
            "namespace_stored_bytes": sum(p.stat().st_size for p in stored) if applied else None,
            "limits": ["Standard full-mip BC estimates are not measured VRAM or streaming residency.",
                       "Previous status/console/hologram image packages remain recovery; active v5 UI is geometry.",
                       "Mesh buffers, shaders, fog grids, particle buffers, render targets and driver allocation are excluded.",
                       "Per-pixel translucent specular adds view-dependent work; fewer UI texture bytes do not establish faster rendering.",
                       "Static components/sections are not measured draw calls. Native package bytes are uncooked storage, not load time."]}


def captures(path, kind, manifest_hash, native):
    if path is None:
        return {"verified": False, "count": 0, "shots": {}, "evidence": None}
    data = read(path)
    wanted = "NATIVE_DISPLAY_V5_CAPTURED_PENDING_VISUAL_REVIEW" if kind == "angles" else "FOUR_NATIVE_FREEZE_CYCLES_VERIFIED_PENDING_VISUAL_REVIEW"
    assert data["status"] == wanted and not data["errors"]
    assert data["fit_manifest_sha256"] == manifest_hash
    assert normal(data["protected_native_hashes"]) == native
    assert data["native_hashes_unchanged"] and data["original_source_hashes_unchanged"]
    assert data["capture_kind"] == "ORDINARY_VIEWPORT_WITH_TSR_HISTORY" and data["actual_viewport_size"] == [960, 1200]
    if kind == "angles":
        assert data["native_cvar_restoration_verified"] and data["analysis"]["four_niagara_active_with_nontrivial_bounds"]
        expected = {(bay, view) for bay in "ABCD" for view in ANGLES}
        expected.update((bay, "console_other_detail") for bay in "ABCD")
        expected.add(("D", "console_rear_detail"))
    else:
        assert data["cvar_restored"] and {c["bay"] for c in data["cycles"]} == set("ABCD")
        expected = {(bay, view) for bay in "ABCD" for view in list(FREEZE)[:4]} | {("C", view) for view in list(FREEZE)[4:]}
    shots = {}
    for row in data["screenshots"]:
        key = (row["bay"], row["angle" if kind == "angles" else "state"])
        assert key in expected and key not in shots
        path_image = Path(row["png"])
        assert sha(path_image) == row["sha256"]
        header = path_image.read_bytes()[:24]
        assert header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack_from(">II", header, 16) == (960, 1200)
        shots[key] = {"file": local(path_image), "sha256": row["sha256"],
                      "label": ({**ANGLES, **EXTRA_CONSOLES} if kind == "angles" else FREEZE)[key[1]]}
    assert set(shots) == expected, "Incomplete current capture set; trials cannot certify the full comparison"
    return {"verified": True, "count": len(shots), "shots": shots, "evidence": evidence(path),
            "samples": len(data["samples"]), "analysis": data.get("analysis"), "cycles": data.get("cycles")}


def main(args):
    manifest = read(args.manifest)
    mh = sha(args.manifest)
    match = re.fullmatch(r"(v5(?:_\d+)?)_(?:vector_mesh|fitted_vector)_displays", manifest["version"])
    assert match and args.manifest.name == "assembly_displays_" + match[1] + ".json", "Manifest revision/name mismatch"
    geometry_path = args.geometry_audit or WORK / ("cryo-display-" + match[1] + "-independent-audit.json")
    geometry = read(geometry_path)
    assert geometry["status"] == "PASS_STATIC_GEOMETRY_PENDING_NATIVE_VISUAL_REVIEW"
    assert geometry["manifest_sha256"] == mh and not geometry["errors"]
    assert geometry["protected_inputs_unchanged"] and geometry["inputs_unchanged_during_audit"]
    applied = read(args.applied) if args.applied else None
    native = normal(applied["native_after_hashes"]) if applied else {}
    if applied:
        assert applied["status"] == "DISPLAY_V5_SAVED_PENDING_VISUAL_REVIEW" and not applied["errors"]
        assert applied["manifest_sha256"] == mh
        assert applied["unchanged_original_bodies"] and applied["unchanged_freeze_niagara_sequence_packages"]
        assert not applied["textures"], "Unexpected new UI texture imports"
        assert all(sha(STAGE / path) == value for path, value in native.items())
    budget = static_costs(manifest, read(args.baseline_costs), applied)
    angles, freeze = (captures(path, kind, mh, native) for path, kind in ((args.angles, "angles"), (args.interaction, "freeze")))
    visual = read(args.visual_review) if args.visual_review else {}
    accepted = bool(visual.get("accepted"))
    if accepted:
        assert angles["verified"] and freeze["verified"]
        assert visual["manifest_sha256"] == mh
        assert visual["angle_receipt_sha256"] == sha(args.angles) and visual["interaction_receipt_sha256"] == sha(args.interaction)
    adopted = read(args.adoption) if args.adoption else {}
    if adopted:
        assert adopted.get("apply") and adopted["status"].startswith("ADOPTED") and accepted
        expected = {key[len(PREFIX):]: value for key, value in native.items() if key.startswith(PREFIX)}
        copied = {row["relative_path"].replace("\\", "/"): row["sha256"] for row in adopted["files"]}
        assert expected == copied
        assert all(sha(Path(adopted["destination"]) / path) == value for path, value in copied.items())
    smoke = read(args.owner_smoke) if args.owner_smoke else {}
    if smoke:
        assert adopted and smoke["status"] == "OWNER_NATIVE_COMPATIBILITY_SMOKE_PASS" and not smoke["errors"]
        assert smoke["stage_proof_sha256"] == sha(args.interaction)
        assert smoke["verified_installed_package_count"] == len(native)
        assert smoke["verified_cryo_package_count"] == len(copied)
        protected = normal(smoke["protected_before_hashes"])
        assert all(protected[path] == digest for path, digest in native.items())
        assert smoke["protected_files_unchanged"] and smoke["fog_restored"]
        assert smoke["configured_chamber_count"] == 4 and smoke["actual_mid_reached_one"]
        assert smoke["native_jets_active_with_nontrivial_bounds"]
    pending = [label for okay, label in [(bool(applied), "Native v5 authoring"), (angles["verified"], "53 native angles/close-ups covering all nine bottom consoles"),
               (freeze["verified"], "Four freeze cycles and 19 frames"), (accepted, "Lead review of these exact captures"), (bool(adopted), "Owner adoption of v5"), (bool(smoke), "Fresh owner compatibility smoke")] if not okay]
    for model in budget["models"]:
        bay = model["id"]
        model["views"] = {"angle:"+view: value for (b,view),value in angles["shots"].items() if b==bay}
        model["views"].update({"freeze:"+view: value for (b,view),value in freeze["shots"].items() if b==bay})
        model["quality"] = visual.get("models", {}).get(bay, {}).get("quality", "Current v5 display/glass quality awaits native visual review.")
    data = {"revision": manifest["version"], "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "V5_NATIVE_REVIEWED_AND_ADOPTED" if not pending else "V5_PENDING_CURRENT_EVIDENCE", "pending": pending,
            "manifest_sha256": mh, "manifest": evidence(args.manifest), "authoring": evidence(args.applied),
            "geometry_audit": {"evidence": evidence(geometry_path), "status": geometry["status"],
                               "protected_file_count": geometry["protected_hash_count"]},
            "budget": budget, "angles": {k:v for k,v in angles.items() if k!="shots"}, "freeze": {k:v for k,v in freeze.items() if k!="shots"},
            "visual_review": {"accepted": accepted, "evidence": evidence(args.visual_review), "observations": visual.get("observations", [])},
            "adoption": {"verified": bool(adopted), "evidence": evidence(args.adoption)},
            "owner_smoke": {"verified": bool(smoke), "evidence": evidence(args.owner_smoke),
                            "reset_seconds": smoke.get("first_observed_reset_s")},
            "scope": "Same font-mesh displays behind glass, subtle glass haze and native specular; original bodies, fitted enclosures, frost, Niagara and light sequence preserved. Display values are authored presentation, not live telemetry.",
            "performance": "Packaged load time, GPU frame time, resident VRAM and physical E/X input remain unmeasured. D leads the reviewed hero detail and A has the smallest static budget. These are visual and resource comparisons, not runtime benchmarks.",
            "map": "/Game/SpaceSurvival/CryoComparison/Maps/L_CryoComparison"}
    if args.publish:
        assert not pending, "Canonical report requires current accepted and adopted evidence"
        archive = OUT / "history" / ("pre-v5-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        archive.mkdir(parents=True, exist_ok=False)
        for extension in ("html", "json", "md"):
            old = OUT / ("Cryo_Evaluation." + extension)
            if old.exists():
                shutil.copyfile(old, archive / old.name)
                assert sha(old) == sha(archive / old.name)
    render(data, "Cryo_Evaluation" if args.publish else "Cryo_Evaluation_v5")


def render(data, stem):
    models = data["budget"]["models"]
    fmt = lambda n: "Pending" if n is None else f"{n/MIB:.2f}"
    table = "".join(f'<tr><td>{m["id"]} · {escape(m["label"])}</td><td>{m["triangles"]:,}</td><td>{m["components"]}</td><td>{fmt(m["body_texture_bytes_estimate"])}</td><td>{fmt(m["model_native_bytes"])}</td></tr>' for m in models)
    cards = []
    for model in models:
        options = "".join(f'<option value="{escape(key)}">{escape(view["label"])}</option>' for key,view in model["views"].items())
        first = next(iter(model["views"].values()), None)
        picture = f'<a class="image-link" href="{escape(first["file"])}"><img src="{escape(first["file"])}" alt="{model["id"]} native Unreal capture"></a>' if first else '<div class="empty">Current Unreal captures pending</div>'
        cards.append(f'<article data-bay="{model["id"]}"><h2>{model["id"]} · {escape(model["label"])}</h2><label>View <select>{options}</select></label>{picture}<p>{escape(model["quality"])}</p></article>')
    pending = " · ".join(data["pending"]) or "Current v5 native evidence reviewed and adopted. Owner preference remains separate."
    observations = "".join('<li>'+escape(x)+'</li>' for x in data["visual_review"]["observations"])
    refs = [data["manifest"],data["geometry_audit"]["evidence"],data["authoring"],data["angles"]["evidence"],data["freeze"]["evidence"],data["visual_review"]["evidence"],data["adoption"]["evidence"],data["owner_smoke"]["evidence"]]
    refs = " · ".join(f'<a href="{escape(x["file"])}">{escape(Path(x["file"]).stem)}</a>' for x in refs if x)
    jsdata = json.dumps({m['id']:m['views'] for m in models}).replace('<','\\u003c')
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Acornaut cryo comparison · v5</title>
<style>body{{margin:0;background:#07121c;color:#e2eef5;font:16px/1.55 system-ui}}main{{max-width:1320px;margin:auto;padding:30px}}h1{{font-size:34px}}h2{{font-size:21px}}.notice,article,table{{background:#102330;border:1px solid #244454;border-radius:10px}}.notice{{padding:16px;color:#a9e9f4}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}}article{{padding:18px}}img{{display:block;width:100%;height:auto;margin-top:16px}}select{{background:#081a28;color:#d9f7ff;padding:8px;border:1px solid #487180;max-width:100%}}a{{color:#76ddf2}}table{{width:100%;border-collapse:collapse;margin:25px 0}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #244454}}.empty{{padding:100px 10px;text-align:center;color:#a4b7c4}}.small{{font-size:13px;overflow-wrap:anywhere;color:#afc1cd}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}main{{padding:15px}}table{{font-size:12px}}th,td{{padding:5px}}}}</style>
<main><h1>Acornaut cryo chambers · v5</h1><p>{escape(data['scope'])}</p><p class="notice">{escape(pending)}</p><p>Each dropdown opens actual Unreal views of that chamber. Click an image for its original full-size PNG.</p><div class="grid">{''.join(cards)}</div>
<h2>Quality observations</h2><ul>{observations or '<li>Current lead visual review pending.</li>'}</ul><h2>Runtime load risk</h2><table><thead><tr><th>Candidate</th><th>Triangles</th><th>Components</th><th>Body texture estimate MiB</th><th>Model native MiB</th></tr></thead><tbody>{table}</tbody></table>
<p>Active shared frost/mist full-mip estimate: <b>{fmt(data['budget']['shared_texture_bytes_estimate_once'])} MiB once</b>. All four bodies plus these shared maps: {fmt(data['budget']['all_body_plus_shared_bytes_estimate'])} MiB. Prior raster display assets stay stored as recovery.</p><ul>{''.join('<li>'+escape(x)+'</li>' for x in data['budget']['limits'])}</ul><p>{escape(data['performance'])}</p><h2>Open in Unreal</h2><p>{escape(data['map'])}</p><p>Approach a chamber and use E/controller X for the native four-second freeze. All four remain separate comparison candidates; production placement and cooking are separate.</p><details><summary>Exact evidence</summary><p class="small">Manifest SHA-256: {data['manifest_sha256']}</p><p class="small">{refs}</p></details></main>
<script>const views={jsdata};document.querySelectorAll('article').forEach(card=>{{card.querySelector('select').addEventListener('change',event=>{{const view=views[card.dataset.bay][event.target.value];if(!view)return;card.querySelector('img').src=view.file;card.querySelector('img').alt=card.dataset.bay+' — '+view.label;card.querySelector('.image-link').href=view.file;}});}});</script></html>'''
    md = ['# Acornaut cryo comparison — v5', '', data['status'], '', data['scope'], '', pending, '', '| Candidate | Triangles | Components | Body texture estimate MiB | Model native MiB |', '|---|---:|---:|---:|---:|']
    md += [f'| {m["id"]} {m["label"]} | {m["triangles"]:,} | {m["components"]} | {fmt(m["body_texture_bytes_estimate"])} | {fmt(m["model_native_bytes"])} |' for m in models]
    md += ['', 'Shared frost/mist estimate once: '+fmt(data['budget']['shared_texture_bytes_estimate_once'])+' MiB.', '', data['performance'], '', 'Visual observations:'] + ['- '+x for x in data['visual_review']['observations']]
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.refs=set()
        def handle_starttag(self, tag, attrs):
            self.refs.update(value for key,value in attrs if key in ('src','href') and value)
    links=Links();links.feed(html)
    links.refs.update(v['file'] for m in models for v in m['views'].values())
    assert all((OUT/unquote(ref)).is_file() for ref in links.refs), 'Missing report evidence/image'
    for extension, content in [('html',html),('json',json.dumps(data,indent=2)),('md','\n'.join(md))]:
        (OUT/(stem+'.'+extension)).write_text(content+'\n',encoding='utf-8')
    print(json.dumps({'report':str(OUT/(stem+'.html')),'status':data['status'],'links':len(links.refs),
                      'angles':data['angles']['count'],'freeze':data['freeze']['count'],'pending':data['pending']},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=OUT/'assembly_displays_v5_4.json')
    parser.add_argument('--geometry-audit',type=Path,help='Defaults to the independent audit for the explicit manifest revision')
    parser.add_argument('--baseline-costs',type=Path,default=WORK/'cryo-costs-v4_4.json')
    parser.add_argument('--applied',type=Path)
    parser.add_argument('--angles',type=Path)
    parser.add_argument('--interaction',type=Path)
    parser.add_argument('--visual-review',type=Path)
    parser.add_argument('--adoption',type=Path)
    parser.add_argument('--owner-smoke',type=Path)
    parser.add_argument('--publish',action='store_true')
    main(parser.parse_args())
