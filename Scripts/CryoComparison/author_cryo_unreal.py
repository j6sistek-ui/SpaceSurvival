"""New-only CryoStage authoring; dry-run unless main(True) or --apply is explicit.

Run inside the owner's already installed Unreal editor, in the disposable
work/CryoStage project. This module never opens Unreal or the production project.
CRYO_MANIFEST / CRYO_RECEIPT may override the two input/output JSON paths.
The source OBJ coordinates are centimeters, Z-up, front -Y, already assembled.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import traceback


WORK = Path(__file__).resolve().parent
WORKSPACE = WORK.parent
STAGE = WORK / "CryoStage"
BASE = "/Game/SpaceSurvival/CryoComparison"
MAP = BASE + "/Maps/L_CryoComparison"
VERSION = "CryoComparison_20261021_v1"
DEFAULT_NIAGARA_SOURCE = "/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume"
ROLES = {"body", "glass", "frost", "console", "status", "holo", "mist", "trim", "housing"}
SHARED_KEYS = {"status", "console", "holo", "frost", "mist"}
X_OFFSETS = (-540.0, -180.0, 180.0, 540.0)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def token(value):
    result = re.sub(r"[^A-Za-z0-9_]", "_", str(value))
    require(result and not result[0].isdigit(), "Invalid asset identifier: " + str(value))
    return result


def glb_factors(path):
    """Preserve the source's single-material numeric PBR factors."""
    with Path(path).open("rb") as handle:
        header = handle.read(20)
        magic, version, _length, size, tag = struct.unpack("<4sIII4s", header)
        require(magic == b"glTF" and version == 2 and tag == b"JSON", "Expected GLB 2: " + str(path))
        doc = json.loads(handle.read(size))
    require(len(doc.get("materials", [])) == 1, "Expected exactly one source body material")
    mat = doc["materials"][0]
    pbr = mat.get("pbrMetallicRoughness", {})
    return {
        "base_color_factor": pbr.get("baseColorFactor", [1, 1, 1, 1]),
        "metallic_factor": pbr.get("metallicFactor", 1.0),
        "roughness_factor": pbr.get("roughnessFactor", 1.0),
        "double_sided": mat.get("doubleSided", False),
        "normal_scale": mat.get("normalTexture", {}).get("scale", 1.0),
    }


def prepare(manifest_path):
    raw = Path(manifest_path).read_bytes()
    manifest = json.loads(raw.decode("utf-8-sig"))
    require(set(manifest.get("shared", {})) >= SHARED_KEYS, "Missing shared texture paths")
    require(len(manifest.get("models", [])) == 4, "Exactly four assemblies required")
    sources = {}

    def source(value):
        path = Path(value)
        require(path.is_absolute() and path.is_file(), "Missing absolute source file: " + str(path))
        path = path.resolve()
        sources[str(path)] = {"bytes": path.stat().st_size, "sha256": digest(path)}
        return str(path)

    manifest["shared"] = {name: source(manifest["shared"][name]) for name in sorted(SHARED_KEYS)}
    identifiers = set()
    for model in manifest["models"]:
        model["id"] = token(model["id"])
        require(model["id"] not in identifiers, "Duplicate model ID")
        identifiers.add(model["id"])
        require(isinstance(model.get("label"), str) and model["label"].strip(), "Missing model label")
        model["source"] = source(model["source"])
        model["source_factors"] = glb_factors(model["source"])
        require(model["source_factors"]["normal_scale"] == 1.0, "Non-unit source normal scale requires explicit handling")
        model["height_cm"] = float(model["height_cm"])
        require(0 < model["height_cm"] <= 1000, "Implausible chamber height")
        require(set(model.get("textures", {})) >= {"base_color", "normal", "orm"}, "Missing body texture maps")
        model["textures"] = {key: source(model["textures"][key]) for key in ("base_color", "normal", "orm")}
        names = set()
        counts = Counter()
        for component in model.get("components", []):
            component["name"] = token(component["name"])
            require(component["name"] not in names, "Duplicate component name in " + model["id"])
            names.add(component["name"])
            require(component["role"] in ROLES, "Unknown component role")
            counts[component["role"]] += 1
            component["file"] = source(component["file"])
            require(Path(component["file"]).suffix.lower() == ".obj", "Only explicit centimeter OBJ import is supported")
        require(set(counts) == ROLES and counts["body"] == 1, "Each assembly needs one body and all eight finish roles")
        model["role_counts"] = dict(counts)
    return manifest, sources, hashlib.sha256(raw).hexdigest()


class Author:
    def __init__(self, unreal, manifest, manifest_hash, receipt):
        self.u = unreal
        self.manifest = manifest
        self.manifest_hash = manifest_hash
        self.receipt = receipt
        self.assets = unreal.EditorAssetLibrary
        self.tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.edit = unreal.MaterialEditingLibrary
        self.actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.created = []

    def metadata(self, asset, role, model_id="Shared", source_sha=""):
        require(asset.get_path_name().split(".")[0].startswith(BASE + "/"), "Refusing asset outside owned namespace")
        for key, value in {
            "CryoAuthoringVersion": VERSION,
            "CryoManifestSHA256": self.manifest_hash,
            "CryoRole": role,
            "CryoModelID": model_id,
            "CryoSourceSHA256": source_sha,
            "CryoAcceptance": "AUTHORED_PENDING_RENDER_AND_RUNTIME_VALIDATION",
        }.items():
            self.assets.set_metadata_tag(asset, key, str(value))

    def new_asset(self, name, folder, cls, factory, role, model_id="Shared"):
        path = folder + "/" + name
        require(path.startswith(BASE + "/") and not self.assets.does_asset_exist(path), "Refusing existing/out-of-scope asset: " + path)
        obj = self.tools.create_asset(name, folder, cls, factory)
        require(obj is not None, "Asset creation failed: " + path)
        self.created.append(obj)
        self.metadata(obj, role, model_id)
        return obj

    def import_texture(self, name, filename, kind, model_id="Shared"):
        u = self.u
        folder = BASE + "/Textures"
        expected = folder + "/" + name
        require(not self.assets.does_asset_exist(expected), "Texture already exists: " + expected)
        task = u.AssetImportTask()
        for key, value in {"filename": filename, "destination_path": folder, "destination_name": name,
                           "automated": True, "replace_existing": False, "save": False,
                           "factory": u.TextureFactory()}.items():
            task.set_editor_property(key, value)
        self.tools.import_asset_tasks([task])
        paths = list(task.get_editor_property("imported_object_paths"))
        require(len(paths) == 1, "Expected exactly one imported texture: " + filename)
        tex = self.assets.load_asset(paths[0])
        require(isinstance(tex, u.Texture2D) and tex.get_path_name().split(".")[0] == expected, "Unexpected texture output")
        tex.set_editor_property("srgb", kind == "color")
        tex.set_editor_property("compression_settings", {
            "color": u.TextureCompressionSettings.TC_DEFAULT,
            "normal": u.TextureCompressionSettings.TC_NORMALMAP,
            "mask": u.TextureCompressionSettings.TC_MASKS,
        }[kind])
        # glTF normals use OpenGL +Y. Unreal uses DirectX -Y tangent normals.
        if kind == "normal":
            tex.set_editor_property("flip_green_channel", True)
        tex.set_editor_property("never_stream", False)
        if model_id == "Shared":
            size = (2048, 1024) if "Console" in name else ((1024, 1024) if "Mist" in name else (1024, 2048))
            tex.set_editor_property("power_of_two_mode", u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
            tex.set_editor_property("resize_during_build_x", size[0])
            tex.set_editor_property("resize_during_build_y", size[1])
            tex.set_editor_property("mip_gen_settings", u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        self.metadata(tex, "Texture:" + kind, model_id, digest(filename))
        self.created.append(tex)
        self.receipt["textures"].append({"asset": expected, "source": filename, "kind": kind,
                                         "normal_green_flipped": kind == "normal", "streaming_enabled": True})
        return tex

    def node(self, mat, cls, **properties):
        obj = self.edit.create_material_expression(mat, getattr(self.u, cls))
        require(obj is not None, "Cannot create material expression: " + cls)
        for key, value in properties.items():
            obj.set_editor_property(key, value)
        return obj

    def wire(self, source, target, pin="", output=""):
        names = [str(name) for name in self.edit.get_material_expression_input_names(target)]
        actual = pin
        if actual not in names:
            if len(names) == 1:
                actual = names[0]
            elif pin == "UVs" and "Coordinates" in names:
                actual = "Coordinates"
        require(self.edit.connect_material_expressions(source, output, target, actual),
                "Material connection failed: " + str((target.get_class().get_name(), actual, names)))

    def prop(self, source, prop, output=""):
        require(self.edit.connect_material_property(source, output, getattr(self.u.MaterialProperty, prop)), "Material property connection failed: " + prop)

    def scalar(self, mat, value):
        return self.node(mat, "MaterialExpressionConstant", r=float(value))

    def color(self, mat, value):
        return self.node(mat, "MaterialExpressionConstant3Vector", constant=self.u.LinearColor(*value[:3], 1.0))

    def multiply(self, mat, a, b, a_output="", b_output=""):
        obj = self.node(mat, "MaterialExpressionMultiply")
        self.wire(a, obj, "A", a_output)
        self.wire(b if not isinstance(b, (int, float)) else self.scalar(mat, b), obj, "B", b_output)
        return obj

    def custom(self, mat, code, inputs):
        node = self.node(mat, "MaterialExpressionCustom", code=code,
                         output_type=self.u.CustomMaterialOutputType.CMOT_FLOAT1)
        pins = []
        for name in inputs:
            pin = self.u.CustomInput()
            pin.set_editor_property("input_name", name)
            pins.append(pin)
        node.set_editor_property("inputs", pins)
        for name, expression in inputs.items():
            self.wire(expression, node, name)
        return node

    def material(self, name, *, translucent=False, unlit=False, two_sided=False, model_id="Shared"):
        u = self.u
        mat = self.new_asset(name, BASE + "/Materials", u.Material, u.MaterialFactoryNew(), "Material", model_id)
        mat.set_editor_property("blend_mode", u.BlendMode.BLEND_TRANSLUCENT if translucent else u.BlendMode.BLEND_OPAQUE)
        mat.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT if unlit else u.MaterialShadingModel.MSM_DEFAULT_LIT)
        mat.set_editor_property("two_sided", two_sided)
        if translucent and not unlit:
            mat.set_editor_property("translucency_lighting_mode", u.TranslucencyLightingMode.TLM_SURFACE)
        return mat

    def sample(self, mat, tex, name, kind="color", uv=None):
        sampler = {"color": self.u.MaterialSamplerType.SAMPLERTYPE_COLOR,
                   "normal": self.u.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                   "mask": self.u.MaterialSamplerType.SAMPLERTYPE_MASKS}[kind]
        node = self.node(mat, "MaterialExpressionTextureSampleParameter2D", texture=tex,
                         parameter_name=name, sampler_type=sampler)
        if uv is not None:
            self.wire(uv, node, "UVs")
        return node

    def compile(self, mat):
        self.edit.layout_material_expressions(mat)
        errors = [str(value) for value in self.edit.recompile_material(mat)]
        self.receipt["materials"].append({"asset": mat.get_path_name(), "compile_errors": errors})
        require(not errors, "Material compile errors: " + str(errors))
        return mat

    def shared_materials(self):
        u = self.u
        textures = {key: self.import_texture("T_Cryo_" + key.title(), value,
                                             "mask" if key in ("mist", "frost") else "color")
                    for key, value in self.manifest["shared"].items()}
        result = {}
        glass = self.material("M_Glass", translucent=True, two_sided=True)
        self.prop(self.color(glass, (0.045, 0.12, 0.15)), "MP_BASE_COLOR")
        fresnel = self.node(glass, "MaterialExpressionFresnel", exponent=4.0, base_reflect_fraction=0.0)
        opacity = self.node(glass, "MaterialExpressionAdd", const_b=0.035)
        self.wire(self.multiply(glass, fresnel, 0.18), opacity, "A")
        self.prop(opacity, "MP_OPACITY")
        self.prop(self.scalar(glass, 0.10), "MP_ROUGHNESS")
        self.prop(self.scalar(glass, 0.45), "MP_SPECULAR")
        result["glass"] = self.compile(glass)

        frost = self.material("M_Frost", translucent=True, two_sided=True)
        sample = self.sample(frost, textures["frost"], "Frost", "mask")
        self.prop(self.color(frost, (0.55, 0.77, 0.84)), "MP_BASE_COLOR")
        self.prop(self.scalar(frost, 0.7), "MP_ROUGHNESS")
        self.prop(self.multiply(frost, sample, 0.40, "A"), "MP_OPACITY")
        self.prop(self.multiply(frost, sample, 0.13, "RGB"), "MP_EMISSIVE_COLOR")
        result["frost"] = self.compile(frost)

        for key in ("console", "status"):
            mat = self.material("M_" + key.title(), unlit=True)
            art = self.sample(mat, textures[key], "Artwork")
            self.prop(self.multiply(mat, art, 1.5, "RGB"), "MP_EMISSIVE_COLOR")
            result[key] = self.compile(mat)

        holo = self.material("M_Holo", translucent=True, unlit=True, two_sided=True)
        uv = self.node(holo, "MaterialExpressionTextureCoordinate", coordinate_index=0)
        clock = self.node(holo, "MaterialExpressionTime")
        art = self.sample(holo, textures["holo"], "Artwork", uv=uv)
        scan = self.custom(holo,
            "return (0.92+0.08*sin((UV.y*110.0-Clock*0.85)*6.2831853))*(0.96+0.04*sin(Clock*1.1));",
            {"UV": uv, "Clock": clock})
        self.prop(self.multiply(holo, self.multiply(holo, art, scan, "RGB"), 2.0), "MP_EMISSIVE_COLOR")
        self.prop(self.multiply(holo, self.multiply(holo, art, scan, "A"), 0.60), "MP_OPACITY")
        result["holo"] = self.compile(holo)

        mist = self.material("M_Mist", translucent=True, unlit=True, two_sided=True)
        uv = self.node(mist, "MaterialExpressionTextureCoordinate", coordinate_index=0)
        panner = self.node(mist, "MaterialExpressionPanner", speed_x=0.009, speed_y=0.018, fractional_part=True)
        self.wire(uv, panner, "Coordinate")
        art = self.sample(mist, textures["mist"], "Mist", "mask", panner)
        edge = self.custom(mist,
            "float2 e=min(UV,1.0-UV); return smoothstep(0.0,0.14,min(e.x,e.y));", {"UV": uv})
        # A quiet supplementary surface detail. Native local volumetric fog and
        # a simulated Niagara system provide the main cold-vapor effect.
        density = self.multiply(mist, self.multiply(mist, art, edge, "A"), 0.13)
        fade = self.node(mist, "MaterialExpressionDepthFade", fade_distance_default=12.0)
        self.wire(density, fade, "Opacity")
        self.prop(fade, "MP_OPACITY")
        self.prop(self.color(mist, (0.15, 0.36, 0.46)), "MP_EMISSIVE_COLOR")
        result["mist"] = self.compile(mist)

        trim = self.material("M_Trim", unlit=True)
        self.prop(self.color(trim, (0.08, 1.2, 1.7)), "MP_EMISSIVE_COLOR")
        result["trim"] = self.compile(trim)

        housing = self.material("M_Housing")
        self.prop(self.color(housing, (0.012, 0.022, 0.035)), "MP_BASE_COLOR")
        self.prop(self.scalar(housing, 0.6), "MP_METALLIC")
        self.prop(self.scalar(housing, 0.32), "MP_ROUGHNESS")
        result["housing"] = self.compile(housing)

        floor = self.material("M_StageFloor")
        self.prop(self.color(floor, (0.018, 0.025, 0.032)), "MP_BASE_COLOR")
        self.prop(self.scalar(floor, 0.35), "MP_ROUGHNESS")
        self.prop(self.scalar(floor, 0.5), "MP_METALLIC")
        result["floor"] = self.compile(floor)
        return result

    def body_material(self, model):
        tex = {key: self.import_texture("T_" + model["id"] + "_" + key,
                                       filename, "color" if key == "base_color" else "normal" if key == "normal" else "mask", model["id"])
               for key, filename in model["textures"].items()}
        factor = model["source_factors"]
        mat = self.material("M_" + model["id"] + "_Body", two_sided=factor["double_sided"], model_id=model["id"])
        color = self.sample(mat, tex["base_color"], "BaseColor")
        self.prop(self.multiply(mat, color, self.color(mat, factor["base_color_factor"]), "RGB"), "MP_BASE_COLOR")
        normal = self.sample(mat, tex["normal"], "Normal", "normal")
        self.prop(normal, "MP_NORMAL", "RGB")
        orm = self.sample(mat, tex["orm"], "ORM", "mask")
        self.prop(orm, "MP_AMBIENT_OCCLUSION", "R")
        rough = self.node(mat, "MaterialExpressionMax", const_b=0.25)
        self.wire(self.multiply(mat, orm, factor["roughness_factor"], "G"), rough, "A")
        self.prop(rough, "MP_ROUGHNESS")
        self.prop(self.multiply(mat, orm, 0.7 * factor["metallic_factor"], "B"), "MP_METALLIC")
        return self.compile(mat)

    def import_mesh(self, model, component, material):
        u = self.u
        folder = BASE + "/Meshes/" + model["id"]
        name = "SM_" + model["id"] + "_" + component["name"]
        expected = folder + "/" + name
        require(not self.assets.does_asset_exist(expected), "Mesh already exists")
        options = u.FbxImportUI()
        for key, value in {"automated_import_should_detect_type": False, "import_mesh": True,
                           "import_as_skeletal": False, "import_materials": False, "import_textures": False,
                           "mesh_type_to_import": u.FBXImportType.FBXIT_STATIC_MESH}.items():
            options.set_editor_property(key, value)
        data = options.get_editor_property("static_mesh_import_data")
        for key, value in {"combine_meshes": True, "auto_generate_collision": False,
                           "generate_lightmap_u_vs": False, "build_nanite": False,
                           "import_uniform_scale": 1.0, "convert_scene": False,
                           "convert_scene_unit": False, "force_front_x_axis": False,
                           "normal_import_method": u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
            data.set_editor_property(key, value)
        task = u.AssetImportTask()
        for key, value in {"filename": component["file"], "destination_path": folder, "destination_name": name,
                           "automated": True, "replace_existing": False, "save": False,
                           "options": options, "factory": u.FbxFactory()}.items():
            task.set_editor_property(key, value)
        self.tools.import_asset_tasks([task])
        paths = list(task.get_editor_property("imported_object_paths"))
        require(len(paths) == 1, "Expected one imported mesh for " + component["name"])
        mesh = self.assets.load_asset(paths[0])
        require(isinstance(mesh, u.StaticMesh) and mesh.get_path_name().split(".")[0] == expected, "Unexpected mesh import output")
        require(mesh.get_num_sections(0) == 1 and len(mesh.get_editor_property("static_materials")) == 1,
                "Each OBJ must have one material section: " + component["name"])
        mesh.set_material(0, material)
        editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        editor.remove_collisions(mesh)
        editor.enable_section_collision(mesh, False, 0, 0)
        self.metadata(mesh, component["role"], model["id"], digest(component["file"]))
        self.created.append(mesh)
        bounds = mesh.get_bounds()
        row = {"model_id": model["id"], "component": component["name"], "role": component["role"],
               "asset": expected, "source": component["file"], "material": material.get_path_name(),
               "bounds_origin_cm": list(bounds.origin.to_tuple()), "bounds_extent_cm": list(bounds.box_extent.to_tuple()),
               "lod_count": editor.get_lod_count(mesh), "sections_lod0": mesh.get_num_sections(0)}
        if component["role"] == "body":
            actual_height = float(bounds.box_extent.z) * 2.0
            row["height_cm"] = actual_height
            require(abs(actual_height - model["height_cm"]) <= max(2.0, model["height_cm"] * 0.03),
                    "OBJ axis/scale check failed for " + model["id"] + ": imported height " + str(actual_height))
        self.receipt["meshes"].append(row)
        return mesh

    def actor(self, cls, label, location, rotation=None, folder="CryoComparison"):
        u = self.u
        actor = self.actors.spawn_actor_from_class(cls, u.Vector(*location), rotation or u.Rotator())
        require(actor is not None, "Cannot spawn " + label)
        actor.set_actor_label(label)
        actor.set_folder_path(folder)
        actor.set_editor_property("tags", [u.Name("CryoComparison"), u.Name(VERSION)])
        self.receipt["actors"].append({"label": label, "class": actor.get_class().get_name(), "location_cm": list(location)})
        return actor

    def camera(self, label, position, target, fov):
        u = self.u
        delta = [target[i] - position[i] for i in range(3)]
        yaw = math.degrees(math.atan2(delta[1], delta[0]))
        pitch = math.degrees(math.atan2(delta[2], math.hypot(delta[0], delta[1])))
        actor = self.actor(u.CameraActor, label, position, u.Rotator(pitch=pitch, yaw=yaw), "CryoComparison/Cameras")
        component = actor.get_component_by_class(u.CameraComponent)
        component.set_field_of_view(fov)
        component.set_aspect_ratio(16.0 / 9.0 if label == "CAM_AllFour_Comparison" else 0.8)
        self.receipt["cameras"].append({"label": label, "location_cm": list(position), "look_at_cm": list(target), "horizontal_fov_degrees": fov})
        return actor

    def stage_lights(self, model_id, x):
        u = self.u
        for suffix, offset, intensity, color, rotation in (
                ("Key", (-115.0, -210.0, 275.0), 4500.0, (0.75, 0.88, 1.0), u.Rotator(pitch=-15, yaw=65)),
                ("Fill", (115.0, -130.0, 150.0), 1800.0, (0.2, 0.58, 0.9), u.Rotator(yaw=115))):
            light = self.actor(u.RectLight, model_id + "_" + suffix, (x + offset[0], offset[1], offset[2]), rotation, "CryoComparison/Lighting")
            comp = light.get_component_by_class(u.RectLightComponent)
            comp.set_mobility(u.ComponentMobility.MOVABLE)
            comp.set_intensity_units(u.LightUnits.LUMENS)
            comp.set_intensity(intensity)
            comp.set_light_color(u.LinearColor(*color, 1.0))
            comp.set_attenuation_radius(350.0)
            comp.set_source_width(100.0)
            comp.set_source_height(190.0)
            comp.set_cast_shadows(suffix == "Key")
        light = self.actor(u.PointLight, model_id + "_InteriorGlow", (x, 0.0, 260.0), folder="CryoComparison/Lighting")
        comp = light.get_component_by_class(u.PointLightComponent)
        comp.set_mobility(u.ComponentMobility.MOVABLE)
        comp.set_intensity_units(u.LightUnits.LUMENS)
        comp.set_intensity(350.0)
        comp.set_attenuation_radius(155.0)
        comp.set_light_color(u.LinearColor(0.15, 0.7, 1.0, 1.0))
        comp.set_cast_shadows(False)

    def native_fog(self):
        """Enable native volumetric scattering with almost no global haze."""
        u = self.u
        actor = self.actor(u.ExponentialHeightFog, "Cryo_NativeVolumetricFog", (0.0, 0.0, 0.0), folder="CryoComparison/NativeFX")
        fog = actor.get_component_by_class(u.ExponentialHeightFogComponent)
        require(fog is not None, "Native exponential fog component unavailable")
        fog.set_fog_density(0.00005)
        fog.set_fog_height_falloff(0.2)
        fog.set_volumetric_fog(True)
        fog.set_volumetric_fog_scattering_distribution(0.2)
        fog.set_volumetric_fog_extinction_scale(1.0)
        fog.set_volumetric_fog_albedo(u.Color(166, 217, 255, 255))
        fog.set_volumetric_fog_emissive(u.LinearColor(0.0, 0.0, 0.0, 1.0))
        fog.set_volumetric_fog_distance(2600.0)
        fog.set_volumetric_fog_start_distance(0.0)
        fog.set_volumetric_fog_near_fade_in_distance(10.0)
        self.receipt["native_fog"] = {"global_actor": actor.get_path_name(), "global_density": 0.00005,
            "volumetric_enabled": bool(fog.get_editor_property("enable_volumetric_fog")),
            "view_distance_cm": 2600.0, "locals": [],
            "shape_note": "UE5.8 LocalFogVolume uses uniform spheres: scene proxy replaces all axes with maximum scale; no ellipsoid claim."}
        require(self.receipt["native_fog"]["volumetric_enabled"], "Volumetric fog did not enable")

    def native_niagara_system(self, donor):
        """Make a new system copy; imported vendor donor packages remain intact."""
        u = self.u
        destination = BASE + "/FX/NS_CryoMist"
        require(not self.assets.does_asset_exist(destination), "Native mist system already exists")
        system = self.assets.duplicate_asset(donor.get_path_name(), destination)
        require(isinstance(system, u.NiagaraSystem), "Native Niagara system duplication failed")
        self.created.append(system)
        self.metadata(system, "NiagaraMist")
        # The standalone preview does not inherit the donor gallery's distance
        # culling policy. This changes the derivative only.
        system.set_editor_property("effect_type", None)
        emitters = list(u.NiagaraFunctionLibrary.get_all_emitters(system))
        require(emitters and any(info.get_editor_property("is_enabled") for info in emitters), "Native Niagara system has no enabled emitter")
        params = [{"name": str(p.get_editor_property("parameter_name")),
                   "type": str(p.get_editor_property("type_name")),
                   "bytes": int(p.get_editor_property("parameter_size_bytes"))}
                  for p in u.NiagaraFunctionLibrary.get_all_user_parameters(system)]
        self.receipt["niagara"] = {"source_system": donor.get_path_name(), "system": system.get_path_name(),
            "emitter_count": len(emitters), "user_parameters": params,
            "actors": [], "simulation_and_visual_validation": "PENDING_REAL_RHI_TICK_AND_CAPTURE"}
        return system

    def chamber_native_fx(self, model, x, system):
        u = self.u
        fog_actor = self.actor(u.LocalFogVolume, model["id"] + "_LocalColdFog", (x, 0.0, 72.0), folder="CryoComparison/NativeFX")
        # Installed LocalFogVolumeComponent::GetBaseVolumeSize() is 500cm.
        # Uniform .09 scale gives exactly a 45cm radius, not an ellipsoid.
        fog_actor.set_actor_scale3d(u.Vector(0.09, 0.09, 0.09))
        fog = fog_actor.get_component_by_class(u.LocalFogVolumeComponent)
        require(fog is not None, "Native LocalFogVolume component unavailable")
        fog.set_radial_fog_extinction(0.2)
        fog.set_height_fog_extinction(0.06)
        fog.set_height_fog_falloff(3.0)
        fog.set_height_fog_offset(-0.15)
        fog.set_fog_phase_g(0.2)
        fog.set_fog_start_distance(0.0)
        fog.set_fog_albedo(u.LinearColor(0.65, 0.85, 1.0, 1.0))
        fog.set_fog_emissive(u.LinearColor(0.0, 0.0, 0.0, 1.0))
        self.receipt["native_fog"]["locals"].append({"model_id": model["id"], "actor": fog_actor.get_path_name(),
            "center_cm": [x, 0.0, 72.0], "radius_cm": 45.0, "radial_density": 0.2,
            "height_density": 0.06, "height_falloff": 3.0, "height_offset": -0.15})
        actor = self.actor(u.NiagaraActor, model["id"] + "_NiagaraColdMist", (x, 0.0, 35.0), folder="CryoComparison/NativeFX")
        component = actor.get_component_by_class(u.NiagaraComponent)
        require(component is not None, "Native Niagara component unavailable")
        scale = float(os.environ.get("CRYO_NIAGARA_SCALE", "0.25"))
        require(0.01 <= scale <= 1.0, "Niagara preview scale must stay within .01..1")
        actor.set_actor_scale3d(u.Vector(scale, scale, scale))
        component.set_asset(system)
        component.set_auto_activate(True)
        component.set_cast_shadow(False)
        available = {p["name"]: p for p in self.receipt["niagara"]["user_parameters"]}
        applied = {}
        # Apply only parameters actually declared by the selected donor with the
        # expected native type. Probe records default values before authoring.
        for name, value in (("SpawnRate", 6.0), ("Sprite Size", 70.0)):
            if name in available and available[name]["bytes"] == 4 and "float" in available[name]["type"].lower():
                component.set_variable_float(name, value)
                actual, valid = component.get_variable_float(name)
                require(valid and abs(actual - value) < 0.001, "Niagara parameter readback failed: " + name)
                applied[name] = value
        color_name = "Smoke Color"
        if color_name in available and available[color_name]["bytes"] == 16:
            component.set_variable_linear_color(color_name, u.LinearColor(0.6, 0.8, 1.0, 0.12))
            applied[color_name] = [0.6, 0.8, 1.0, 0.12]
        component.activate(True)
        self.receipt["niagara"]["actors"].append({"model_id": model["id"], "actor": actor.get_path_name(),
            "position_cm": [x, 0.0, 35.0], "uniform_scale": scale, "applied_user_parameters": applied,
            "note": "Actor scale is not proof of bounded world-space particle motion; actual simulated plume fit remains to verify."})

    def build(self):
        u = self.u
        project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
        require(project == STAGE.resolve(), "This author may only run in the disposable CryoStage project: " + str(project))
        editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
        require(not editor.get_game_world(), "Stop PIE before authoring")
        registry = u.AssetRegistryHelpers.get_asset_registry()
        registry.search_all_assets(True)
        existing = list(registry.get_assets_by_path(BASE, recursive=True))
        require(not existing and not self.assets.does_asset_exist(MAP), "Namespace is not empty; inspect partial work instead of overwriting")
        donor_path = os.environ.get("CRYO_NIAGARA_SOURCE", DEFAULT_NIAGARA_SOURCE)
        donor = self.assets.load_asset(donor_path)
        require(isinstance(donor, u.NiagaraSystem), "Required native mist donor missing; copy verified dependency closure first: " + donor_path)
        world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
        require(world is not None, "Cannot create isolated blank comparison map")
        shared = self.shared_materials()
        self.native_fog()
        niagara = self.native_niagara_system(donor)
        for model, x in zip(self.manifest["models"], X_OFFSETS):
            body = self.body_material(model)
            for component in model["components"]:
                material = body if component["role"] == "body" else shared[component["role"]]
                mesh = self.import_mesh(model, component, material)
                actor = self.actor(u.StaticMeshActor, model["id"] + "_" + component["name"], (x, 0.0, 0.0), folder="CryoComparison/" + model["id"])
                # FbxFactory's OBJ parser negates Y unconditionally. Restore
                # the authored front -Y basis consistently for every component.
                actor.set_actor_scale3d(u.Vector(1.0, -1.0, 1.0))
                comp = actor.get_component_by_class(u.StaticMeshComponent)
                comp.set_static_mesh(mesh)
                comp.set_collision_profile_name("NoCollision")
                comp.set_cast_shadow(component["role"] == "body")
                if component["role"] in ("glass", "frost", "holo", "mist"):
                    comp.set_editor_property("translucency_sort_priority", {"mist": 0, "glass": 1, "frost": 2, "holo": 3}[component["role"]])
            self.stage_lights(model["id"], x)
            self.chamber_native_fx(model, x, niagara)
            label = self.actor(u.TextRenderActor, model["id"] + "_Label", (x, -175.0, 12.0), u.Rotator(yaw=-90), "CryoComparison/Labels")
            text = label.get_component_by_class(u.TextRenderComponent)
            text.set_text(model["id"] + " | " + model["label"])
            text.set_world_size(12.0)
            text.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
            text.set_text_render_color(u.Color(135, 220, 250, 255))
            text.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            self.camera("CAM_" + model["id"] + "_" + token(model["label"]), (x, -650.0, 180.0), (x, 0.0, model["height_cm"] * 0.5), 35.0)

        floor = self.actor(u.StaticMeshActor, "Comparison_DarkFloor", (0.0, 0.0, -6.0), folder="CryoComparison/Stage")
        floor.set_actor_scale3d(u.Vector(18.0, 12.0, 0.1))
        floor_comp = floor.get_component_by_class(u.StaticMeshComponent)
        floor_comp.set_static_mesh(self.assets.load_asset("/Engine/BasicShapes/Cube"))
        floor_comp.set_material(0, shared["floor"])
        floor_comp.set_collision_profile_name("BlockAll")
        self.camera("CAM_AllFour_Comparison", (0.0, -1600.0, 180.0), (0.0, 0.0, 160.0), 55.0)
        self.actor(u.PlayerStart, "CryoPreview_PlayerStart", (0.0, -1100.0, 180.0), u.Rotator(yaw=90), "CryoComparison/Stage")
        world.get_world_settings().set_editor_property("default_game_mode", u.GameModeBase)
        # Fixed manual exposure makes the four bays comparable and avoids an
        # auto-exposure response to each source's texture brightness.
        volume = self.actor(u.PostProcessVolume, "CryoPreview_Exposure", (0.0, 0.0, 0.0), folder="CryoComparison/Stage")
        volume.set_editor_property("unbound", True)
        settings = volume.get_editor_property("settings")
        for key, value in {"override_auto_exposure_method": True,
                           "auto_exposure_method": u.AutoExposureMethod.AEM_MANUAL,
                           "override_auto_exposure_bias": True, "auto_exposure_bias": 0.0,
                           "override_auto_exposure_apply_physical_camera_exposure": True,
                           "auto_exposure_apply_physical_camera_exposure": False,
                           "override_bloom_intensity": True, "bloom_intensity": 0.25,
                           "override_motion_blur_amount": True, "motion_blur_amount": 0.0}.items():
            settings.set_editor_property(key, value)
        volume.set_editor_property("settings", settings)
        for asset in self.created:
            require(asset.get_path_name().split(".")[0].startswith(BASE + "/"), "Out-of-scope save refused")
            require(self.assets.save_loaded_asset(asset, only_if_is_dirty=False), "Asset save failed: " + asset.get_path_name())
        require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "New comparison map save failed")
        self.receipt["saved_assets"] = sorted(asset.get_path_name() for asset in self.created)
        self.receipt["counts"] = {"models": len(self.manifest["models"]), "assets": len(self.created),
                                  "meshes": len(self.receipt["meshes"]), "textures": len(self.receipt["textures"]),
                                  "materials": len(self.receipt["materials"]), "actors": len(self.receipt["actors"]),
                                  "cameras": len(self.receipt["cameras"])}
        self.receipt["counts"].update(local_fog_volumes=len(self.receipt["native_fog"]["locals"]),
                                      niagara_actors=len(self.receipt["niagara"]["actors"]), niagara_systems=1)
        self.receipt["map"] = MAP
        self.receipt["engine"] = u.SystemLibrary.get_engine_version()


def main(apply=False, manifest_path=None, receipt_path=None):
    manifest_path = Path(manifest_path or os.environ.get("CRYO_MANIFEST", WORKSPACE / "outputs/Cryo_Comparison/assembly.json")).resolve()
    receipt_path = Path(receipt_path or os.environ.get("CRYO_RECEIPT", WORK / ("CryoUnrealAuthor.json" if apply else "CryoUnrealDryRun.json"))).resolve()
    require(receipt_path.is_relative_to(WORKSPACE), "Receipt must remain in this task workspace")
    receipt = {"version": VERSION, "utc": datetime.now(timezone.utc).isoformat(), "apply": bool(apply),
               "status": "FAILED", "manifest": str(manifest_path), "stage_project": str(STAGE),
               "namespace": BASE, "map": MAP, "meshes": [], "textures": [], "materials": [],
               "actors": [], "cameras": [], "errors": [], "limitations": [
                   "Authoring and native compile receipts are not visual or performance acceptance.",
                   "Native exponential volumetric fog, one bounded LocalFogVolume sphere and one Niagara system actor per chamber require real-RHI verification.",
                   "Low-opacity mist cards supplement native effects; Niagara donor motion and local/world-space scale require visual fitting.",
                   "Holo text is authored artwork with animated scan/pulse, not game telemetry.",
                   "Imported chambers have no collision; the comparison floor alone has BlockAll.",
                   "No production game map, settings, hero data, save or engine file is modified.",
                   "Native fresh-load, two-time appearance, translucency sorting and packaged runtime load remain to verify."]}
    sources = {}
    try:
        manifest, sources, manifest_hash = prepare(manifest_path)
        receipt["manifest_sha256"] = manifest_hash
        receipt["source_files"] = sources
        receipt["plan"] = [{"id": m["id"], "label": m["label"], "x_cm": x,
                            "height_cm": m["height_cm"], "role_counts": m["role_counts"],
                            "source_factors": m["source_factors"]} for m, x in zip(manifest["models"], X_OFFSETS)]
        receipt["shared_role_counts_identical"] = len({json.dumps(m["role_counts"], sort_keys=True) for m in manifest["models"]}) == 1
        require(receipt["shared_role_counts_identical"], "Shared finish component counts must match across all four versions")
        if not apply:
            receipt["status"] = "DRY_RUN_VALIDATED_NO_UNREAL_WRITES"
        else:
            import unreal
            Author(unreal, manifest, manifest_hash, receipt).build()
            changed = [path for path, row in sources.items() if digest(path) != row["sha256"]]
            require(not changed, "Source file changed during authoring: " + str(changed))
            receipt["source_hashes_unchanged"] = True
            receipt["status"] = "AUTHORED_SAVED_PENDING_RENDER_RUNTIME_AND_FRESH_LOAD"
    except Exception:
        receipt["errors"].append(traceback.format_exc())
    finally:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print("CRYO_AUTHOR_RESULT " + json.dumps({"status": receipt["status"], "receipt": str(receipt_path), "error_count": len(receipt["errors"])}), flush=True)
    if receipt["errors"]:
        raise RuntimeError("Cryo authoring failed; inspect " + str(receipt_path))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Explicitly create new native assets in CryoStage")
    parser.add_argument("--manifest")
    parser.add_argument("--receipt")
    args, _unknown = parser.parse_known_args()
    main(args.apply, args.manifest, args.receipt)
