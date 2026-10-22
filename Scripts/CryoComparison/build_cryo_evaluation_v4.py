"""Build the fitted cryo comparison without inheriting earlier acceptance.

All receipt paths are explicit. Omitted captures/review/adoption remain pending.
No native assets, pixels, owner files, or previous reports are edited. Use
--output-stem Cryo_Evaluation only when the lead is ready to publish this revision.
"""
from datetime import datetime, timezone
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import struct

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
ANGLES = [("front", "Front"), ("front_left", "Front left"), ("left", "Left"),
          ("back_left", "Back left"), ("back", "Back"), ("back_right", "Back right"),
          ("right", "Right"), ("front_right", "Front right"), ("top", "Top")]
STATES = [("jet_start", "Jets start"), ("full_frost", "Full frost"),
          ("hold", "Cold hold"), ("restored", "Restored")]
C_FROZEN_SIDES = [("frozen_left", "Frozen · left"), ("frozen_back", "Frozen · back"),
                  ("frozen_right", "Frozen · right")]
NOTES = {
    "A": {"choice": "Lowest static budget", "quality": "Clear central character and tail silhouette in the earlier body review. The original armor and enclosure have softer detail than D.",
          "budget": "Lowest finished geometry count. Its three 4K body maps share the lower texture tier with C."},
    "B": {"choice": "Middle geometry budget", "quality": "Broad front window and centered character. Earlier native images showed soft fur and suit detail despite the 8K color map.",
          "budget": "Less geometry than C or D, but the 8K color map puts its body textures in the same budget tier as D."},
    "C": {"choice": "Four-sided enclosure", "quality": "Four fitted glass sectors enclose the previously open posts, supporting views around the chamber. The preserved front rib still divides the hero reveal.",
          "budget": "Four glass/frost sectors and their supporting rails bring finished geometry close to D. Its three 4K maps retain the lower texture budget; more overlapping transparent surfaces can add view-dependent work."},
    "D": {"choice": "Hero-detail candidate", "quality": "The earlier native body review showed the strongest fur, tail and armor separation. Current multi-angle captures are the fit check for this revision.",
          "budget": "Highest finished geometry count and the larger body-texture tier. This is a relative budget, not evidence of an FPS problem."},
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def relative(path):
    return Path(path).resolve().relative_to(OUT.resolve()).as_posix()


def preserve_receipt(path):
    """Copy immutable evidence into the handoff, with a hash in its filename."""
    if path is None:
        return None, None
    path = Path(path).resolve()
    digest = sha(path)
    dest = OUT / "evidence" / (path.stem + "_" + digest[:12] + ".json")
    dest.parent.mkdir(exist_ok=True)
    content = path.read_bytes()
    if dest.exists():
        assert dest.read_bytes() == content, "Evidence filename collision"
    else:
        dest.write_bytes(content)
    return relative(dest), digest


def captures(path, kind, manifest_hash):
    if path is None:
        return {"provided": False, "verified": False, "status": "PENDING", "shots": {}}, None
    raw = read(path)
    expected = ("NATIVE_FIT_V4_36_ANGLES_AND_RUNTIME_VERIFIED_PENDING_VISUAL_REVIEW" if kind == "angles"
                else "FOUR_NATIVE_FREEZE_CYCLES_VERIFIED_PENDING_VISUAL_REVIEW")
    assert raw.get("status") == expected, f"{kind} receipt is not a completed successful run"
    assert not raw.get("errors"), f"{kind} receipt reports errors"
    assert raw.get("native_hashes_unchanged") and raw.get("original_source_hashes_unchanged")
    if kind == "angles":
        assert raw.get("fit_manifest_sha256") == manifest_hash, "Angle captures use another assembly revision"
        assert raw.get("native_cvar_restoration_verified")
        assert raw.get("analysis", {}).get("four_niagara_active_with_nontrivial_bounds")
    else:
        assert len(raw.get("cycles", [])) == 4 and raw.get("cvar_restored")
    shots = {}
    expected_names = {(bay, name) for bay in "ABCD" for name, _ in (ANGLES if kind == "angles" else STATES)}
    if kind != "angles":
        expected_names.update(("C", name) for name, _ in C_FROZEN_SIDES)
    for row in raw["screenshots"]:
        key = (row["bay"], row["angle" if kind == "angles" else "state"])
        assert key in expected_names and key not in shots, f"Unexpected or duplicate capture {key}"
        png = Path(row["png"]).resolve()
        assert sha(png) == row["sha256"], f"Capture hash mismatch: {png}"
        with png.open("rb") as handle:
            header = handle.read(24)
        assert header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack_from(">II", header, 16) == (960, 1200)
        shots[key] = {"image": relative(png), "sha256": row["sha256"],
                      "label": dict(ANGLES if kind == "angles" else STATES + C_FROZEN_SIDES)[key[1]], "kind": kind,
                      "time_s": row.get("request_world_elapsed", row.get("at_elapsed_s")),
                      "freeze": row.get("actual_freeze_at_request"),
                      "native_sequence_seconds": row.get("native_sequence_seconds_at_request")}
    assert set(shots) == expected_names, f"Incomplete {kind} screenshot coverage"
    link, digest = preserve_receipt(path)
    return {"provided": True, "verified": True, "status": raw["status"], "run": Path(path).stem,
            "receipt": link, "receipt_sha256": digest, "count": len(shots), "shots": shots,
            "limits": raw.get("limits", []), "analysis": raw.get("analysis"),
            "cycles": raw.get("cycles", [])}, raw


def checked_adoption(path, native_hashes):
    if path is None:
        return {"status": "PENDING_CURRENT_REVISION_ADOPTION", "verified": False}
    receipt = read(path)
    assert receipt.get("apply") is True and str(receipt.get("status", "")).startswith("ADOPTED")
    assert native_hashes, "Current native proof is required before confirming installed files"
    prefix = "Content/SpaceSurvival/CryoComparison/"
    expected = {key.replace("\\", "/")[len(prefix):]: value
                for key, value in native_hashes.items() if key.replace("\\", "/").startswith(prefix)}
    copied = {row["relative_path"].replace("\\", "/"): row["sha256"] for row in receipt["files"]}
    assert expected == copied, "Adoption differs from this revision's tested namespace"
    destination = Path(receipt["destination"])
    assert all(sha(destination / key) == value for key, value in copied.items()), "Installed file hash mismatch"
    link, digest = preserve_receipt(path)
    return {"status": receipt["status"], "verified": True, "receipt": link, "receipt_sha256": digest,
            "files": len(copied), "bytes": sum((destination / key).stat().st_size for key in copied),
            "destination": str(destination), "owner_project_launched": receipt.get("owner_loaded_in_editor", False),
            "note": "Hash-verified review content installation; not production-map integration or packaged validation."}


def main(args):
    manifest = read(args.manifest)
    manifest_hash = sha(args.manifest)
    revision_label = {"v4_2_fitted_enclosures":"v4_2", "v4_3_C_tail_clearance":"v4_3",
                      "v4_4_D_rear_console":"v4_4"}[manifest["version"]]
    costs = read(args.costs) if args.costs.is_file() else None
    if costs:
        assert Path(costs["inputs"]["manifest"]).resolve() == args.manifest.resolve(), "Costs use another manifest"
        assert costs["read_only_validation"]["source_glb_hashes_match_baseline"]
        cost_models={row["id"]:row for row in costs["models"]}
        for assembly in manifest["models"]:
            cost=cost_models[assembly["id"]]
            assert cost["original"]["sha256"] == assembly["source_sha256"] == sha(assembly["source"])
            components={row["name"]:row for row in cost["finished_geometry"]["components"]}
            assert set(components)=={row["name"] for row in assembly["components"]}
            for component in assembly["components"]:
                measured=components[component["name"]]
                assert measured["triangles"]==component["triangles"] and measured["sha256"]==sha(component["file"]), "Static metrics do not match current geometry"
    angle_proof, angle_raw = captures(args.angles, "angles", manifest_hash)
    freeze_proof, freeze_raw = captures(args.interaction, "freeze", manifest_hash)
    if angle_raw and freeze_raw:
        assert angle_raw["protected_native_hashes"] == freeze_raw["protected_native_hashes"], "Capture runs use different native packages"
    if freeze_raw and not angle_raw:
        raise AssertionError("Provide matching angles receipt to bind interaction proof to the fitted manifest")
    visual = read(args.visual_review) if args.visual_review else {}
    reviewed = bool(visual.get("accepted") is True)
    if reviewed:
        assert visual.get("fit_manifest_sha256") == manifest_hash
        assert visual.get("angle_receipt_sha256") == angle_proof.get("receipt_sha256")
        assert visual.get("interaction_receipt_sha256") == freeze_proof.get("receipt_sha256")
        assert angle_proof["verified"] and freeze_proof["verified"]
    visual_link, visual_hash = preserve_receipt(args.visual_review)
    adoption = checked_adoption(args.adoption, (angle_raw or {}).get("protected_native_hashes"))
    pending = []
    for good, message in [(costs is not None, "Current static native package budget"),
                          (angle_proof["verified"], "36 native views for fitted " + revision_label),
                          (freeze_proof["verified"], "Four native freeze cycles and 19 captures, including C's frozen side windows"),
                          (reviewed, "Lead visual review of these exact capture runs"),
                          (adoption["verified"], "Hash-verified adoption of this revision in the owner project")]:
        if not good:
            pending.append(message)
    shared = costs["common"]["estimated_shared_texture_gpu_full_mips"]["MiB"] if costs else None
    rows = {row["id"]: row for row in costs["models"]} if costs else {}
    models = []
    for assembly in manifest["models"]:
        bay = assembly["id"];cost = rows.get(bay);notes = dict(NOTES[bay])
        if reviewed and bay in visual.get("models", {}):
            notes.update({key: value for key, value in visual["models"][bay].items() if key in notes})
        shots = {"angle:" + name: angle_proof["shots"][(bay, name)] for name, _ in ANGLES if (bay, name) in angle_proof["shots"]}
        shots.update({"freeze:" + name: freeze_proof["shots"][(bay, name)] for name, _ in STATES + C_FROZEN_SIDES if (bay, name) in freeze_proof["shots"]})
        models.append({"id": bay, "label": assembly["label"], **notes, "views": shots,
            "triangles": sum(row["triangles"] for row in assembly["components"]),
            "components": len(assembly["components"]), "glass_sectors": assembly["fit_v4"]["panes"],
            "body_texture_MiB": cost["estimated_body_texture_gpu_full_mips"]["MiB"] if cost else None,
            "body_plus_shared_texture_MiB": round(cost["estimated_body_texture_gpu_full_mips"]["MiB"] + shared, 6) if cost else None,
            "active_model_native_MiB": cost["native_uncooked"]["model_owned_total"]["MiB"] if cost else None,
            "native_material_sections": cost["finished_geometry"]["native_lod0_material_sections"] if cost else None,
            "original_glb_MiB": cost["original"]["glb_file_MiB"] if cost else None,
            "finished_glb": relative(assembly["finished_glb"]), "editable_blend": relative(assembly["editable_blend"]),
            "source_sha256": assembly["source_sha256"]})
    fit_path = args.fit_audit or WORK / ("cryo-fit-audit-" + revision_label + "-contact.json")
    fit = read(fit_path) if fit_path.is_file() else None
    if fit:
        assert fit.get("manifest_sha256") == manifest_hash, "Fit audit uses another assembly revision"
    fit_link, _ = preserve_receipt(fit_path if fit else None)
    costs_link, _ = preserve_receipt(args.costs if costs else None)
    manifest_link, _ = preserve_receipt(args.manifest)
    prompts_path = OUT / "shared/image-prompts.json"
    tail_path = OUT / "fit-v4_3-tail-clearance.json"
    tail = read(tail_path) if revision_label in ("v4_3", "v4_4") else None
    if tail:
        tail_manifest=read(tail["manifest"])
        assert tail["manifest_sha256"] == sha(tail["manifest"]) and tail["pane_perimeter_unchanged"]
        assert next(m for m in tail_manifest["models"] if m["id"]=="C") == next(m for m in manifest["models"] if m["id"]=="C"), "Tail evidence no longer describes current C"
        assert tail["all_four_source_GLBS_and_v4_2_files_unchanged"]
        assert tail["after"]["minimum_euclidean_clearance_mm"] >= 5
    tail_link, _ = preserve_receipt(tail_path if tail else None)
    tail_reload_path = WORK / "cryo-C-rear-intersection-v4_3.json"
    tail_reload = read(tail_reload_path) if tail and tail_reload_path.is_file() else None
    if tail_reload:
        assert tail_reload["manifest_sha256"] == tail["manifest_sha256"] and tail_reload["protected_files_unchanged"]
        assert tail_reload["blob_region"] is None
        assert tail_reload["fresh_loaded_tail_clearance"]["minimum_euclidean_clearance_mm"] >= 5
    tail_reload_link, _ = preserve_receipt(tail_reload_path if tail_reload else None)
    rear_path=OUT/"fit-v4_4-rear-console.json"
    rear=read(rear_path) if revision_label=="v4_4" else None
    if rear:
        assert rear["manifest_sha256"]==manifest_hash and rear["protected_inputs_unchanged"]
    rear_link,_=preserve_receipt(rear_path if rear else None)
    data = {"title": "Acornaut cryo chambers · fitted " + revision_label, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FINISH_RUNTIME_VISUAL_AND_STATIC_ASSESSMENT_VERIFIED" if not pending else "CURRENT_REVISION_PENDING_EVIDENCE",
        "revision": manifest["version"], "revision_label": revision_label, "manifest": manifest_link, "manifest_sha256": manifest_hash,
        "models": models, "pending": pending,
        "static_assessment": {"status": "COMPLETE_STATIC_BUDGET_ASSESSMENT" if costs else "PENDING_CURRENT_NATIVE_BYTES",
            "costs_receipt": costs_link, "shared_texture_MiB_once": shared,
            "all_four_body_plus_shared_texture_MiB": costs["totals"]["estimated_body_plus_shared_texture_gpu_full_mips_MiB"] if costs else None,
            "method": "Standard full-mip BC1 opaque color/ORM, BC3 transparent artwork and BC5 normals; estimates, not measured GPU allocation.",
            "effect_textures": "Freeze and nozzle effects reuse the shared frost/mist maps; no additional authored texture maps.",
            "native_storage": costs.get("totals") if costs else None, "recovery": costs.get("stored_recovery") if costs else None},
        "recommendation": {"hero_detail_candidate": "D", "smallest_static_budget": "A", "four_sided_display": "C",
            "status": "CURRENT_CAPTURE_REVIEWED" if reviewed else "BODY_REVIEW_CARRIED_FORWARD_CURRENT_FIT_REVIEW_PENDING",
            "reason": "D retains the most detailed hero body; A has the smallest static budget. C adds an enclosed 360° presentation, while its preserved front rib still obstructs part of the central reveal."},
        "finish": {"components_each": 19, "console_glass_offset_mm": 8, "console_HUD_offset_mm": 10,
            "bottom_console_faces":9 if rear else 8, "D_rear_service_console_receipt":rear_link,
            "holo_glass_offset_mm": 2.5, "C_window_sectors": 4, "glass_seat": "Closed 4mm rails fitted to post/cap regions",
            "freeze_cycle": "Native interaction starts two downward nozzle jets, freezes all window sectors and restores the normal view after four seconds.",
            "freeze_cycle_status": "VERIFIED_NATIVE_ACTION" if freeze_proof["verified"] else "AUTHORED_RUNTIME_VERIFICATION_PENDING",
            "visual_telemetry": "Display artwork and shader animation are authored visuals; live game telemetry is not implemented."},
        "angle_proof": {key: value for key, value in angle_proof.items() if key != "shots"},
        "freeze_proof": {key: value for key, value in freeze_proof.items() if key != "shots"},
        "visual_review": {"accepted": reviewed, "receipt": visual_link, "receipt_sha256": visual_hash,
            "observations": visual.get("observations", []), "owner_acceptance": "NOT_CLAIMED"},
        "native_adoption": adoption,
        "C_rear_tail_clearance": {"receipt": tail_link,
            "fresh_reload_receipt": tail_reload_link,
            "maximum_local_glass_lift_mm": tail["maximum_lift_mm"] if tail else None,
            "minimum_sampled_clearance_mm": tail["after"]["minimum_euclidean_clearance_mm"] if tail else None,
            "sampling_limit": tail["sampling_limit"] if tail else None,
            "body_and_perimeter_preserved": bool(tail)},
        "fit_audit": {"receipt": fit_link, "status": fit.get("status") if fit else "PENDING",
            "unresolved_checks": fit.get("failures", []) if fit else [],
            "note": (("The numerical audit retains local seating-span flags at irregular source recesses. Reviewed illuminated side/oblique views show no clearly floating added panes or consoles; dark native top views do not establish every fine contact. The linked audit preserves the flagged distances." if reviewed else "The numerical audit still flags local seat-to-body clearance at irregular source recesses. Native top/oblique review determines whether these supported rail spans show a visible gap; the linked audit retains the unresolved checks and raw distances.")
                     if fit and fit.get("failures") else "Numerical fit checks passed; visual acceptance is recorded separately for the current native views." if fit else "Numerical fit evidence is pending.")},
        "open_in_unreal": {"project": "C:/Users/j6sis/SpaceSurvival/SpaceSurvival.uproject",
            "map": "/Game/SpaceSurvival/CryoComparison/Maps/L_CryoComparison",
            "instruction": ("Open the comparison map in SpaceSurvival and press Play. " if adoption["verified"] else "After current adoption is verified, open the comparison map in SpaceSurvival and press Play. ") + "Approach a chamber and press E (or controller X) to start its four-second freeze cycle.",
            "scope": "Review map only; production-map placement and cooking remain separate."},
        "risk_explanation": ["One chamber has 19 static mesh sections. Combining them under one actor does not remove geometry or material work.",
            "Texture memory depends on pixel count and format. An 8K color image has four times the pixels of a 4K image.",
            "Overlapping glass, frost, holograms and particles add view-dependent transparency work. C has four window sectors.",
            "Niagara, volumetric fog and animated lights add per-frame work. Effects reuse shared textures, but their rendering cost is not zero.",
            "All four stored downloads do not mean all four are resident. This review map loads all four; a game can load only the selected chamber.",
            "One detailed hero chamber is not automatically a performance problem. These relative budgets do not prove an FPS failure."],
        "performance_limits": "Packaged FPS, GPU frame time, actual resident VRAM and representative production-scene load time are unmeasured future profiling; the static assessment does not require an FPS-failure claim.",
        "measured_fps": None, "measured_gpu_time_ms": None, "measured_resident_vram_MiB": None,
        "provenance": {"generated_images": len(read(prompts_path)), "image_prompts": relative(prompts_path),
            "pixels_modified_by_report_builder": False, "engine_launched_by_report_builder": False}}
    render(data, args.output_stem)


def render(data, stem):
    def number(value, precision=2):
        return "Pending" if value is None else f"{value:,.{precision}f}"
    def options(model=None):
        groups=[]
        for prefix, label, entries in [("angle", "Native angles", ANGLES), ("freeze", "Freeze cycle", STATES)]:
            if prefix == "freeze" and model is not None and model["id"] == "C":
                entries = entries + C_FROZEN_SIDES
            items=[]
            for key, title in entries:
                value=prefix+":"+key
                enabled=model is None or value in model["views"]
                items.append(f'<option value="{value}" {"disabled" if not enabled else ""}>{title}{" · pending" if not enabled else ""}</option>')
            groups.append(f'<optgroup label="{label}">{"".join(items)}</optgroup>')
        return "".join(groups)
    cards=[]
    for model in data["models"]:
        first=model["views"].get("angle:front")
        image=(f'<a class="image-link" href="{escape(first["image"])}" target="_blank"><img src="{escape(first["image"])}" alt="{model["id"]} front native view"></a>'
               if first else '<a class="image-link" hidden><img alt="Native view pending"></a>')
        cards.append(f'''<article class="card" data-bay="{model['id']}"><header><span class="bay">{model['id']}</span><div><h2>{escape(model['label'])}</h2><span class="muted">{escape(model['choice'])}</span></div></header>
<label class="view-label">Inspect view<select class="view-choice" aria-label="{model['id']} angle or freeze state">{options(model)}</select></label>
<div class="image-shell">{image}<div class="placeholder" {"hidden" if first else ""}>Current native captures pending</div></div><p class="caption">{"Front · native game" if first else "No earlier revision shown as current evidence."}</p>
<div class="card-copy"><strong>{model['triangles']:,} triangles · {model['glass_sectors']} glass sector{'s' if model['glass_sectors']!=1 else ''}</strong><p>{escape(model['quality'])}</p><p class="muted">{escape(model['budget'])}</p>
<p><a href="{escape(model['finished_glb'])}" download>Current fitted GLB</a> · <a href="{escape(model['editable_blend'])}" download>Editable Blender</a></p></div></article>''')
    rows="".join(f'<tr><th>{m["id"]} · {escape(m["label"])}</th><td>{m["triangles"]:,}</td><td>{m["components"]}</td><td>{number(m["body_texture_MiB"])}</td><td>{number(m["body_plus_shared_texture_MiB"])}</td><td>{number(m["active_model_native_MiB"])}</td></tr>' for m in data["models"])
    pending=("<ul>"+"".join("<li>"+escape(item)+"</li>" for item in data["pending"])+"</ul>" if data["pending"] else "<p>Current native captures, interaction, lead visual review, static budgets and installed-file hashes are verified. Your preferred chamber remains your choice.</p>")
    proof_links=" · ".join(f'<a href="{escape(row["receipt"])}">{label}</a>' for label,row in [("36-view receipt",data["angle_proof"]),("Freeze-cycle receipt",data["freeze_proof"]),("Visual review",data["visual_review"]),("Owner adoption",data["native_adoption"]),("Numerical fit audit",data["fit_audit"]),("C tail-clearance audit",data["C_rear_tail_clearance"])] if row.get("receipt"))
    payload=json.dumps(data,ensure_ascii=False).replace("<","\\u003c")
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Acornaut · Fitted cryo comparison</title><style>
:root{color-scheme:dark;--bg:#071117;--panel:#10212b;--line:#294650;--ink:#e6f4f7;--muted:#aec3ca;--cyan:#6de0ef}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}main{max-width:1680px;margin:auto;padding:36px 28px 60px}h1{font-size:clamp(28px,3.8vw,48px);line-height:1.1;margin:6px 0 18px}h2{font-size:20px;line-height:1.2;margin:0}h3{margin-top:0}a{color:var(--cyan)}p{margin:10px 0}.eyebrow{letter-spacing:.15em;color:var(--cyan);font-size:13px}.lead{max-width:1000px;font-size:19px}.muted,.caption,.notes{color:var(--muted)}.status{border:1px solid #675634;background:#26251d;border-radius:12px;padding:16px 22px;margin:24px 0}.status ul{margin:8px 0;padding-left:22px}.toolbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:24px 0 18px}select{font:inherit;background:#09171f;border:1px solid var(--line);border-radius:7px;color:var(--ink);padding:8px 12px;max-width:100%}.grid{display:grid;grid-template-columns:repeat(4,minmax(240px,1fr));gap:18px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}.card header{display:flex;gap:12px;padding:18px 16px;min-height:96px}.bay{display:grid;place-items:center;width:40px;height:40px;flex:0 0 40px;border:1px solid var(--cyan);border-radius:50%;font-weight:750;color:var(--cyan)}.card header .muted{font-size:13px}.view-label{display:flex;gap:8px;flex-direction:column;padding:0 16px 14px;font-size:13px}.image-shell{aspect-ratio:4/5;background:#02080d;display:grid;place-items:center}.image-shell a{width:100%;height:100%;display:block}.image-shell img{width:100%;height:100%;object-fit:contain;display:block}.image-shell [hidden]{display:none}.placeholder{padding:30px;text-align:center;color:var(--muted)}.caption{font-size:12px;padding:0 16px;min-height:36px}.card-copy{padding:0 16px 16px;font-size:14px}.card-copy strong{color:var(--cyan);font-size:13px}section{margin-top:32px;background:#0c1b23;border:1px solid var(--line);padding:24px;border-radius:12px}section h2{margin-bottom:14px}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{padding:12px 10px;border-bottom:1px solid var(--line);text-align:right}th:first-child{text-align:left}thead th{font-size:13px;color:var(--muted)}.table-scroll{overflow-x:auto}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:28px}.notes{font-size:14px}.path{word-break:break-word;font-family:ui-monospace,monospace}.risk-list{padding-left:21px}.risk-list li{margin:8px 0}footer{margin-top:28px;color:var(--muted);font-size:13px}[hidden]{display:none!important}@media(max-width:1250px){.grid{grid-template-columns:repeat(2,minmax(240px,1fr))}}@media(max-width:650px){main{padding:22px 14px}.grid,.two-col{grid-template-columns:1fr}section{padding:18px}th,td{padding:9px}}
</style></head><body><main>
<div class="eyebrow">ACORNAUT · SPACESURVIVAL · FITTED '''+escape(data["revision_label"].upper())+'''</div><h1>Four cryogenic chambers</h1><p class="lead">Inspect every side, compare the four-second freeze cycle, then choose the hero chamber. All four retain their original generated bodies and use the same screen art and native effect settings.</p>
<div class="status"><strong>''' + ("Current revision verified" if not data["pending"] else "Current revision: verification in progress") + '</strong>'+pending+'''</div>
<div class="toolbar"><label for="all-view">Set every chamber to</label><select id="all-view">'''+options()+'''</select><span class="muted">Each card can also be inspected independently.</span></div>
<div class="grid">'''+"".join(cards)+'''</div>
<section><h2>Static load-risk comparison</h2><p>D remains the hero-detail candidate; A has the smallest static budget. C now offers four-sided glazing, with geometry close to D and a lower texture budget. Final fit preference should follow the current views above.</p><div class="table-scroll"><table><thead><tr><th>Chamber</th><th>Triangles</th><th>Mesh sections</th><th>Body textures<br>MiB estimate</th><th>Body + shared<br>MiB estimate</th><th>Active model files<br>uncooked MiB</th></tr></thead><tbody>'''+rows+'''</tbody></table></div><p class="notes">Shared artwork: '''+number(data["static_assessment"]["shared_texture_MiB_once"])+''' MiB estimated once. BC mip-chain estimates exclude geometry buffers, Niagara buffers, fog grids, render targets and shader storage. Uncooked asset bytes are file lengths, not resident memory or cooked download sizes. Superseded meshes remain separate recovery files in the cost receipt.</p><ul class="risk-list">'''+"".join("<li>"+escape(item)+"</li>" for item in data["risk_explanation"])+'''</ul><p class="notes">'''+escape(data["performance_limits"])+'''</p></section>
<section class="two-col"><div><h2>What changed in this revision</h2><p>Glass follows the measured caps and posts. C has four joined window sectors. Closed metal seats support the glass, while the front HUD follows its actual grid at 2.5 mm.</p><p>The bottom consoles are inset inside their existing bezel: glass 8 mm above backing, transparent HUD 10 mm above it. D's additional rear service screen uses the same finish. Original body geometry is preserved.</p><p>Native interaction is authored to emit cold vapor from two top nozzles, frost the windows, then restore the normal view after four seconds. The state selector shows actual captured stages when verified.</p><p class="notes">'''+escape(data["fit_audit"]["note"])+'''</p></div><div><h2>Open the Unreal comparison</h2><p>'''+escape(data["open_in_unreal"]["instruction"])+'''</p><p class="path">Content/SpaceSurvival/CryoComparison/Maps/L_CryoComparison</p><p class="notes">Current adoption: '''+escape(data["native_adoption"]["status"])+'''</p><p class="notes">The native-action observer uses the same controller action through Python; it does not simulate physical key presses. Display labels are authored artwork, not live game telemetry.</p><p>'''+proof_links+'''</p></div></section>
<footer>Evidence belongs to this revision only. Earlier rejected fit is retained separately. <a href="'''+escape(stem)+'''.json">Evaluation JSON</a> · <a href="'''+escape(stem)+'''.md">Evaluation notes</a> · <a href="shared/image-prompts.json">Generated-image provenance</a></footer>
<script id="evaluation-data" type="application/json">'''+payload+'''</script><script>
const report=JSON.parse(document.getElementById('evaluation-data').textContent);
function selectView(card,key){const model=report.models.find(m=>m.id===card.dataset.bay),shot=model.views[key];if(!shot)return;const anchor=card.querySelector('.image-link'),img=anchor.querySelector('img');anchor.hidden=false;anchor.href=shot.image;img.src=shot.image;img.alt=model.id+' '+model.label+' · '+shot.label;card.querySelector('.placeholder')?.setAttribute('hidden','');let text=shot.label+' · native game';if(shot.kind==='freeze'&&shot.time_s!=null)text+=' · '+shot.time_s.toFixed(2)+'s after interaction';if(shot.kind==='angles'&&shot.native_sequence_seconds!=null)text+=' · light phase '+shot.native_sequence_seconds.toFixed(2)+'s';card.querySelector('.caption').textContent=text;card.querySelector('select').value=key;}
document.querySelectorAll('.card').forEach(card=>card.querySelector('select').addEventListener('change',event=>selectView(card,event.target.value)));
document.getElementById('all-view').addEventListener('change',event=>document.querySelectorAll('.card').forEach(card=>selectView(card,event.target.value)));
</script></main></body></html>'''
    observations=data["visual_review"]["observations"]
    if observations:
        review_notes='<section><h2>Visual review notes</h2><ul>'+''.join('<li>'+escape(item)+'</li>' for item in observations)+'</ul></section>'
        html=html.replace('<footer>',review_notes+'<footer>',1)
    json_path=OUT/(stem+".json");html_path=OUT/(stem+".html");md_path=OUT/(stem+".md")
    json_path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    html_path.write_text(html,encoding="utf-8")
    markdown=["# Acornaut cryo comparison — fitted "+data["revision_label"], "", "Status: "+data["status"], "",
        "D is the hero-detail candidate; A has the smallest static budget. C adds four-sided glazing while retaining its lower texture tier.", "",
        "| Model | Triangles | Body texture estimate MiB | Body + shared estimate MiB |", "|---|---:|---:|---:|"]
    markdown += [f'| {m["id"]} {m["label"]} | {m["triangles"]:,} | {number(m["body_texture_MiB"])} | {number(m["body_plus_shared_texture_MiB"])} |' for m in data["models"]]
    markdown += ["", data["performance_limits"], "", "Current evidence:"]
    markdown += ["- "+item for item in data["pending"]] or ["- Current native views, interactions, visual review and owner adoption verified."]
    markdown += ["", data["fit_audit"]["note"], "", "Visual review notes:", ""] + ["- "+item for item in observations]
    markdown += ["", data["open_in_unreal"]["instruction"], "", "Original geometry and source files remain preserved. Owner preference is separate from technical verification."]
    md_path.write_text("\n".join(markdown)+"\n",encoding="utf-8")
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ("href","src") and value and not value.startswith(("#","http:","https:","data:")):
                    self.links.append(value)
    links=Links();links.feed(html)
    referenced=set(links.links)
    referenced.update(view["image"] for model in data["models"] for view in model["views"].values())
    missing=[link for link in referenced if not (OUT/link).resolve().is_file()]
    assert not missing, "Broken report links: "+str(missing)
    print(json.dumps({"html":str(html_path),"status":data["status"],"links_checked":len(referenced),
        "angle_images":data["angle_proof"].get("count",0),"freeze_images":data["freeze_proof"].get("count",0),"pending":data["pending"]},indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,default=OUT/"assembly_fit_v4_4.json")
    parser.add_argument("--costs",type=Path,default=WORK/"cryo-costs-v4_4.json")
    parser.add_argument("--fit-audit",type=Path)
    parser.add_argument("--angles",type=Path)
    parser.add_argument("--interaction",type=Path)
    parser.add_argument("--visual-review",type=Path)
    parser.add_argument("--adoption",type=Path)
    parser.add_argument("--output-stem",default="Cryo_Evaluation_v4_4")
    args=parser.parse_args()
    assert args.output_stem.replace("_","").isalnum(), "Output stem must be a simple filename"
    main(args)
