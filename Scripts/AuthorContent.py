"""Author real Unreal content from preserved, reviewable source files.

In Editor: py "C:/path/to/SpaceSurvival/Scripts/AuthorContent.py"
Full Editor: UnrealEditor-Cmd.exe SpaceSurvival.uproject -unattended
             -ExecutePythonScript=Scripts/AuthorContent.py
Source-only: python Scripts/AuthorContent.py --source-only

No .uasset/.umap stand-ins are written. Import exceptions are fatal and recorded.
Existing authored assets are preserved on rerun; delete/reimport deliberately in
Editor if changing source. The supplied character GLB is never modified.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "/Game/SpaceSurvival"
HERO_HASH = "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"
MAP_PATH = BASE + "/Maps/Survival"


def source_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_hero():
    path = ROOT / "model-rigged.glb"
    if not path.is_file():
        raise RuntimeError(f"Supplied rigged Acornaut source is missing: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != HERO_HASH:
        raise RuntimeError("Supplied Acornaut GLB changed; review source provenance before importing")
    return path


def generate_sources():
    verify_hero()
    geometry = source_module("ss_geometry", ROOT / "ContentSource" / "GenerateGeometry.py")
    audio = source_module("ss_audio", ROOT / "Scripts" / "GenerateAudio.py")
    return geometry.main(), audio.main()


def read_sources():
    """Import checked-in sources; editor Python must not rewrite source content."""
    verify_hero()
    manifests = []
    for directory, extension in (("Meshes", ".obj"), ("Audio", ".wav")):
        folder = ROOT / "ContentSource" / directory
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        for item in manifest["assets"]:
            path = folder / (item["name"] + extension)
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise RuntimeError(f"Source differs from its manifest: {path}; regenerate and review before importing")
        manifests.append(manifest)
    return tuple(manifests)


class Author:
    def __init__(self, unreal, meshes, audio):
        self.u = unreal
        self.mesh_manifest = meshes
        self.audio_manifest = audio
        self.tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.library = unreal.EditorAssetLibrary
        self.created = []
        self.errors = []

    def required(self, path, cls=None):
        asset = self.library.load_asset(path)
        if not asset:
            raise RuntimeError(f"Required asset failed to load: {path}")
        if cls and not isinstance(asset, cls):
            raise RuntimeError(f"{path}: expected {cls.__name__}, found {asset.get_class().get_name()}")
        return asset

    def save(self, asset):
        self.library.set_metadata_tag(asset, "SSAuthoringVersion", "1")
        if not self.library.save_loaded_asset(asset, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save {asset.get_path_name()}")
        self.created.append(asset.get_path_name())
        return asset

    def existing_authored(self, path, cls=None):
        asset = self.required(path, cls)
        if self.library.get_metadata_tag(asset, "SSAuthoringVersion") != "1":
            raise RuntimeError(f"{path}: existing asset has no completed authoring marker; inspect partial/manual import before adopting it")
        return asset

    def stage(self, label, fn):
        try:
            fn()
        except Exception as error:
            message = f"{label}: {error}"
            self.errors.append(message)
            self.u.log_error(message)

    def palette(self):
        u = self.u
        edit = u.MaterialEditingLibrary
        for name, (rgb, metal, rough, emission) in self.mesh_manifest["palette"].items():
            path = f"{BASE}/Materials/{name}"
            if self.library.does_asset_exist(path):
                material = self.existing_authored(path, u.Material)
                if name in ("M_Hull", "M_Gold", "M_Cyan") and not material.get_editor_property("used_with_instanced_static_meshes"):
                    material.set_editor_property("used_with_instanced_static_meshes", True)
                    edit.recompile_material(material)
                    self.save(material)
                continue
            material = self.tools.create_asset(name, BASE + "/Materials", u.Material, u.MaterialFactoryNew())
            if not material:
                raise RuntimeError(f"Could not create material {path}")
            if name in ("M_Space", "M_Star", "M_StarWarm"):
                material.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT)
                material.set_editor_property("two_sided", True)

            if name in ("M_Hull", "M_Gold", "M_Cyan"):
                material.set_editor_property("used_with_instanced_static_meshes", True)

            def vector(parameter, color, x, y):
                node = edit.create_material_expression(material, u.MaterialExpressionVectorParameter, x, y)
                node.set_editor_property("parameter_name", parameter)
                node.set_editor_property("default_value", u.LinearColor(*color, 1))
                return node

            def scalar(parameter, value, x, y):
                node = edit.create_material_expression(material, u.MaterialExpressionScalarParameter, x, y)
                node.set_editor_property("parameter_name", parameter)
                node.set_editor_property("default_value", value)
                return node

            tint = vector("Tint", (1, 1, 1), -900, -200)
            color = vector("Color", rgb, -900, 0)
            multiply = edit.create_material_expression(material, u.MaterialExpressionMultiply, -600, 0)
            edit.connect_material_expressions(tint, "", multiply, "A")
            edit.connect_material_expressions(color, "", multiply, "B")
            edit.connect_material_property(multiply, "", u.MaterialProperty.MP_BASE_COLOR)
            metal_node = scalar("Metallic", metal, -600, 200)
            rough_node = scalar("Roughness", rough, -600, 300)
            emission_node = scalar("Emission", emission, -600, 400)
            edit.connect_material_property(metal_node, "", u.MaterialProperty.MP_METALLIC)
            edit.connect_material_property(rough_node, "", u.MaterialProperty.MP_ROUGHNESS)
            glow = edit.create_material_expression(material, u.MaterialExpressionMultiply, -250, 100)
            edit.connect_material_expressions(multiply, "", glow, "A")
            edit.connect_material_expressions(emission_node, "", glow, "B")
            edit.connect_material_property(glow, "", u.MaterialProperty.MP_EMISSIVE_COLOR)
            edit.recompile_material(material)
            self.save(material)

    def task_import(self, filename, destination, name, options=None, factory=None):
        u = self.u
        task = u.AssetImportTask()
        for key, value in {"filename": str(filename), "destination_path": destination,
                           "destination_name": name, "automated": True,
                           "replace_existing": False, "save": True}.items():
            task.set_editor_property(key, value)
        if options:
            task.set_editor_property("options", options)
        if factory:
            task.set_editor_property("factory", factory)
        self.tools.import_asset_tasks([task])
        paths = list(task.get_editor_property("imported_object_paths"))
        if not paths:
            raise RuntimeError(f"Importer produced no objects for {filename}; inspect Unreal import log")
        return [self.required(path) for path in paths]

    def static_mesh(self, item):
        u = self.u
        name = item["name"]
        path = f"{BASE}/Meshes/{name}"
        if self.library.does_asset_exist(path):
            self.existing_authored(path, u.StaticMesh)
            return
        options = u.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("mesh_type_to_import", u.FBXImportType.FBXIT_STATIC_MESH)
        data = options.get_editor_property("static_mesh_import_data")
        data.set_editor_property("combine_meshes", True)
        data.set_editor_property("auto_generate_collision", name != "SM_Starfield")
        data.set_editor_property("generate_lightmap_u_vs", True)
        data.set_editor_property("import_uniform_scale", 1.0)
        data.set_editor_property("convert_scene", False)
        data.set_editor_property("force_front_x_axis", False)
        data.set_editor_property("normal_import_method", u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        imported = self.task_import(ROOT / "ContentSource" / "Meshes" / (name + ".obj"), BASE + "/Meshes", name, options, u.FbxFactory())
        meshes = [obj for obj in imported if isinstance(obj, u.StaticMesh)]
        if len(meshes) != 1:
            raise RuntimeError(f"{name}: expected one combined mesh; imported {len(meshes)}")
        mesh = meshes[0]
        if mesh.get_path_name().split(".")[0] != path:
            if not self.library.rename_asset(mesh.get_path_name(), path):
                raise RuntimeError(f"Cannot assign canonical asset name {path}")
            mesh = self.required(path, u.StaticMesh)
        slots = mesh.get_editor_property("static_materials")
        seen = set()
        for index, slot in enumerate(slots):
            imported_name = str(slot.get_editor_property("imported_material_slot_name"))
            slot_name = str(slot.get_editor_property("material_slot_name"))
            material_name = imported_name if imported_name in item["materials"] else slot_name
            if material_name not in item["materials"]:
                raise RuntimeError(f"{name}: unknown material slot {imported_name}/{slot_name}; do not silently flatten authored palette")
            mesh.set_material(index, self.required(f"{BASE}/Materials/{material_name}"))
            seen.add(material_name)
        if set(item["materials"]) != seen:
            raise RuntimeError(f"{name}: imported material groups differ from source")
        self.save(mesh)

    def hero_materials(self, mesh):
        for slot in mesh.get_editor_property("materials"):
            material = slot.get_editor_property("material_interface")
            if not material:
                raise RuntimeError("Acornaut skeletal material is missing")
            base = material.get_base_material()
            if not base.get_editor_property("used_with_skeletal_mesh"):
                base.set_editor_property("used_with_skeletal_mesh", True)
                self.u.MaterialEditingLibrary.recompile_material(base)
                self.save(base)

    def hero(self):
        u = self.u
        destination = BASE + "/Character"
        target_mesh = destination + "/SK_Acornaut"
        target_walk = destination + "/A_Walk"
        if self.library.does_asset_exist(target_mesh) and self.library.does_asset_exist(target_walk):
            mesh = self.existing_authored(target_mesh, u.SkeletalMesh)
            walk = self.existing_authored(target_walk, u.AnimSequence)
            if mesh.get_editor_property("skeleton") != walk.get_editor_property("skeleton"):
                raise RuntimeError("Existing character and walk animation do not share a skeleton")
            if walk.get_editor_property("sequence_length") <= 0:
                raise RuntimeError("Existing walk animation has no duration")
            self.hero_materials(mesh)
            return
        if self.library.does_asset_exist(target_mesh) or self.library.does_asset_exist(target_walk):
            raise RuntimeError("Partial character import exists; reconcile canonical mesh and animation before rerun")
        manager = u.InterchangeManager.get_interchange_manager_scripted()
        source = manager.create_source_data(str(verify_hero()))
        if not manager.can_translate_source_data(source):
            raise RuntimeError("No GLB Interchange translator available. Enable Interchange and InterchangeEditor plugins")
        # Use an owned copy so global/user Interchange defaults remain untouched.
        pipeline_path = BASE + "/Authoring/P_AcornautImport"
        if not self.library.does_asset_exist(pipeline_path):
            template = "/Interchange/Pipelines/DefaultAssetsPipeline"
            self.required(template)
            if not self.library.duplicate_asset(template, pipeline_path):
                raise RuntimeError("Cannot duplicate built-in Interchange assets pipeline")
        pipeline = self.required(pipeline_path)
        pipeline.set_editor_property("asset_type_sub_folders", False)
        pipeline.set_editor_property("scene_name_sub_folder", False)
        pipeline.set_editor_property("use_source_name_for_asset", False)
        mesh_settings = pipeline.get_editor_property("mesh_pipeline")
        mesh_settings.set_editor_property("import_skeletal_meshes", True)
        mesh_settings.set_editor_property("import_static_meshes", False)
        mesh_settings.set_editor_property("combine_skeletal_meshes_behavior", u.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON)
        mesh_settings.set_editor_property("create_physics_asset", True)
        animation = pipeline.get_editor_property("animation_pipeline")
        animation.set_editor_property("import_animations", True)
        self.save(pipeline)
        params = u.ImportAssetParameters()
        params.set_editor_property("is_automated", True)
        params.set_editor_property("replace_existing", False)
        params.set_editor_property("override_pipelines", [u.SoftObjectPath(pipeline.get_path_name())])
        imported = manager.import_asset(destination, source, params)
        if not imported:
            raise RuntimeError("GLB import returned no assets. Skeletal mesh and walk animation are required; see import log")
        meshes = [obj for obj in imported if isinstance(obj, u.SkeletalMesh)]
        walks = [obj for obj in imported if isinstance(obj, u.AnimSequence)]
        if len(meshes) != 1 or len(walks) != 1:
            raise RuntimeError(f"Expected 1 skeletal mesh and 1 walk animation; got {len(meshes)} and {len(walks)}")
        if "walk" not in walks[0].get_name().lower():
            raise RuntimeError(f"Unexpected GLB animation: {walks[0].get_name()}; inspect before naming A_Walk")
        for obj, target in ((meshes[0], target_mesh), (walks[0], target_walk)):
            if not self.library.rename_asset(obj.get_path_name(), target):
                raise RuntimeError(f"Failed renaming imported {obj.get_name()} to {target}")
            self.save(self.required(target))
        mesh = self.required(target_mesh, u.SkeletalMesh)
        walk = self.required(target_walk, u.AnimSequence)
        if mesh.get_editor_property("skeleton") != walk.get_editor_property("skeleton"):
            raise RuntimeError("Character mesh and walk animation do not share a skeleton")
        if walk.get_editor_property("sequence_length") <= 0:
            raise RuntimeError("Imported walk animation has no duration")
        for obj in imported:
            self.save(obj)
        self.hero_materials(mesh)

    def sound(self, item):
        u = self.u
        name = item["name"]
        path = f"{BASE}/Audio/{name}"
        if self.library.does_asset_exist(path):
            sound = self.required(path, u.SoundWave)
        else:
            imported = self.task_import(ROOT / "ContentSource" / "Audio" / (name + ".wav"), BASE + "/Audio", name)
            sound = self.required(path, u.SoundWave)
            if sound not in imported:
                raise RuntimeError(f"{name}: import did not produce expected sound")
        sound.set_editor_property("looping", item["loop"])
        self.save(sound)

    def animation_clip(self, name, seconds, actor_owned_motion=False):
        u = self.u
        path = BASE + "/Character/A_" + name
        source = ROOT / "ContentSource/Animation" / (name + ".glb")
        manifest = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != manifest["animation_sha256"]:
            raise RuntimeError(f"{name} animation source differs from its manifest")
        format_tag = "SS" + name + "SourceFormat"
        hash_tag = "SS" + name + "SourceSHA256"
        mesh = self.required(BASE + "/Character/SK_Acornaut", u.SkeletalMesh)
        skeleton = mesh.get_editor_property("skeleton")
        if self.library.does_asset_exist(path):
            clip = self.existing_authored(path, u.AnimSequence)
            if self.library.get_metadata_tag(clip,format_tag) != "OriginalGLTFBasis1":
                raise RuntimeError(f"Existing {name} clip needs deliberate reimport with original glTF joint basis")
            stored_hash = self.library.get_metadata_tag(clip, hash_tag)
            if (stored_hash or actor_owned_motion) and stored_hash != digest:
                raise RuntimeError(f"Existing {name} clip differs from its source; deliberate reimport required")
        else:
            pipeline_path = BASE + "/Authoring/P_" + name + "Import"
            if not self.library.does_asset_exist(pipeline_path):
                if not self.library.duplicate_asset("/Interchange/Pipelines/DefaultAssetsPipeline",pipeline_path):
                    raise RuntimeError(f"Cannot create {name} animation import pipeline")
            pipeline = self.required(pipeline_path)
            pipeline.set_editor_property("asset_name","A_" + name)
            pipeline.set_editor_property("use_source_name_for_asset",False)
            pipeline.set_editor_property("asset_type_sub_folders",False)
            pipeline.set_editor_property("scene_name_sub_folder",False)
            common = pipeline.get_editor_property("common_skeletal_meshes_and_animations_properties")
            common.set_editor_property("import_only_animations",True)
            common.set_editor_property("skeleton",skeleton)
            common.set_editor_property("try_auto_select_skeleton",False)
            pipeline.get_editor_property("mesh_pipeline").set_editor_property("import_skeletal_meshes",False)
            pipeline.get_editor_property("mesh_pipeline").set_editor_property("import_static_meshes",False)
            pipeline.get_editor_property("mesh_pipeline").set_editor_property("create_physics_asset",False)
            pipeline.get_editor_property("animation_pipeline").set_editor_property("import_animations",True)
            pipeline.get_editor_property("material_pipeline").set_editor_property("import_materials",False)
            pipeline.get_editor_property("material_pipeline").get_editor_property("texture_pipeline").set_editor_property("import_textures",False)
            self.save(pipeline)
            manager = u.InterchangeManager.get_interchange_manager_scripted()
            params = u.ImportAssetParameters()
            params.set_editor_property("is_automated",True)
            params.set_editor_property("replace_existing",False)
            params.set_editor_property("override_pipelines",[u.SoftObjectPath(pipeline.get_path_name())])
            imported = manager.import_asset(BASE+"/Character",manager.create_source_data(str(source)),params)
            clips = [obj for obj in imported if isinstance(obj,u.AnimSequence)]
            if len(clips) != 1 or len(imported) != 1:
                raise RuntimeError(f"{name} source must import exactly one animation and no replacement mesh/skeleton")
            clip = clips[0]
            if clip.get_path_name().split(".")[0] != path:
                if not self.library.rename_asset(clip.get_path_name(),path):
                    raise RuntimeError(f"Cannot name {name} animation")
                clip = self.required(path,u.AnimSequence)
            self.library.set_metadata_tag(clip,format_tag,"OriginalGLTFBasis1")
            self.library.set_metadata_tag(clip, hash_tag, digest)
            if actor_owned_motion:
                clip.set_editor_property("enable_root_motion", False)
                clip.set_editor_property("force_root_lock", False)
            self.save(clip)
        if clip.get_editor_property("skeleton") != skeleton or abs(clip.get_editor_property("sequence_length")-seconds) > .01:
            raise RuntimeError(f"{name} animation skeleton or duration differs from source contract")
        if actor_owned_motion and (clip.get_editor_property("enable_root_motion") or clip.get_editor_property("force_root_lock")):
            raise RuntimeError(f"{name} must preserve the local pelvis track without root motion extraction")

    def pilot(self):
        self.animation_clip("Pilot", 4.0)

    def disembark(self):
        self.animation_clip("Disembark", 2.4, actor_owned_motion=True)

    def pilot_mesh(self):
        path = BASE + "/Character/SK_AcornautPilot"
        source = ROOT / "ContentSource/Animation/PilotMesh.glb"
        manifest = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
        if hashlib.sha256(source.read_bytes()).hexdigest() != manifest["derivative_sha256"]:
            raise RuntimeError("Pilot mesh derivative differs from its reviewed manifest")
        if not self.library.does_asset_exist(path):
            source_module("ss_pilot_mesh_import", ROOT / "ContentSource/ImportPilotMesh.py").main()
        mesh = self.existing_authored(path, self.u.SkeletalMesh)
        original = self.required(BASE + "/Character/SK_Acornaut", self.u.SkeletalMesh)
        if mesh.get_editor_property("skeleton") != original.get_editor_property("skeleton"):
            raise RuntimeError("Pilot derivative does not share the original skeleton")
        if self.library.get_metadata_tag(mesh, "SSPilotMeshSourceSHA256") != manifest["derivative_sha256"]:
            raise RuntimeError("Pilot derivative requires a deliberate reviewed reimport")

    def data_asset(self):
        u = self.u
        path = BASE + "/Data/DA_Phase1"
        cls = u.load_class(None, "/Script/SpaceSurvival.SSPhase1Data")
        if not cls:
            raise RuntimeError("SSPhase1Data class unavailable. Build SpaceSurvivalEditor before authoring")
        if self.library.does_asset_exist(path):
            asset = self.existing_authored(path)
            if asset.get_class() != cls:
                raise RuntimeError("Existing DA_Phase1 has wrong class")
            return
        factory = u.DataAssetFactory()
        factory.set_editor_property("data_asset_class", cls)
        asset = self.tools.create_asset("DA_Phase1", BASE + "/Data", cls, factory)
        if not asset:
            raise RuntimeError("Could not create Phase 1 data asset from C++ defaults")
        self.save(asset)

    def world(self):
        u = self.u
        if self.library.does_asset_exist(MAP_PATH):
            existing = self.existing_authored(MAP_PATH, u.World)
            expected = u.load_class(None, "/Script/SpaceSurvival.SSGameMode")
            if existing.get_world_settings().get_editor_property("default_game_mode") != expected:
                raise RuntimeError("Existing Survival map GameMode differs from the runtime contract")
            return
        game_mode = u.load_class(None, "/Script/SpaceSurvival.SSGameMode")
        if not game_mode:
            raise RuntimeError("SSGameMode class unavailable. Build SpaceSurvivalEditor first")
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        if not levels.new_level(MAP_PATH):
            raise RuntimeError(f"Cannot create {MAP_PATH}")
        world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        world.get_world_settings().set_editor_property("default_game_mode", game_mode)
        start = actors.spawn_actor_from_class(u.PlayerStart, u.Vector(0, 0, 200))
        start.set_actor_label("InitialPlayerStart")
        # Presentation only; all gameplay/station actors remain runtime-owned.
        for label, mesh_path, scale, material in (
            ("DistantStarfield", BASE + "/Meshes/SM_Starfield", 1, None),
            ("DeepSpaceBackdrop", "/Engine/BasicShapes/Sphere", 100000, BASE + "/Materials/M_Space"),
        ):
            actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, 0))
            actor.set_actor_label(label)
            actor.set_editor_property("tags", [u.Name("SpaceStars" if label == "DistantStarfield" else "SpaceBackdrop")])
            component = actor.get_component_by_class(u.StaticMeshComponent)
            component.set_mobility(u.ComponentMobility.MOVABLE)
            component.set_static_mesh(self.required(mesh_path, u.StaticMesh))
            actor.set_actor_enable_collision(False)
            component.set_collision_profile_name("NoCollision")
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            component.set_editor_property("cast_shadow", False)
            actor.set_actor_scale3d(u.Vector(scale, scale, scale))
            if material:
                component.set_material(0, self.required(material, u.Material))
        for label, rotation, color, intensity in (
            ("SpaceKey", u.Rotator(pitch=-35, yaw=-40, roll=0), u.LinearColor(0.60, 0.77, 1, 1), 3.5),
            ("SpaceRim", u.Rotator(pitch=20, yaw=140, roll=0), u.LinearColor(1, 0.52, 0.24, 1), 1.2),
        ):
            light = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 500), rotation)
            light.set_actor_label(label)
            component = light.get_component_by_class(u.DirectionalLightComponent)
            component.set_mobility(u.ComponentMobility.MOVABLE)
            component.set_light_color(color)
            component.set_intensity(intensity)
            component.set_editor_property("forward_shading_priority", 2 if label == "SpaceKey" else 1)
        post = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0))
        post.set_actor_label("ReadableSpaceExposure")
        post.set_editor_property("unbound", True)
        settings = post.get_editor_property("settings")
        settings.set_editor_property("override_auto_exposure_min_brightness", True)
        settings.set_editor_property("override_auto_exposure_max_brightness", True)
        settings.set_editor_property("auto_exposure_min_brightness", 1.0)
        settings.set_editor_property("auto_exposure_max_brightness", 1.0)
        settings.set_editor_property("override_bloom_intensity", True)
        settings.set_editor_property("bloom_intensity", 0.35)
        post.set_editor_property("settings", settings)
        self.library.set_metadata_tag(world, "SSAuthoringVersion", "1")
        if not levels.save_current_level():
            raise RuntimeError("Persistent Survival map save failed")
        self.created.append(MAP_PATH)

    def run(self, assets_only=False):
        for directory in ("Materials", "Meshes", "Character", "Audio", "Maps", "Data", "Authoring"):
            self.library.make_directory(BASE + "/" + directory)
        self.stage("Materials", self.palette)
        self.stage("Cinematic space material", lambda: source_module("ss_space_panorama", ROOT / "Scripts/AuthorSpacePanorama.py").author())
        for item in self.mesh_manifest["assets"]:
            self.stage(item["name"], lambda asset=item: self.static_mesh(asset))
        self.stage("Preserved Acornaut import", self.hero)
        self.stage("Authored pilot animation", self.pilot)
        self.stage("Authored disembark animation", self.disembark)
        self.stage("Reviewed pilot mesh", self.pilot_mesh)
        for item in self.audio_manifest["assets"]:
            self.stage(item["name"], lambda asset=item: self.sound(asset))
        if not assets_only:
            self.stage("Phase1 DataAsset", self.data_asset)
            self.stage("Persistent map", self.world)
        self.stage("Source integrity", verify_hero)
        status = "ASSETS_IMPORTED_GAMEPLAY_CLASSES_PENDING" if assets_only else "IMPORTED_NOT_GAMEPLAY_VALIDATED"
        record = {"status": "FAILED" if self.errors else status,
                  "engine": self.u.SystemLibrary.get_engine_version(),
                  "source_glb_sha256": HERO_HASH, "saved_assets": sorted(set(self.created)),
                  "errors": self.errors,
                  "limits": "Import does not verify visual quality, character orientation, input, gameplay, or performance"}
        output = ROOT / "Saved" / "Validation" / "ContentImport.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        if self.errors:
            raise RuntimeError(f"Content authoring has {len(self.errors)} errors; see {output}")
        self.u.log("SpaceSurvival content imported. In-engine visual and gameplay validation remains required.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--assets-only", action="store_true", help="Import assets without requiring compiled gameplay classes or authoring the map")
    args, _ = parser.parse_known_args()
    if args.source_only:
        generate_sources()
        print("Source generation only. No Unreal assets imported or gameplay validation performed.")
        return
    meshes, audio = read_sources()
    try:
        import unreal
    except ImportError as error:
        raise RuntimeError("Unreal Python API unavailable. Run this script in Unreal Editor, or pass --source-only to generate source files") from error
    Author(unreal, meshes, audio).run(assets_only=args.assets_only)


if __name__ == "__main__":
    main()
