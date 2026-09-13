"""Blender background authoring: separate seated pilot animation, original GLB unchanged.

Uses the supplied skeleton and a sampled walk pose as rig reference, then authors
seated hip/knee, forward hand-control and restrained breathing/head motion keys.
Run with existing Blender --background --factory-startup --python <this file>.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "model-rigged.glb"
EXPECTED = "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"
OUT = ROOT / "ContentSource/Animation"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    scene = bpy.context.scene
    scene.frame_set(1)
    base = {bone.name: bone.matrix.copy() for bone in rig.pose.bones}
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.rotation_mode = "QUATERNION"
        bone.matrix = base[bone.name]
    bpy.context.view_layer.update()

    def aim(name, child, direction):
        bone = rig.pose.bones[name]
        vector = rig.pose.bones[child].head - bone.head
        desired = Vector(direction).normalized()
        delta = vector.normalized().rotation_difference(desired)
        matrix = delta.to_matrix().to_4x4() @ bone.matrix
        matrix.translation = bone.head
        bone.matrix = matrix
        bpy.context.view_layer.update()

    aim("Pelvis", "Spine1", (0,.08,1))
    pelvis = rig.pose.bones["Pelvis"]
    matrix = pelvis.matrix.copy()
    matrix.translation = Vector((0,0,0))
    pelvis.matrix = matrix
    bpy.context.view_layer.update()
    for name, child in (("Spine1","Spine2"),("Spine2","Spine3"),("Spine3","Neck"),("Neck","Head")):
        aim(name,child,(0,-.08,1))
    for side, sign in (("L",1),("R",-1)):
        aim(side+"_Hip",side+"_Knee",(sign*.08,-1,-.08))
        aim(side+"_Knee",side+"_Ankle",(0,-.08,-1))
        aim(side+"_Ankle",side+"_Foot",(0,-1,-.1))
        aim(side+"_Shoulder",side+"_Elbow",(sign*.15,-.35,-1))
        aim(side+"_Elbow",side+"_Wrist",(0,-1,.15))
        aim(side+"_Wrist",side+"_Middle1",(0,-1,-.1))
    pose = {bone.name: (bone.location.copy(),bone.rotation_quaternion.copy(),bone.scale.copy()) for bone in rig.pose.bones}
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, 121
    for frame in range(1,122):
        phase = (frame-1)/120*math.tau
        for bone in rig.pose.bones:
            location, rotation, scale = pose[bone.name]
            bone.location, bone.rotation_quaternion, bone.scale = location, rotation, scale
            if bone.name in ("Spine2","Spine3"):
                bone.rotation_quaternion = rotation @ Quaternion((1,0,0),math.sin(phase)*.008)
            elif bone.name == "Head":
                bone.rotation_quaternion = rotation @ Quaternion((0,1,0),math.sin(phase)*.017)
            elif bone.name in ("L_Elbow","R_Elbow"):
                bone.rotation_quaternion = rotation @ Quaternion((1,0,0),math.sin(phase)*.006)
            for field in ("location","rotation_quaternion","scale"):
                bone.keyframe_insert(data_path=field,frame=frame,group=bone.name)
    rig.animation_data.action.name = "Pilot"
    scene.frame_set(1)
    OUT.mkdir(parents=True,exist_ok=True)
    # Retain the original glTF joint basis. FBX round-tripping introduces a
    # different bone-axis/unit convention against the already imported skeleton.
    raw = SOURCE.read_bytes()
    json_size = struct.unpack_from("<I",raw,12)[0]
    document = json.loads(raw[20:20+json_size])
    bin_start = 20+json_size+8
    binary = bytearray(raw[bin_start:])
    node_index = {node.get("name"):i for i,node in enumerate(document["nodes"])}
    samples = {bone.name:{"translation":[],"rotation":[],"scale":[]} for bone in rig.pose.bones}
    conversion = Matrix.Rotation(math.pi/2,4,"X")
    inverse_conversion = conversion.inverted()
    for frame in range(1,122):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        joints = {bone.name:bone.matrix @ bone.bone.matrix_local.inverted() @ Matrix.Translation(bone.bone.head_local)
                  for bone in rig.pose.bones}
        for bone in rig.pose.bones:
            local = joints[bone.parent.name].inverted() @ joints[bone.name] if bone.parent else joints[bone.name]
            location,rotation,scale = (inverse_conversion @ local @ conversion).decompose()
            samples[bone.name]["translation"].extend(location)
            samples[bone.name]["rotation"].extend((rotation.x,rotation.y,rotation.z,rotation.w))
            samples[bone.name]["scale"].extend(scale)

    def accessor(values,kind,minimum=None,maximum=None):
        while len(binary)%4:
            binary.append(0)
        offset = len(binary)
        payload = struct.pack("<"+"f"*len(values),*values)
        binary.extend(payload)
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(payload)})
        data = {"bufferView":view,"componentType":5126,"count":121,"type":kind}
        if minimum is not None:
            data["min"],data["max"] = minimum,maximum
        index = len(document["accessors"])
        document["accessors"].append(data)
        return index
    times = accessor([i/30 for i in range(121)],"SCALAR",[0],[4])
    clip = {"name":"A_Pilot","channels":[],"samplers":[]}
    for name,tracks in samples.items():
        for path,values in tracks.items():
            output_accessor = accessor(values,"VEC4" if path=="rotation" else "VEC3")
            sampler = len(clip["samplers"])
            clip["samplers"].append({"input":times,"output":output_accessor,"interpolation":"LINEAR"})
            clip["channels"].append({"sampler":sampler,"target":{"node":node_index[name],"path":path}})
    document["animations"] = [clip]
    document["buffers"][0]["byteLength"] = len(binary)
    encoded = json.dumps(document,separators=(",",":")).encode("utf-8")
    encoded += b" "*((-len(encoded))%4)
    binary.extend(b"\0"*((-len(binary))%4))
    output = OUT / "Pilot.glb"
    output.write_bytes(struct.pack("<III",0x46546C67,2,12+8+len(encoded)+8+len(binary))
                       +struct.pack("<II",len(encoded),0x4E4F534A)+encoded
                       +struct.pack("<II",len(binary),0x004E4942)+binary)
    record = {"status":"AUTHORED_PILOT_SOURCE_REQUIRES_ENGINE_POSE_REVIEW","seconds":4,"fps":30,
              "source_glb_sha256":EXPECTED,"animation_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
              "bones":len(rig.pose.bones),"seat_anchor":"Pelvis at source origin; +Z up, -Y forward in Blender",
              "transport":"Original glTF nodes/mesh/inverse binds copied unchanged; only new animation channels authored. Import animations only.",
              "notes":"Separate derived animation; source GLB unchanged. Existing Unreal skeleton and mesh must not be replaced."}
    (OUT/"Pilot.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    print("Authored separate pilot animation:",output)


if __name__=="__main__":
    main()
