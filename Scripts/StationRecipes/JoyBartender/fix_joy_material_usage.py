"""Give Joy's material masters the skeletal-mesh AND morph-target usage flags, recompile and save them, then re-save
their child instances so each child's stored usage follows its parent. Reports before/after for every asset touched.

Why (2026-10-15 PIE, Saved/Logs/SpaceSurvival.log lines 2789/3393/3498/3637):
  "Material .../JoyBartender/Materials/MI_Joy_Std_Skin_Body missing usage flag MorphTargets! Default Material will be
   used in game."
SK_Joy carries morph targets (the twelve ST_Breast_*/ST_Hip_* soft-tissue keys written every tick, plus the CC face,
eye-occlusion and tear-line keys). import_joy_original.py made M_JoyBOpaque / M_JoyBMasked / M_JoyBTranslucent with
used_with_skeletal_mesh only (line 129), so none of their 17 children on SK_Joy can draw a morphed section. In the editor
the flag is auto-set when the check runs outside Play-In-Editor; inside PIE it is not, and the section drew the default
(checker) material.

Run it INSIDE the open editor, and NOT while Play-In-Editor is running:
    Output Log, Python console:   py "<absolute path>/set_usage_flags.py"
or headless, only with the editor CLOSED (the open editor holds these packages):
    UnrealEditor-Cmd.exe <project> -unattended -NullRHI -stdout -FullStdOutLogOutput
        -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/fix_joy_material_usage.py"

    set SS_USAGE_DRY_RUN=1          log the before-state only; change and save nothing
    (Vendor masters are refused, as in Scripts/AuthorStationVisualPass.py. The jacket's /Game/Jacket_1 M_PBR_Base also
    lacks MorphTargets, but the fitted jacket carries no morph keys today; if it ever gets them, give Joy a private
    copy of MI_Jacket and call set_material_usage_override(..., MATUSAGE_MORPH_TARGETS, True, True) on that copy.)
    set SS_USAGE_REPORT=<file.json> also write the report there as JSON

Every log line starts with "USAGEFIX|". Adding MorphTargets to the three masters compiles one extra set of shader
permutations per master (their instances share the parent's shader map): expect a short shader-compile wait.
"""
import json
import os

import unreal as u

E = u.MaterialEditingLibrary
L = u.EditorAssetLibrary
JOY = "/Game/SpaceSurvival/Licensed/StationAssets/JoyBartender"
MATS = JOY + "/Materials"
MESH = JOY + "/Mesh/SK_Joy"
DRY = os.environ.get("SS_USAGE_DRY_RUN") == "1"

SKEL_MORPH = ("SkeletalMesh", "MorphTargets")
# master path -> the usage flags it must carry (EMaterialUsage names without the MATUSAGE_ prefix)
MASTERS = {
    MATS + "/M_JoyBOpaque": SKEL_MORPH,       # Skin_Body/Head/Arm/Leg, Nails, Upper/Lower_Teeth, Tongue, Piercing, GString, EyeOption
    MATS + "/M_JoyBMasked": SKEL_MORPH,       # Eyelash, ShortStraight_Transparency (hair); Underwear_Bottoms (no longer on SK_Joy)
    MATS + "/M_JoyBTranslucent": SKEL_MORPH,  # Eye_Occlusion_L/R, Tearline_L/R; Cornea_L/R (no longer on SK_Joy)
    MATS + "/M_Joy_SciFiPants": SKEL_MORPH,   # duplicate of the pack master: already saved with both (expected no-op)
}
assert all(p.startswith("/Game/SpaceSurvival/") for p in MASTERS), "refusing vendor material mutation"

PROPERTY = {"SkeletalMesh": "used_with_skeletal_mesh", "MorphTargets": "used_with_morph_targets"}
# EMaterialUsage bit order, UE 5.8 Engine/Source/Runtime/Engine/Public/Materials/MaterialInterface.h
USAGE_BITS = ["SkeletalMesh", "ParticleSprites", "BeamTrails", "MeshParticles", "StaticLighting", "MorphTargets",
              "SplineMesh", "InstancedStaticMeshes", "GeometryCollections", "Clothing", "NiagaraSprites",
              "NiagaraRibbons", "NiagaraMeshParticles", "GeometryCache", "Water", "HairStrands", "LidarPointCloud",
              "VirtualHeightfieldMesh", "Nanite", "Voxels", "VolumetricCloud", "HeterogeneousVolumes", "StaticMesh",
              "EditorCompositing", "NeuralNetworks", "MeshDeformer", "InstancedSkinnedMesh", "Curves"]


def log(s):
    u.log_warning("USAGEFIX| " + str(s))


def usage_enum(name):
    """unreal.MaterialUsage member for 'MorphTargets' -> MATUSAGE_MORPH_TARGETS (None if this build lacks it)."""
    enum = getattr(u, "MaterialUsage", None)
    if enum is None:
        return None
    snake = "".join(("_" + c) if (c.isupper() and i) else c for i, c in enumerate(name)).upper()
    for candidate in ("MATUSAGE_" + snake, "MATUSAGE_" + name.upper(), "MATUSAGE_" + name):
        if hasattr(enum, candidate):
            return getattr(enum, candidate)
    return None


def has_usage(material, name):
    """What the engine answers (GetUsageByFlag via HasMaterialUsage); None when this build cannot say."""
    enum = usage_enum(name)
    if enum is not None and hasattr(E, "has_material_usage"):
        return bool(E.has_material_usage(material, enum))
    return None


def master_state(mat, wanted):
    row = {}
    for n in wanted:
        try:
            prop = bool(mat.get_editor_property(PROPERTY[n]))
        except Exception as e:  # noqa: BLE001 - report, do not hide
            prop = "unreadable: %s" % e
        row[n] = {"property": prop, "has_usage": has_usage(mat, n)}
    return row


def ok(cell):
    """The engine's answer when there is one, else the stored bool."""
    return cell["has_usage"] if cell["has_usage"] is not None else cell["property"] is True


def bits(mask):
    return None if mask is None else [USAGE_BITS[i] for i in range(len(USAGE_BITS)) if mask >> i & 1]


def instance_masks(mi):
    """(stored usage mask, override mask) from BasePropertyOverrides; None where this build hides them."""
    try:
        bpo = mi.get_editor_property("base_property_overrides")
    except Exception:  # noqa: BLE001
        return None, None
    value = override = None
    for name in ("usage_flags",):
        try:
            value = int(bpo.get_editor_property(name))
        except Exception:  # noqa: BLE001
            pass
    for name in ("b_override_usage_flags", "override_usage_flags", "bOverride_UsageFlags"):
        try:
            override = int(bpo.get_editor_property(name))
            break
        except Exception:  # noqa: BLE001
            continue
    return value, override


def instance_state(mi, wanted):
    value, override = instance_masks(mi)
    return {"has_usage": {n: has_usage(mi, n) for n in wanted}, "stored_usage_flags": bits(value),
            "override_bits": bits(override)}


assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), "stop Play-In-Editor first, then run this"
log("start (dry run: %s) - %d masters" % (DRY, len(MASTERS)))
report = {"dry_run": DRY, "masters": {}, "instances": {}, "sk_joy_slots": [], "skipped": []}
changed_masters = set()

# 1. masters
for path, wanted in MASTERS.items():
    if not L.does_asset_exist(path):
        report["skipped"].append(path + " (does not exist)")
        log("SKIP (does not exist) " + path)
        continue
    mat = u.load_asset(path)
    if not isinstance(mat, u.Material):
        report["skipped"].append("%s (not a Material: %s)" % (path, type(mat).__name__))
        log("SKIP (not a Material) " + path)
        continue
    before = master_state(mat, wanted)
    missing = [n for n in wanted if not ok(before[n])]
    row = {"wanted": list(wanted), "before": before, "missing_before": missing, "route": None}
    log("%s BEFORE %s missing=%s" % (path, json.dumps(before), missing))
    if missing and not DRY:
        for n in missing:
            mat.set_editor_property(PROPERTY[n], True)  # UE 5.8 deprecates these bools for C++, they stay UPROPERTYs
        row["route"] = "set_editor_property"
        still = [n for n in wanted if not ok(master_state(mat, wanted)[n])]
        if still:
            # 5.8 reads usage through GetUsageByFlag(); its own editor setter is the fallback if the bool did not take
            assert hasattr(E, "set_base_material_usage"), ("the bool did not take and set_base_material_usage is absent", path, still)
            for n in still:
                enum = usage_enum(n)
                assert enum is not None, ("no unreal.MaterialUsage member for", n)
                E.set_base_material_usage(mat, enum, True)
            row["route"] = "set_editor_property + set_base_material_usage(%s)" % ",".join(still)
        E.recompile_material(mat)
        assert L.save_loaded_asset(mat, False), path
        changed_masters.add(mat.get_path_name())
    row["after"] = master_state(mat, wanted)
    row["missing_after"] = [n for n in wanted if not ok(row["after"][n])]
    log("%s AFTER %s missing=%s route=%s" % (path, json.dumps(row["after"]), row["missing_after"], row["route"]))
    assert DRY or not row["missing_after"], ("still missing after the fix", path, row["missing_after"])
    report["masters"][path] = row

master_objects = {u.load_asset(p).get_path_name(): MASTERS[p] for p in report["masters"]}

# 2. their instances: Joy's own folder only (the pack's instances are never edited)
for asset_path in L.list_assets(MATS, recursive=False, include_folder=False):
    mi = u.load_asset(asset_path)
    if not isinstance(mi, u.MaterialInstanceConstant):
        continue
    base = mi.get_base_material()
    base_path = base.get_path_name() if base else None
    if base_path not in master_objects:
        continue
    wanted = master_objects[base_path]
    before = instance_state(mi, wanted)
    row = {"base": base_path, "before": before, "override_cleared": [], "saved": False}
    if not DRY:
        # an instance-level override that switches a wanted usage OFF would beat the parent: hand it back to the parent
        for n in wanted:
            enum = usage_enum(n)
            if enum is not None and hasattr(E, "has_material_usage_override") and E.has_material_usage_override(mi, enum) \
                    and has_usage(mi, n) is False:
                E.set_material_usage_override(mi, enum, False, True)
                row["override_cleared"].append(n)
        if base_path in changed_masters or row["override_cleared"]:
            E.update_material_instance(mi)
            assert L.save_loaded_asset(mi, False), asset_path
            row["saved"] = True
    row["after"] = instance_state(mi, wanted)
    log("%s base=%s BEFORE %s AFTER %s saved=%s overrides_cleared=%s" % (mi.get_name(), base.get_name(), json.dumps(before),
                                                                       json.dumps(row["after"]), row["saved"], row["override_cleared"]))
    if not DRY:
        assert all(v is not False for v in row["after"]["has_usage"].values()), ("instance still lacks a usage", asset_path, row["after"])
    report["instances"][mi.get_path_name()] = row

# 3. the receipt that matters: every material on SK_Joy's slots, as the engine answers for it now
mesh = u.load_asset(MESH)
if isinstance(mesh, u.SkeletalMesh):
    for slot in mesh.materials:
        m = slot.material_interface
        base = m.get_base_material() if m else None
        cell = {"slot": str(slot.material_slot_name), "material": m.get_path_name() if m else None,
                "base": base.get_path_name() if base else None,
                "SkeletalMesh": has_usage(m, "SkeletalMesh") if m else None,
                "MorphTargets": has_usage(m, "MorphTargets") if m else None}
        report["sk_joy_slots"].append(cell)
        log("SK_Joy slot %(slot)s -> %(material)s (base %(base)s) SkeletalMesh=%(SkeletalMesh)s MorphTargets=%(MorphTargets)s" % cell)
    lacking = [c["slot"] for c in report["sk_joy_slots"] if c["MorphTargets"] is False]
    # expected to remain only for the jacket slot (vendor master M_PBR_Base, and the jacket has no morph keys)
    log("SK_Joy slots still without MorphTargets: %s" % lacking)
    report["sk_joy_slots_without_morph_usage"] = lacking
else:
    report["skipped"].append(MESH + " (not loaded as a SkeletalMesh)")

if os.environ.get("SS_USAGE_REPORT"):
    with open(os.environ["SS_USAGE_REPORT"], "w") as f:
        json.dump(report, f, indent=2)
log("DONE masters changed=%d instances saved=%d dry_run=%s" % (len(changed_masters),
                                                              sum(1 for r in report["instances"].values() if r["saved"]), DRY))
