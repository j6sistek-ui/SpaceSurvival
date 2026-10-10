"""Write a GLB's PBR set as PNGs for Scripts/ImportCrewMaterial.py: T_<Name>_BaseColor (sRGB), T_<Name>_Normal
(as delivered: glTF is OpenGL +Y, so the Unreal import flips green), T_<Name>_Roughness (ORM green) and
T_<Name>_Metallic (ORM blue) as greyscale. Emission is written too when the map is not black.

  blender -b --factory-startup -P export_glb_textures.py -- <in.glb> <outdir> <Name>
"""
import os
import sys

import bpy
import numpy as np

GLB, OUT, NAME = sys.argv[-3], sys.argv[-2], sys.argv[-1]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=GLB)
m = next(o for o in bpy.data.objects if o.type == 'MESH'); mat = m.data.materials[0]
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def image_of(inp):
    if not bsdf.inputs[inp].links:
        return None
    n = bsdf.inputs[inp].links[0].from_node
    while n.type != 'TEX_IMAGE':
        n = next(i for i in n.inputs if i.is_linked).links[0].from_node
    return n.image


def pixels(img):
    w, h = img.size; px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); return px.reshape(h, w, 4)


def save(px, name):
    h, w = px.shape[:2]; out = bpy.data.images.new(name, w, h, alpha=False); out.colorspace_settings.name = 'Non-Color'
    px = px.copy(); px[..., 3] = 1.0; out.pixels.foreach_set(px.ravel()); out.file_format = 'PNG'
    out.filepath_raw = os.path.join(OUT, name + ".png"); out.save()
    print("TEX| wrote %s %dx%d mean %.3f" % (name, w, h, float(px[..., :3].mean())))


base, normal, orm, emis = image_of("Base Color"), image_of("Normal"), image_of("Metallic"), image_of("Emission Color")
save(pixels(base), "T_%s_BaseColor" % NAME); save(pixels(normal), "T_%s_Normal" % NAME)
o = pixels(orm)
for ch, what in ((1, "Roughness"), (2, "Metallic")):
    g = o[..., ch]; save(np.stack([g, g, g, g], -1), "T_%s_%s" % (NAME, what))
if emis is not None:
    e = pixels(emis)
    if e[..., :3].max() > 0.05:
        save(e, "T_%s_Emissive" % NAME)
    else:
        print("TEX| emissive map is black (max %.3f), skipped" % float(e[..., :3].max()))
