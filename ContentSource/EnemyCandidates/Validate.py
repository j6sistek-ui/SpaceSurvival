"""Read-only candidate mesh inspection, writing only Validation.json beside this file."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def inspect(name):
    points, normals, uvs, faces, mats = [], [], [], [], set()
    material = None
    for line in (OUT/(name+".obj")).read_text(encoding="utf-8").splitlines():
        word = line.split()
        if not word:
            continue
        if word[0] == "v":
            points.append(tuple(map(float, word[1:])))
        elif word[0] == "vn":
            normals.append(tuple(map(float, word[1:])))
        elif word[0] == "vt":
            uvs.append(tuple(map(float, word[1:])))
        elif word[0] == "usemtl":
            material = word[1]
            mats.add(material)
        elif word[0] == "f":
            assert len(word) == 4 and material
            face = [tuple(int(n)-1 for n in item.split("/")) for item in word[1:]]
            faces.append(face)
    assert 8000 <= len(faces) <= 20000
    assert len(mats) == 4
    assert all(math.isfinite(n) for row in points+normals+uvs for n in row)
    assert all(abs(dot(n, n)-1) < .000001 for n in normals)
    assert all(-.000001 <= n <= 1.000001 for uv in uvs for n in uv)
    edges = Counter()
    min_area, min_uv_area, min_dot = math.inf, math.inf, 1
    parent = list(range(len(points)))
    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)] = min(a,b)
    for face in faces:
        assert all(0 <= p < len(points) and 0 <= u < len(uvs) and 0 <= n < len(normals) for p,u,n in face)
        a,b,c = [points[p] for p,_,_ in face]
        normal = cross(sub(b,a), sub(c,a))
        area = math.sqrt(dot(normal,normal))/2
        assert area > 1e-8, (name, "degenerate triangle", face)
        min_area = min(min_area,area)
        uv = [uvs[u] for _,u,_ in face]
        uv_area = abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-
                      (uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]))/2
        assert uv_area > 1e-14, (name,"degenerate UV triangle",face)
        min_uv_area = min(min_uv_area,uv_area)
        for _,_,n in face:
            cos = dot(normal,normals[n])/(area*2)
            assert cos > -.0001, (name,"opposed corner normal",cos)
            min_dot = min(min_dot,cos)
        for i in range(3):
            p,q=face[i][0],face[(i+1)%3][0]
            edges[tuple(sorted((p,q)))] += 1
            union(p,q)
    assert all(count==2 for count in edges.values()),(name,"open or nonmanifold edges",Counter(edges.values()))
    volumes = {}
    for face in faces:
        a,b,c = [points[p] for p,_,_ in face]
        component = find(face[0][0])
        volumes[component] = volumes.get(component,0)+dot(a,cross(b,c))/6
    assert all(v > 0 for v in volumes.values()),(name,"inverted component",[(k,v) for k,v in volumes.items() if v<=0])
    raw=(OUT/(name+".glb")).read_bytes()
    magic,version,length=struct.unpack_from("<III",raw,0)
    assert magic==0x46546c67 and version==2 and length==len(raw)
    size,kind=struct.unpack_from("<II",raw,12)
    assert kind==0x4e4f534a
    gltf=json.loads(raw[20:20+size])
    assert len(gltf["materials"])==4 and len(gltf["meshes"])==1 and len(gltf["meshes"][0]["primitives"])==4
    assert "skins" not in gltf and "animations" not in gltf
    assert sum(gltf["accessors"][p["indices"]]["count"]//3 for p in gltf["meshes"][0]["primitives"])==len(faces)
    assert all("NORMAL" in p["attributes"] and "TEXCOORD_0" in p["attributes"] for p in gltf["meshes"][0]["primitives"])
    return {"name":name,"triangles":len(faces),"vertices":len(points),"closed_components":len(volumes),
            "all_edges_two_incident_faces":True,"all_components_outward_positive_volume":True,
            "min_triangle_area_cm2":min_area,"min_uv_triangle_area":min_uv_area,
            "min_corner_normal_dot_face_normal":min_dot,"finite_unit_normals":True,"four_materials":sorted(mats),
            "glb_four_primitives_with_normals_uvs":True,
            "obj_sha256":sha(OUT/(name+".obj")),"glb_sha256":sha(OUT/(name+".glb"))}


def main():
    source=json.loads((OUT/"SourceReport.json").read_text(encoding="utf-8"))
    for name,digest in source["protected_sha256"].items():
        assert sha(ROOT/name)==digest,name
    assets=[inspect(name) for name in ("Pursuer","Flanker")]
    result={"status":"CANDIDATE_SOURCE_TOPOLOGY_NORMAL_UV_EXPORT_CHECKS_PASS_NOT_UNREAL",
            "generator_sha256":sha(OUT/"Generate.py"),"validator_sha256":sha(__file__),"assets":assets,
            "original_assets_preserved":True,
            "limits":["Closed components may overlap as assembled manufactured parts; no boolean-unioned collision is implied.",
                      "UV bounds, nondegeneracy and export references checked; no texture bake or runtime lightmap tested.",
                      "Existing runtime sphere and gameplay are unchanged; studio renders and Unreal integration remain separate."]}
    (OUT/"Validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
