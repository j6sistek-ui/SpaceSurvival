"""Four editable static Acornaut cabinet assets; no game or HUD wiring."""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from finish_cabinets import OUT,TEXTURES,material,cube,tube,panel,cylinder,configure_render


def main():
    if (OUT.parent / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    for mode in ("Normal","DebrisField","Arcade","HyperRun"):
        name="Acornaut"+mode
        bpy.ops.wm.open_mainfile(filepath=str(OUT/"AsteroidArena/AsteroidArena.blend"))
        for obj in list(bpy.context.scene.objects):
            if obj.type!="MESH": bpy.data.objects.remove(obj,do_unlink=True)
        for mat in bpy.data.materials:
            if mat.name.startswith("M_Asteroid"):
                if "Display" in mat.name: texture="Screen"
                elif "Marquee" in mat.name: texture="Title"
                elif "Badge" in mat.name: texture="Badge"
                elif "Paint" in mat.name: texture="Paint"
                else: continue
                mat.name="M_"+name+"_"+texture
                for node in mat.node_tree.nodes:
                    if node.type=="TEX_IMAGE": node.image=bpy.data.images.load(str(TEXTURES/(name+"_"+texture+".png")),check_existing=True)
        graphite=bpy.data.materials.get("M_Graphite")
        accent=bpy.data.materials.get("M_"+name+"_Paint")
        metal=bpy.data.materials.get("M_Titanium")
        side=material("M_"+name+"_Side",name+"_Side",metallic=.12,roughness=.46)
        for sign in (-1,1):
            x=sign*.531
            points=[(x,.07,.57),(x,.40,.57),(x,.40,1.47),(x,.07,1.47)]
            if sign<0: points=[points[1],points[0],points[3],points[2]]
            panel(name+"_SideBadge",points,side,graphite)
        if mode=="DebrisField":
            brass=material("M_DebrisProtectiveMetal","Graphite",metallic=.8,roughness=.58)
            for x in (-.50,.50):
                for z in (.16,.63,1.69):
                    cube("IndustrialCornerGuard",(x,-.07 if z>1.5 else -.385,z),(.10,.14 if z>1.5 else .22,.20),brass,.016)
            for x in (-.36,.36):
                for z in (.20,.59,1.72):
                    bolt=cylinder("ArmoredFastener",(x,-.112 if z>1.5 else -.459,z),.011,.012,metal,6)
                    bolt.rotation_euler.x=math.pi/2
        if mode=="Arcade":
            for x in (-.54,.54):
                cube("RetroSideColumn",(x,.452,.99),(.065,.05,1.82),accent,.027)
        if mode=="HyperRun":
            # A wider seated silhouette, preserving a separate editable chair assembly.
            for obj in [o for o in bpy.context.scene.objects if o.type=="MESH"]:
                for v in obj.data.vertices:
                    co=obj.matrix_world@v.co
                    v.co=(co.x*1.28,co.y,co.z*.84)
                obj.matrix_world.identity()
            cube("FlightCabinetPlatform",(0,-.53,.07),(1.40,2.05,.14),graphite,.06)
            cube("SeatPedestal",(0,-1.20,.24),(.60,.55,.25),graphite,.055)
            cube("SeatCushion",(0,-1.16,.46),(.60,.56,.17),graphite,.07)
            seat=cube("SeatBack",(0,-1.43,.83),(.62,.145,.83),graphite,.065)
            seat.rotation_euler.x=math.radians(-8)
            for x in (-.32,.32):
                tube("SeatEdgePiping",[(x,-1.37,.51),(x,-1.47,1.05),(x*.73,-1.49,1.22)],.014,accent)
                cube("FlightArmrest",(x,-1.14,.70),(.11,.49,.10),graphite,.04)
            for z in (.60,.69,.78,.87,.96,1.05):
                cube("SeatUpholsteryChannel",(0,-1.345,z),(.47,.022,.014),accent,.005)
            rearplate=material("M_HyperRun_SeatBadge",name+"_Badge",metallic=.2,roughness=.4)
            panel("HyperRunSeatBadge",[(-.17,-1.523,.83),(.17,-1.523,.83),(.17,-1.523,1.17),(-.17,-1.523,1.17)],rearplate)
        target=OUT/name
        target.mkdir(parents=True,exist_ok=True)
        objects=[o for o in bpy.context.scene.objects if o.type in {"MESH","CURVE"}]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects: obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.convert(target="MESH")
        for image in bpy.data.images:
            if image.source=="FILE": image.pack()
        bpy.ops.wm.save_as_mainfile(filepath=str(target/(name+".blend")))
        materials=[]
        used={m.name:m for obj in objects for m in obj.data.materials}
        for key,mat in sorted(used.items()):
            shader=mat.node_tree.nodes.get("Principled BSDF")
            imgs=[n.image for n in mat.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
            materials.append({"slot":key,"base_color_texture":str(Path(bpy.path.abspath(imgs[0].filepath))) if imgs else None,"base_color_linear":list(shader.inputs["Base Color"].default_value),"metallic":shader.inputs["Metallic"].default_value,"roughness":shader.inputs["Roughness"].default_value,"emission_strength":shader.inputs["Emission Strength"].default_value,"emission_color_linear":list(shader.inputs["Emission Color"].default_value),"emission_uses_base_texture":shader.inputs["Emission Color"].is_linked,"alpha":1.0})
        vv=[obj.matrix_world@v.co for obj in objects for v in obj.data.vertices]
        bounds=[[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]]
        bpy.ops.object.join()
        bpy.context.object.name="SM_"+name
        bpy.context.scene.cursor.location=(0,0,0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        bpy.ops.export_scene.gltf(filepath=str(target/(name+".glb")),export_format="GLB",use_selection=True)
        bpy.ops.export_scene.fbx(filepath=str(target/(name+".fbx")),use_selection=True,object_types={"MESH"},axis_forward="-Z",axis_up="Y",path_mode="COPY",embed_textures=True)
        report={"name":name,"mode":mode,"geometry_provenance":"Locally generated Hunyuan chassis with authored hard surface finishing and variant additions","texture_provenance":"Existing owner Acornaut art with HUD cropped out; static local attract composition","dimensions_m":[bounds[1][i]-bounds[0][i] for i in range(3)],"bounds_m":bounds,"materials":materials,"fbx_path":str(target/(name+".fbx")),"final_triangles":sum(len(p.vertices)-2 for p in bpy.context.object.data.polygons),"front_axis":"-Y in Blender","origin":"cabinet ground center; HyperRun platform extends forward -Y","status":"static decorative asset; no game wiring","collision_recommendation":"simple exterior convex boxes; chair/console clearance needs station placement review"}
        (target/"asset.json").write_text(json.dumps(report,indent=2))
        configure_render(bpy.context.scene,name,report["dimensions_m"][2])
        print(json.dumps({"name":name,"triangles":report["final_triangles"]}))


if __name__=="__main__": main()
