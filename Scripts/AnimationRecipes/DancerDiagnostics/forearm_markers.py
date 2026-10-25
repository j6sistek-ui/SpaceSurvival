"""Removable, bone-following palmar forearm arrows for review copies only."""
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

COLLECTION = 'REVIEW_ONLY_ForearmArrows'

def remove():
    coll = bpy.data.collections.get(COLLECTION)
    if coll:
        meshes = [obj.data for obj in coll.objects if obj.type == 'MESH']
        materials = {mat for mesh in meshes for mat in mesh.materials if mat}
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)
        for mesh in meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for material in materials:
            if material.users == 0 and material.name.startswith('REVIEW_ONLY_'):
                bpy.data.materials.remove(material)

def add(rig):
    remove()
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)
    material = bpy.data.materials.new('REVIEW_ONLY_CyanForearmArrow')
    material.diffuse_color = (0.01, 0.9, 1.0, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = material.diffuse_color
    bsdf.inputs['Roughness'].default_value = 0.7
    bsdf.inputs['Emission Color'].default_value = material.diffuse_color
    bsdf.inputs['Emission Strength'].default_value = 0.5
    records = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    surfaces = [(ob, BVHTree.FromObject(ob, depsgraph)) for ob in bpy.data.objects
                if ob.type == 'MESH' and ob.visible_get() and not ob.hide_render]
    for side in ('l', 'r'):
        bone = rig.data.bones['lowerarm_' + side]
        def rest(name):
            return (rig.matrix_world @ rig.data.bones[name].matrix_local).translation
        elbow, wrist = rest(bone.name), rest('hand_' + side)
        axis = (wrist - elbow).normalized()
        finger = rest('middle_01_' + side) - wrist
        width = rest('index_01_' + side) - rest('pinky_01_' + side)
        normal = finger.cross(width).normalized() * (1 if side == 'l' else -1)
        normal = (normal - axis * normal.dot(axis)).normalized()
        across = axis.cross(normal).normalized()
        # A tiny curved surface rather than a camera-facing sprite. The arrowhead
        # points distally; vertices are expressed in the real forearm bone frame.
        center = elbow.lerp(wrist, 0.66)
        outline = [(-.022, -.004), (.007, -.004), (.007, -.010),
                   (.024, 0), (.007, .010), (.007, .004), (-.022, .004)]
        world = []
        for x,y in outline:
            p = center + axis*x + across*y
            hits = []
            for ob, tree in surfaces:
                inverse = ob.matrix_world.inverted()
                origin = inverse @ (p + normal*.15)
                direction = (inverse.to_3x3() @ -normal).normalized()
                hit, _, _, _ = tree.ray_cast(origin, direction)
                if hit is not None:
                    hit = ob.matrix_world @ hit
                    distance = (hit-p).dot(normal)
                    if 0 < distance < .08: hits.append((distance, hit))
            hit = max(hits, key=lambda v:v[0])[1] if hits else p+normal*.028
            world.append(hit + normal*.001)
        verts = [rig.matrix_world.inverted() @ p for p in world]
        mesh = bpy.data.meshes.new('REVIEW_ONLY_ForearmArrow_' + side)
        mesh.from_pydata(verts, [], [list(range(len(verts)))])
        mesh.materials.append(material)
        obj = bpy.data.objects.new(mesh.name, mesh)
        coll.objects.link(obj)
        obj['review_only'] = True
        obj['meaning'] = 'Palmar forearm surface; arrow points toward wrist'
        obj.matrix_world = rig.matrix_world.copy()
        group = obj.vertex_groups.new(name=bone.name)
        group.add(list(range(len(verts))), 1.0, 'REPLACE')
        follow = obj.modifiers.new('FollowForearm', 'ARMATURE')
        follow.object = rig
        solid = obj.modifiers.new('ThinReviewMark', 'SOLIDIFY')
        solid.thickness = .001
        # Rig FBX scale may be .01. Local dimensions already account for that.
        solid.thickness /= max(rig.matrix_world.to_scale())
        records.append({'bone':bone.name, 'palmar_normal_world':list(normal),
                        'direction_world':list(axis), 'vertices_armature_space':[list(v) for v in verts]})
    return records
