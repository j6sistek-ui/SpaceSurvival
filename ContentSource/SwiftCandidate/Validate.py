"""Fresh Blender/source validation for the separate Swift candidate."""
from pathlib import Path
import hashlib,importlib.util,json,math,struct
import bpy
from mathutils import Vector
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def obj_check(path):
 vertices=[];normals=[];uvs=[];faces=[];materials=set()
 for line in path.read_text(encoding="utf-8").splitlines():
  p=line.split()
  if not p:continue
  if p[0]=="v":vertices.append(tuple(map(float,p[1:])))
  elif p[0]=="vn":normals.append(tuple(map(float,p[1:])))
  elif p[0]=="vt":uvs.append(tuple(map(float,p[1:])))
  elif p[0]=="usemtl":materials.add(p[1])
  elif p[0]=="f":faces.append([tuple(map(int,v.split("/")))for v in p[1:]])
 assert vertices and normals and uvs and faces
 assert all(len(v)==3 and all(math.isfinite(n)for n in v)for v in vertices+normals)
 assert all(abs(sum(n*n for n in v)-1)<1e-5 for v in normals)
 assert all(len(v)==2 and all(math.isfinite(n)and -.00001<=n<=1.00001 for n in v)for v in uvs)
 bad=0
 for face in faces:
  assert len(face)==3
  for v,t,n in face:assert 1<=v<=len(vertices)and 1<=t<=len(uvs)and 1<=n<=len(normals)
  a,b,c=[Vector(vertices[x[0]-1])for x in face]
  if (b-a).cross(c-a).length*.5<=1e-8:bad+=1
 return {"vertices":len(vertices),"triangles":len(faces),"materials":sorted(materials),"finite_unit_normals":True,"finite_unit_square_uvs":True,"valid_references":True,"triangles_below_1e_8_cm2":bad,"bounds_cm":[[min(v[i]for v in vertices)for i in range(3)],[max(v[i]for v in vertices)for i in range(3)]]}
def glb_check(path):
 data=path.read_bytes();magic,version,total=struct.unpack_from("<4sII",data,0)
 assert magic==b"glTF"and version==2 and total==len(data)
 cursor=12;doc=None;binary=None
 while cursor<len(data):
  size,kind=struct.unpack_from("<II",data,cursor);cursor+=8
  chunk=data[cursor:cursor+size];cursor+=size
  if kind==0x4e4f534a:doc=json.loads(chunk)
  elif kind==0x004e4942:binary=chunk
 assert doc and binary and len(doc["meshes"])==1 and len(doc["meshes"][0]["primitives"])==7
 assert not doc.get("skins")and not doc.get("animations")and not doc.get("images")and not doc.get("textures")
 types={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}
 formats={5126:("f",4),5125:("I",4),5123:("H",2),5121:("B",1)}
 def accessor(index):
  acc=doc["accessors"][index];view=doc["bufferViews"][acc["bufferView"]]
  code,width=formats[acc["componentType"]];count=types[acc["type"]];stride=view.get("byteStride",width*count)
  start=view.get("byteOffset",0)+acc.get("byteOffset",0)
  return [struct.unpack_from("<"+code*count,binary,start+i*stride)for i in range(acc["count"])]
 tris=0;max_error=0
 for p in doc["meshes"][0]["primitives"]:
  assert p.get("mode",4)==4 and all(n in p["attributes"]for n in ("POSITION","NORMAL","TEXCOORD_0"))
  positions=accessor(p["attributes"]["POSITION"]);normals=accessor(p["attributes"]["NORMAL"]);uvs=accessor(p["attributes"]["TEXCOORD_0"]);indices=accessor(p["indices"])
  assert len(positions)==len(normals)==len(uvs)and len(indices)%3==0
  assert all(0<=v[0]<len(positions)for v in indices)
  assert all(math.isfinite(n)for v in positions+normals+uvs for n in v)
  error=max(abs(sum(n*n for n in v)-1)for v in normals);assert error<1e-5;max_error=max(max_error,error)
  tris+=len(indices)//3
 return {"one_mesh":True,"material_primitives":7,"triangles":tris,"skins_animations_images_textures":0,"finite_attributes":True,"maximum_squared_normal_length_error":max_error}
def main():
 report=json.loads((OUT/"Report.json").read_text())
 assert sha(OUT/"Generate.py")==report["generator_sha256"]
 for p,digest in report["protected_sha256"].items():assert sha(ROOT/p)==digest,p
 for f in report["outputs"]:assert sha(OUT/f["file"])==f["sha256"],f["file"]
 spec=importlib.util.spec_from_file_location("swift_source",OUT/"Generate.py");source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/"ContentSource/AcornShipCandidate/AcornShipCandidate.blend"))
 baseline={name:source.fingerprint(bpy.data.objects[name])for name in report["preserved_cockpit"]}
 assert len(baseline)==24 and baseline==report["preserved_cockpit"]
 bpy.ops.wm.open_mainfile(filepath=str(OUT/"SwiftCandidate.blend"))
 actual={name:source.fingerprint(bpy.data.objects[name])for name in baseline}
 assert actual==baseline,"Cockpit geometry/material/normal or transform mismatch"
 assets=[o for o in bpy.context.scene.objects if o.type in ("MESH","CURVE")]
 assert len(assets)==report["parts"]==85 and len(assets)-len(baseline)==61
 assert not any(o.type=="ARMATURE"for o in bpy.data.objects)
 deps=bpy.context.evaluated_depsgraph_get();new_body=[]
 for obj in assets:
  if obj.name in baseline:continue
  assert obj.name.startswith("Swift ")
  evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
  assert all(t.area>1e-12 for t in mesh.loop_triangles),"Degenerate new part "+obj.name
  assert all(all(math.isfinite(x)for x in v.co)for v in mesh.vertices)
  new_body.append({"name":obj.name,"triangles":len(mesh.loop_triangles)})
  evaluated.to_mesh_clear()
 assert all(name in baseline for name in report["joined_degenerate_by_part"]),"A new body export has degenerate faces"
 obj=obj_check(OUT/"SwiftCandidate.obj");glb=glb_check(OUT/"SwiftCandidate.glb")
 assert obj["triangles"]==glb["triangles"]==report["triangles"]
 assert all(abs(obj["bounds_cm"][e][i]-report["bounds_cm"][e][i])<.0001 for e in range(2)for i in range(3))
 result={"status":"SWIFT_FRESH_SOURCE_GEOMETRY_COCKPIT_EXPORT_CHECKS_PASS_NOT_UNREAL","blender":bpy.app.version_string,"generator_sha256":sha(OUT/"Generate.py"),"validator_sha256":sha(__file__),"report_sha256":sha(OUT/"Report.json"),"cockpit_parts_preserved":24,"cockpit_fingerprints":actual,"new_body_parts":new_body,"obj":obj,"glb":glb,"source_degenerate_export_triangles":report["degenerate_triangles"],"source_degenerate_export_by_part":report["joined_degenerate_by_part"],"protected_originals_unchanged":len(report["protected_sha256"]),"limits":["Only separate source; no Unreal build, import, new collision or gameplay selection.","Retained cockpit contains existing collapsed bevel triangles after join/world transform; exact authored parts are preserved and new body has no degenerate triangles.","No owner visual approval, complete animated clearance, runtime shader/LOD/performance or physical-input acceptance."]}
 (OUT/"Validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
 print("SWIFT_VALIDATION_PASS",json.dumps({"cockpit_parts":24,"new_parts":61,"triangles":obj["triangles"],"source_degeneracies_retained":report["degenerate_triangles"],"obj_degeneracies":obj["triangles_below_1e_8_cm2"]}))
if __name__=="__main__":main()
