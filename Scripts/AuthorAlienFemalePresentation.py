"""Repair the owned female's broken references through a private derivative.

The integration lead runs this in a separate offscreen editor. Default is dry-run;
-SSApplyAlienFemalePresentation creates a new derivative only when no outputs exist.
-SSApplyAlienFemaleRepair updates an owned nine/eleven/twelve-output derivative without
deleting assets. The legacy material stays untouched; only the private mesh's
material slot changes to the corrected replacement. Existing outputs
require their prior ownership receipt and are backed up before modification.
-SSApplyAlienFemaleGrounding changes only the three receipt-owned baked clips.
Original geometry, skeleton, textures, material and physics asset remain unchanged.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / "Artifacts/AlienFemaleReview"
SOURCE = "/Game/TripoModels/AlienFemale"
BASE = "/Game/SpaceSurvival/Licensed/AlienFemalePresentation"
MESH = BASE + "/SK_AlienFemalePresentation"
LEGACY_MATERIAL = BASE + "/MI_AlienFemalePresentation"
MATERIAL = BASE + "/MI_AlienFemaleCorrected"
SKELETON = BASE + "/SKEL_AlienFemalePresentation"
AUTHOR = BASE + "/Authoring"
SOURCE_MESH = "/Game/Robot_scout_R_21/Mesh/SK_Robot_scout_R21"
SOURCE_CLIPS = "/Game/Robot_scout_R_21/Demo/Animations"
CLIPS = {"ThirdPersonIdle": "A_AlienFemaleIdle", "ThirdPersonWalk": "A_AlienFemaleWalk",
         "ThirdPersonRun": "A_AlienFemaleRun"}
PRIVATE_CLIPS = tuple(BASE + "/" + name for name in CLIPS.values())
LINEAR_MASKS = {"MetallicTex": BASE + "/T_AlienFemaleMetallicLinear",
                "RoughnessTex": BASE + "/T_AlienFemaleRoughnessLinear"}
TARGETS = (MESH, LEGACY_MATERIAL, MATERIAL, SKELETON, AUTHOR + "/IK_Source", AUTHOR + "/IK_Female",
           AUTHOR + "/RTG_Female", *PRIVATE_CLIPS, *LINEAR_MASKS.values())
CHAINS = {"Spine": ("spine_01", "spine_03"), "Neck": ("neck_01", "neck_01"), "Head": ("head", "head")}
for side, word in (("l", "Left"), ("r", "Right")):
    CHAINS.update({word + "Clavicle": ("clavicle_" + side, "clavicle_" + side),
                   word + "Arm": ("upperarm_" + side, "hand_" + side),
                   word + "Leg": ("thigh_" + side, "ball_" + side)})
    for finger in ("thumb", "index", "middle", "ring", "pinky"):
        CHAINS[word + finger.title()] = (finger + "_01_" + side, finger + "_03_" + side)
LIB = u.EditorAssetLibrary
AUTHORIZED = None
AUTH_STATE = {}
# Actual source pixels and import metadata were inspected on September 21. The
# supplied filenames are swapped: "Normal" is black/silver/cyan albedo, and
# "BaseColor" is the purple tangent-space normal map. Preserve the source names.
TEXTURES = {"BaseColorTex": "T_AlienFemale_Normal", "NormalTex": "T_AlienFemale_BaseColor",
            "MetallicTex": "T_AlienFemale_Metallic", "RoughnessTex": "T_AlienFemale_Roughness"}
TEXTURE_SOURCE_SHA256 = {
    "BaseColorTex": "5b04f1d4aceb55ce4ea453c41e5439b231f1b941f9ce6e91ede27c07c6144f96",
    "NormalTex": "bb75d0a9aa7fa4cfadd9d9720911b5d2e1d40c6f8a273e2f0172ca5d9e206e7d",
    "MetallicTex": "9b6805f87b4e4750a173b322b63e4fc8da7d36a2947831ef46f890b422fdc064",
    "RoughnessTex": "dfca595c9e5bf8d8fa54a0becf53f7bc7aa43b5b4d4d8226467a6645e23f30a7",
}


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def package_file(package):
    assert package in TARGETS, "Output escaped the private presentation assets"
    return ROOT / "Content" / (package.removeprefix("/Game/") + ".uasset")


def source_hashes():
    files = list((ROOT / "Content/TripoModels/AlienFemale").glob("*.uasset"))
    files += list((ROOT / "Content/TripoModels/Materials").glob("*.uasset"))
    files += [ROOT / "Content/Robot_scout_R_21/Mesh/UE4_Mannequin_Skeleton.uasset"]
    files += [ROOT / "Content" / (SOURCE_MESH.removeprefix("/Game/") + ".uasset")]
    files += [ROOT / "Content" / (SOURCE_CLIPS.removeprefix("/Game/") + "/" + name + ".uasset") for name in CLIPS]
    return {str(file.relative_to(ROOT)): sha(file) for file in files}


def output_hashes():
    return {package: sha(package_file(package)) for package in TARGETS if package_file(package).exists()}


def validate_pbr_sources(material, textures):
    """Reject changed source identities or graph roles before modifying a derivative."""
    for parameter, name in TEXTURES.items():
        file = ROOT / "Content" / (SOURCE.removeprefix("/Game/") + "/" + name + ".uasset")
        assert sha(file) == TEXTURE_SOURCE_SHA256[parameter], "Reinspect changed PBR source: " + parameter
    assert textures["BaseColorTex"].get_editor_property("srgb")
    assert textures["BaseColorTex"].get_editor_property("compression_settings") == u.TextureCompressionSettings.TC_DEFAULT
    assert not textures["NormalTex"].get_editor_property("srgb")
    assert textures["NormalTex"].get_editor_property("compression_settings") == u.TextureCompressionSettings.TC_NORMALMAP
    base = material.get_base_material()
    assert base.get_path_name() == "/Game/TripoModels/Materials/M_Tripo_PBR_Master.M_Tripo_PBR_Master"
    edit = u.MaterialEditingLibrary
    roles = (("BaseColorTex", u.MaterialProperty.MP_BASE_COLOR, u.MaterialSamplerType.SAMPLERTYPE_COLOR),
             ("NormalTex", u.MaterialProperty.MP_NORMAL, u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
             ("MetallicTex", u.MaterialProperty.MP_METALLIC, u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE),
             ("RoughnessTex", u.MaterialProperty.MP_ROUGHNESS, u.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE))
    result = {}
    for parameter, prop, sampler in roles:
        node = edit.get_material_property_input_node(base, prop)
        # The inspected scalar routes contain one red-channel ComponentMask;
        # color and normal connect directly. Do not accept a new tuning graph.
        if isinstance(node, u.MaterialExpressionComponentMask):
            assert parameter in LINEAR_MASKS
            assert node.get_editor_property("r") and not any(node.get_editor_property(c) for c in ("g", "b", "a"))
            inputs = edit.get_inputs_for_material_expression(base, node)
            assert len(inputs) == 1
            node = inputs[0]
        assert isinstance(node, u.MaterialExpressionTextureSampleParameter2D)
        assert str(node.get_editor_property("parameter_name")) == parameter
        assert node.get_editor_property("sampler_type") == sampler
        assert node.get_editor_property("const_coordinate") == 0
        assert not any(edit.get_inputs_for_material_expression(base, node)), "Unexpected source UV transform"
        result[parameter] = {"source": textures[parameter].get_path_name(),
                             "source_sha256": TEXTURE_SOURCE_SHA256[parameter], "sampler": str(sampler),
                             "private_linear_copy": LINEAR_MASKS.get(parameter)}
    return result


def create_linear_masks(textures, existing=None, save=True):
    result = dict(textures)
    for parameter, target in LINEAR_MASKS.items():
        if existing and target in existing:
            copy = LIB.load_asset(target)
            assert isinstance(copy, u.Texture2D), "Owned mask does not load: " + target
            assert LIB.get_metadata_tag(copy, "SSSourceSHA256") == TEXTURE_SOURCE_SHA256[parameter]
            assert LIB.get_metadata_tag(copy, "SSSourcePackage") == SOURCE + "/" + TEXTURES[parameter]
            assert not copy.get_editor_property("srgb")
            assert copy.get_editor_property("compression_settings") == u.TextureCompressionSettings.TC_GRAYSCALE
            result[parameter] = copy
            continue
        copy = LIB.duplicate_asset(SOURCE + "/" + TEXTURES[parameter], target)
        assert isinstance(copy, u.Texture2D), "Could not create the new private mask: " + target
        # The original JPEG mask pixels are scalar data, despite the source's
        # sRGB flag. TC_Grayscale + SRGB=false matches the existing master's
        # LinearGrayscale sampler (installed MaterialExpressions.cpp:14042).
        copy.set_editor_property("srgb", False)
        copy.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_GRAYSCALE)
        assert not copy.get_editor_property("srgb")
        assert copy.get_editor_property("compression_settings") == u.TextureCompressionSettings.TC_GRAYSCALE
        LIB.set_metadata_tag(copy, "SSSourceSHA256", TEXTURE_SOURCE_SHA256[parameter])
        LIB.set_metadata_tag(copy, "SSSourcePackage", SOURCE + "/" + TEXTURES[parameter])
        if save:
            assert LIB.save_loaded_asset(copy, only_if_is_dirty=False), "Could not save private mask: " + target
        result[parameter] = copy
    return result


def ground_clip(mesh, clip, apply=False):
    result = json.loads(u.SSCharacterAuthoringLibrary.ground_alien_female_clip(mesh, clip, apply))
    assert result.get("success"), "Private clip grounding rejected: " + json.dumps(result)
    return result


def bind_signature(mesh):
    modifier = u.SkeletonModifier()
    assert modifier.set_skeletal_mesh(mesh)
    result = []
    for name in modifier.get_all_bone_names():
        transform = modifier.get_bone_transform(name, False)
        result.append((str(name), str(modifier.get_parent_name(name)),
                       tuple(getattr(transform.translation, axis) for axis in "xyz"),
                       tuple(getattr(transform.rotation, axis) for axis in "xyzw"),
                       tuple(getattr(transform.scale3d, axis) for axis in "xyz")))
    return result


def normalization(mesh, apply):
    """Unit-scale bind bones at the exact original global positions/orientations.

    SkeletonModifier commits inverse bind matrices and unchanged mesh positions.
    Only transforms change, so UE's PreCommitSkeleton takes its no-skeleton-change
    path. A fresh private skeleton is then created from this normalized mesh.
    """
    modifier = u.SkeletonModifier()
    assert modifier.set_skeletal_mesh(mesh)
    names = list(modifier.get_all_bone_names())
    parents = {str(name): str(modifier.get_parent_name(name)) for name in names}
    original = {str(name): modifier.get_bone_transform(name, True) for name in names}
    normalized = {}
    for name, value in original.items():
        transform = u.Transform()
        transform.set_editor_property("translation", value.translation)
        transform.set_editor_property("rotation", value.rotation)
        transform.set_editor_property("scale3d", u.Vector(1, 1, 1))
        normalized[name] = transform
    normalized["root"] = u.Transform()
    locals_ = []
    for name in names:
        key = str(name)
        parent = parents[key]
        locals_.append(u.MathLibrary.make_relative_transform(normalized[key], normalized[parent])
                       if parent in normalized else normalized[key])
    result = {"bones": len(names), "original_root": str(original["root"]),
              "normalized_root": str(normalized["root"]), "global_joint_locations_preserved_except_root": True}
    if apply:
        assert modifier.set_bones_transforms(names, locals_, True)
        for name in names:
            actual = modifier.get_bone_transform(name, True)
            expected = normalized[str(name)]
            assert (actual.translation - expected.translation).length() < .001, "Joint position changed: " + str(name)
            assert (actual.scale3d - u.Vector(1, 1, 1)).length() < .001, "Bone scale remains: " + str(name)
        assert modifier.commit_skeleton_to_skeletal_mesh()
    return result


def build_rig(name, mesh):
    tools = u.AssetToolsHelpers.get_asset_tools()
    rig = tools.create_asset(name, AUTHOR, u.IKRigDefinition, u.IKRigDefinitionFactory())
    assert rig
    control = u.IKRigController.get_controller(rig)
    assert control.set_skeletal_mesh(mesh)
    assert control.set_retarget_root("pelvis")
    assert control.set_root_motion_bone("root")
    for chain, (start, end) in CHAINS.items():
        assert str(control.add_retarget_chain(chain, start, end, "None")) == chain
    assert len(control.get_retarget_chains()) == len(CHAINS)
    assert LIB.save_loaded_asset(rig, only_if_is_dirty=False)
    return rig


def retarget(mesh, skeleton):
    source_mesh = u.load_asset(SOURCE_MESH)
    rigs = [build_rig("IK_Source", source_mesh), build_rig("IK_Female", mesh)]
    retargeter = u.AssetToolsHelpers.get_asset_tools().create_asset("RTG_Female", AUTHOR, u.IKRetargeter, u.IKRetargetFactory())
    assert retargeter
    control = u.IKRetargeterController.get_controller(retargeter)
    for side, rig, body in zip((u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET), rigs, (source_mesh, mesh)):
        control.set_ik_rig(side, rig)
        control.set_preview_mesh(side, body)
    control.add_default_ops()
    for side, rig in zip((u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET), rigs):
        control.assign_ik_rig_to_all_ops(side, rig)
    control.auto_map_chains(u.AutoMapChainType.EXACT, True)
    target = u.RetargetSourceOrTarget.TARGET
    pose = control.create_retarget_pose("FemaleAligned", target)
    assert str(pose) == "FemaleAligned" and control.set_current_retarget_pose(pose, target)
    control.auto_align_all_bones(target, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    control.snap_bone_to_ground("ball_l", target)
    assert LIB.save_loaded_asset(retargeter, only_if_is_dirty=False)
    registry = u.AssetRegistryHelpers.get_asset_registry()
    made, grounding = [], []
    for source, output in CLIPS.items():
        inputs = u.IKRetargetBatchOperationInputs()
        for prop, value in {"assets_to_retarget": [registry.get_asset_by_object_path(SOURCE_CLIPS + "/" + source + "." + source)],
                            "source_mesh": source_mesh, "target_mesh": mesh, "ik_retarget_asset": retargeter,
                            "search": source, "replace": output, "target_path": BASE, "use_source_path": False,
                            "include_referenced_assets": False, "overwrite_existing_files": False}.items():
            inputs.set_editor_property(prop, value)
        assets = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        assert assets and len(assets) == 1, "Retarget did not produce the requested single clip"
        clip = LIB.load_asset(BASE + "/" + output)
        assert isinstance(clip, u.AnimSequence) and clip.get_editor_property("skeleton") == skeleton
        grounding.append(ground_clip(mesh, clip, True))
        assert LIB.save_loaded_asset(clip, only_if_is_dirty=False)
        made.append(clip.get_path_name())
    return made, grounding


def main():
    global AUTHORIZED, AUTH_STATE
    command = u.SystemLibrary.get_command_line()
    rebuild = "-SSApplyAlienFemalePresentation" in command
    grounding_only = "-SSApplyAlienFemaleGrounding" in command
    repair = "-SSApplyAlienFemaleRepair" in command
    assert sum((rebuild, grounding_only, repair)) <= 1, "Select one private author operation"
    apply = rebuild or grounding_only or repair
    before = source_hashes()
    mesh = u.load_asset(SOURCE + "/SK_AlienFemale")
    material = u.load_asset(SOURCE + "/MI_AlienFemale")
    skeleton = u.load_asset("/Game/Robot_scout_R_21/Mesh/UE4_Mannequin_Skeleton")
    textures = {parameter: u.load_asset(SOURCE + "/" + name) for parameter, name in TEXTURES.items()}
    assert isinstance(mesh, u.SkeletalMesh) and isinstance(material, u.MaterialInstanceConstant)
    assert skeleton and mesh.get_editor_property("skeleton") == skeleton
    assert all(isinstance(texture, u.Texture2D) for texture in textures.values())
    pbr = validate_pbr_sources(material, textures)
    edit = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    vertices = edit.get_num_verts(mesh, 0)
    assert vertices > 1000 and edit.get_num_sections(mesh, 0) == 1, "Inspect changed source topology"
    assert len(mesh.get_editor_property("materials")) == 1, "Inspect changed source material layout"
    existing = output_hashes()
    inventory = ({item.split(".")[0] for item in LIB.list_assets(BASE, recursive=True, include_folder=False)}
                 if LIB.does_directory_exist(BASE) else set())
    assert inventory == set(existing), "Private folder contains unexpected or unsaved assets; preserving it"
    receipt = OUT / "author.json"
    previous = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
    if existing:
        assert previous and previous.get("status") in ("complete", "partial"), "Preserving unowned private outputs"
        assert previous.get("source_preserved"), "Previous author did not preserve originals"
        assert existing == previous.get("output_hashes"), "Preserving edited private outputs"
        assert previous.get("source_hashes") == before, "Original source changed since derivative authoring"
    if rebuild:
        assert not existing, "Existing derivatives are preserved; use -SSApplyAlienFemaleRepair, never delete/rebuild"
    if repair:
        eleven = set(TARGETS) - {MATERIAL}
        predecessor = eleven - set(LINEAR_MASKS.values())
        assert previous and set(existing) in (predecessor, eleven, set(TARGETS)), \
            "Repair requires the complete receipt-owned nine-, eleven- or twelve-output baseline"
    result = {"utc": datetime.now(timezone.utc).isoformat(), "mode": "apply" if apply else "dry-run",
              "source_hashes": before, "targets": list(TARGETS), "source_vertices": vertices,
              "source_skeleton": skeleton.get_path_name(), "textures": {key: obj.get_path_name()
                                                                           for key, obj in textures.items()},
              "geometry_modified": False, "normalization": normalization(mesh, False),
              "pbr_source_roles": pbr,
              "status": "dry-run", "source_preserved": False}
    OUT.mkdir(parents=True, exist_ok=True)
    if existing and not rebuild:
        # A read-only plan can inspect the receipt-owned nine-output predecessor
        # before the full rebuild adds two linear masks. Grounding-only never
        # claims that predecessor is the complete corrected material set.
        required = set(TARGETS) if grounding_only else {MESH, *PRIVATE_CLIPS}
        assert required <= set(existing), "Grounding requires the owned mesh and baked clips"
        private_mesh = LIB.load_asset(MESH)
        result["grounding_preview"] = [ground_clip(private_mesh, LIB.load_asset(path)) for path in PRIVATE_CLIPS]
    if repair:
        backup = OUT / "Backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup.mkdir(parents=True, exist_ok=True)
        for package, digest in existing.items():
            destination = backup / package.removeprefix(BASE + "/")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = destination.with_suffix(".uasset")
            shutil.copy2(package_file(package), destination)
            assert sha(destination) == digest, "Backup verification failed: " + package
        shutil.copy2(receipt, backup / "author.json")
        AUTHORIZED = before
        AUTH_STATE = {"mode": "apply", "operation": "targeted-repair", "backup": str(backup),
                      "baseline_output_hashes": existing}
        legacy_material = LIB.load_asset(LEGACY_MATERIAL)
        assert isinstance(legacy_material, u.MaterialInstanceConstant), "Owned legacy material is unavailable"
        private_material = LIB.load_asset(MATERIAL) if MATERIAL in existing else None
        slots = list(private_mesh.get_editor_property("materials"))
        assert len(slots) == 1 and slots[0].material_interface in (legacy_material, private_material), \
            "Preserving a mesh whose material assignment differs from the owned baseline"
        assert private_mesh.get_editor_property("skeleton") == LIB.load_asset(SKELETON)
        original_bind = bind_signature(private_mesh)
        original_vertices = edit.get_num_verts(private_mesh, 0)
        original_sections = edit.get_num_sections(private_mesh, 0)
        original_physics = private_mesh.get_editor_property("physics_asset")
        # Never save or delete the legacy MI: another editor may hold its file open.
        # The unique replacement is published with its masks before the mesh references it.
        if private_material is None:
            private_material = LIB.duplicate_asset(LEGACY_MATERIAL, MATERIAL)
        assert isinstance(private_material, u.MaterialInstanceConstant), "Could not create corrected material"
        corrected_textures = create_linear_masks(textures, existing, save=False)
        materials = u.MaterialEditingLibrary
        material_changed = MATERIAL not in existing
        for parameter, texture in corrected_textures.items():
            if materials.get_material_instance_texture_parameter_value(private_material, parameter) != texture:
                materials.set_material_instance_texture_parameter_value(private_material, parameter, texture)
                material_changed = True
            assert materials.get_material_instance_texture_parameter_value(private_material, parameter) == texture, \
                "Texture parameter read-back failed: " + parameter
        assert output_hashes() == existing and source_hashes() == before, "Baseline changed before the first save"
        if material_changed:
            materials.set_material_usage_override(private_material, u.MaterialUsage.MATUSAGE_SKELETAL_MESH, True, True)
            materials.update_material_instance(private_material)
            assert LIB.save_loaded_asset(private_material, only_if_is_dirty=False), \
                "Corrected material could not be saved; no legacy material is modified or deleted"
        for parameter, package in LINEAR_MASKS.items():
            if package not in existing:
                assert LIB.save_loaded_asset(corrected_textures[parameter], only_if_is_dirty=False), \
                    "Could not save the new private mask: " + package
        if slots[0].material_interface != private_material:
            slots[0].material_interface = private_material
            private_mesh.set_editor_property("materials", slots)
            assert bind_signature(private_mesh) == original_bind, "Material assignment changed the bind pose"
            assert edit.get_num_verts(private_mesh, 0) == original_vertices
            assert edit.get_num_sections(private_mesh, 0) == original_sections
            assert private_mesh.get_editor_property("physics_asset") == original_physics
            assert private_mesh.get_editor_property("skeleton") == LIB.load_asset(SKELETON)
            assert LIB.save_loaded_asset(private_mesh, only_if_is_dirty=False), \
                "Could not save the private mesh's corrected material slot; preserve the backup"
        grounded = []
        for package, preview in zip(PRIVATE_CLIPS, result["grounding_preview"]):
            clip = LIB.load_asset(package)
            needs_change = abs(preview["root_offset_z_cm"]) > .0001
            corrected = ground_clip(private_mesh, clip, needs_change)
            if needs_change:
                assert LIB.save_loaded_asset(clip, only_if_is_dirty=False), "Could not save grounded clip: " + package
            corrected["already_grounded"] = not needs_change
            grounded.append(corrected)
        after = output_hashes()
        writable = {MESH, MATERIAL, *PRIVATE_CLIPS, *LINEAR_MASKS.values()}
        assert set(after) == set(TARGETS), "Targeted repair did not produce the complete twelve outputs"
        assert all(after[package] == digest for package, digest in existing.items() if package not in writable), \
            "Repair changed the preserved legacy material, skeleton or authoring assets"
        result = {**previous, **AUTH_STATE, "utc": datetime.now(timezone.utc).isoformat(), "status": "complete",
                  "targets": list(TARGETS), "grounding": grounded, "pbr_source_roles": pbr,
                  "textures": {key: obj.get_path_name() for key, obj in corrected_textures.items()},
                  "mesh_material_assignment_only": True, "mesh_bind_preserved": True,
                  "legacy_material_preserved": True, "skeleton_authoring_preserved": True, "output_hashes": after}
    elif grounding_only:
        assert existing and previous, "Grounding never creates or adopts a private derivative"
        backup = OUT / "Backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup.mkdir(parents=True, exist_ok=True)
        for package in PRIVATE_CLIPS:
            shutil.copy2(package_file(package), backup / (package.rsplit("/", 1)[-1] + ".uasset"))
        shutil.copy2(receipt, backup / "author.json")
        AUTHORIZED = before
        grounded = []
        for package, preview in zip(PRIVATE_CLIPS, result["grounding_preview"]):
            clip = LIB.load_asset(package)
            needs_change = abs(preview["root_offset_z_cm"]) > .0001
            corrected = ground_clip(private_mesh, clip, needs_change)
            if needs_change:
                assert LIB.save_loaded_asset(clip, only_if_is_dirty=False)
            corrected["already_grounded"] = not needs_change
            grounded.append(corrected)
        after = output_hashes()
        assert all(after[package] == digest for package, digest in existing.items() if package not in PRIVATE_CLIPS), \
            "Grounding changed a non-animation derivative"
        result = {**previous, "utc": datetime.now(timezone.utc).isoformat(), "mode": "apply", "operation": "grounding-only",
                  "status": "complete", "backup": str(backup), "grounding": grounded,
                  "non_animation_outputs_preserved": True, "output_hashes": after}
    elif rebuild:
        AUTHORIZED = before
        private_mesh = LIB.duplicate_asset(SOURCE + "/SK_AlienFemale", MESH)
        private_material = LIB.duplicate_asset(SOURCE + "/MI_AlienFemale", MATERIAL)
        assert isinstance(private_mesh, u.SkeletalMesh) and isinstance(private_material, u.MaterialInstanceConstant)
        textures = create_linear_masks(textures)
        result["textures"] = {key: obj.get_path_name() for key, obj in textures.items()}
        materials = u.MaterialEditingLibrary
        actual_parameters = {str(name) for name in materials.get_texture_parameter_names(private_material)}
        assert set(textures) <= actual_parameters, "Private material parent lacks the inspected PBR parameters"
        for parameter, texture in textures.items():
            # UE5.8.2 MaterialEditingLibrary.cpp:1507 initializes bResult=false and
            # never sets it even after a successful write. Read-back is the contract.
            materials.set_material_instance_texture_parameter_value(private_material, parameter, texture)
            assert materials.get_material_instance_texture_parameter_value(private_material, parameter) == texture, \
                "Texture parameter read-back failed: " + parameter
        materials.set_material_usage_override(private_material, u.MaterialUsage.MATUSAGE_SKELETAL_MESH, True, True)
        materials.update_material_instance(private_material)
        slots = list(private_mesh.get_editor_property("materials"))
        slots[0].material_interface = private_material
        private_mesh.set_editor_property("materials", slots)
        # Walker collision is its native capsule. The original missing/differently-bound body
        # asset must not supply misleading render bounds or a second collision authority.
        private_mesh.set_editor_property("physics_asset", None)
        assert private_mesh.get_editor_property("skeleton") == skeleton
        result["normalization"] = normalization(private_mesh, True)
        # SkeletonFactory.TargetSkeletalMesh is reflected but protected from Python.
        # The native bridge checks exact private paths and normalized bones, and never saves.
        private_skeleton = u.SSCharacterAuthoringLibrary.create_alien_female_skeleton(private_mesh)
        assert private_skeleton and private_mesh.get_editor_property("skeleton") == private_skeleton
        assert edit.get_num_verts(private_mesh, 0) == vertices, "Derivative geometry must match source"
        for parameter, texture in textures.items():
            assert materials.get_material_instance_texture_parameter_value(private_material, parameter) == texture
        assert LIB.save_loaded_asset(private_material, only_if_is_dirty=False)
        legacy_material = LIB.duplicate_asset(MATERIAL, LEGACY_MATERIAL)
        assert isinstance(legacy_material, u.MaterialInstanceConstant)
        assert LIB.save_loaded_asset(legacy_material, only_if_is_dirty=False)
        assert LIB.save_loaded_asset(private_skeleton, only_if_is_dirty=False)
        assert LIB.save_loaded_asset(private_mesh, only_if_is_dirty=False)
        result["retargeted_clips"], result["grounding"] = retarget(private_mesh, private_skeleton)
        result.update(status="complete", output_hashes=output_hashes())
    result["source_preserved"] = before == source_hashes()
    assert result["source_preserved"], "Original source changed during private authoring"
    if result["status"] == "complete":
        # Recovery keeps the earlier failure in its backed-up receipt, not as a
        # current error on the successful author result.
        result.pop("error", None)
    destination = receipt if apply else OUT / "author-dry-run.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


try:
    main()
except Exception as error:
    # Only files created after the ownership gate can enter a recovery receipt.
    # A rejection of pre-existing unknown content never adopts or rewrites it.
    if AUTHORIZED is not None:
        OUT.mkdir(parents=True, exist_ok=True)
        partial = {**AUTH_STATE, "utc": datetime.now(timezone.utc).isoformat(), "status": "partial", "error": repr(error),
                   "source_hashes": AUTHORIZED, "source_preserved": AUTHORIZED == source_hashes(),
                   "output_hashes": output_hashes(), "targets": list(TARGETS)}
        (OUT / "author.json").write_text(json.dumps(partial, indent=2) + "\n", encoding="utf-8")
    raise
