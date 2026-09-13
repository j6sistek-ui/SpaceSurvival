"""Read-only checks of actual generated OBJ data; no Blender/Unreal/rendering."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report=json.loads((OUT/"SourceReport.json").read_text(encoding="utf-8"))
    for path,digest in report["protected_sha256"].items():
        assert sha(ROOT/path)==digest,"Protected input changed: "+path
    assert sha(OUT/"Generate.py")==report["generator_sha256"]
    assert sha(OUT/"FieldPalette.mtl")==report["palette_sha256"]
    for path,digest in report["shader_sha256"].items():
        assert sha(OUT/path)==digest,"Shader changed after receipt"
    historical=report["historical_runtime_git"]
    for path,digest in historical["sha256"].items():
        assert hashlib.sha256(subprocess.check_output(["git","show",historical["base"]+":"+path],cwd=ROOT)).hexdigest()==digest
    previous=json.loads((OUT.parent/"SourceReport.json").read_text(encoding="utf-8"))
    records=[]
    for item,prior in zip(report["meshes"],previous["meshes"]):
        assert item["name"]==prior["name"]+"V2"
        assert len(item["paths"])==len(prior["paths"])
        assert all(abs(a["half_width_cm"]/b["half_width_cm"]-.3)<1e-9 for a,b in zip(item["paths"],prior["paths"]))
        for output in item["outputs"]:
            assert sha(OUT/output["file"])==output["sha256"]
        vertices,uvs,faces,normals,materials=[],[],[],[],set()
        for line in (OUT/(item["name"]+".obj")).read_text(encoding="utf-8").splitlines():
            words=line.split()
            if not words:continue
            if words[0]=="v":vertices.append(tuple(map(float,words[1:])))
            elif words[0]=="vt":uvs.append(tuple(map(float,words[1:])))
            elif words[0]=="vn":normals.append(tuple(map(float,words[1:])))
            elif words[0]=="usemtl":materials.add(words[1])
            elif words[0]=="f":faces.append([tuple(int(x)-1 for x in word.split("/")) for word in words[1:]])
        assert len(vertices)==item["vertices"]
        assert len(faces)==item["triangles"] <= 5000 and materials=={item["material"]}
        assert all(math.isfinite(x) for data in (vertices,uvs,normals) for row in data for x in row)
        assert max(math.sqrt(sum(x*x for x in v)) for v in vertices) <=100.000001
        for axis in range(3):
            assert abs(min(v[axis] for v in vertices)+100)<.000001
            assert abs(max(v[axis] for v in vertices)-100)<.000001
        roles=set()
        min_area=float("inf")
        for face in faces:
            assert len(face)==3
            for v,t,n in face:
                assert 0<=v<len(vertices) and 0<=t<len(uvs) and 0<=n<len(normals)
                assert abs(sum(x*x for x in normals[n])-1)<1e-6
            role={math.floor(uvs[t][0]/4+1e-5) for _,t,_ in face}
            assert len(role)==1 and role.issubset({0,1,2}),"A triangle crosses shader roles"
            roles.update(role)
            a,b,c=[vertices[v] for v,_,_ in face]
            ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
            cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
            area=math.sqrt(sum(x*x for x in cross))*.5
            assert area>1e-8,"Degenerate imported triangle"
            min_area=min(min_area,area)
        assert roles==({0,1,2} if "Electrical" in item["name"] else {0,1})
        boundary=[vertices[v] for face in faces if math.floor(uvs[face[0][1]][0]/4+1e-5)==0 for v,_,_ in face]
        assert min(math.sqrt(sum(x*x for x in v)) for v in boundary)>99.7,"Boundary enters the effect interior"
        records.append({"name":item["name"],"triangles":len(faces),"roles":sorted(roles),"minimum_area_cm2":min_area,
                        "radius_cm":100,"sections":len(materials)})
    print("FIELD_SOURCE_CHECK_PASS",json.dumps({"meshes":records,"protected_hashes":len(report["protected_sha256"]),
          "limits":"Actual OBJ geometry/UV/normal/provenance checks only; Unreal import/rendering is outside this source check."}))


if __name__=="__main__":
    main()
