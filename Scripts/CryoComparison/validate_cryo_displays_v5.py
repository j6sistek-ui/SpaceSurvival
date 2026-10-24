"""Independent, read-only stdlib OBJ audit of the completed v5 display export.

Writes a revision-named independent audit JSON beside this script. This is
geometry/provenance evidence, not native visual or gameplay acceptance.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
MANIFEST = OUT / "assembly_displays_v5.json"
RECEIPT = OUT / "display-v5-geometry.json"
AUDIT = WORK / "cryo-display-v5-independent-audit.json"


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1 / length(a)) if length(a) > 1e-20 else (0., 0., 0.)
def blend(points, weights): return tuple(sum(p[k]*w for p, w in zip(points, weights)) for k in range(len(points[0])))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4*1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_obj(path):
    vertices, uv, triangles, materials = [], [], [], set()
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            values = line.split()
            if not values: continue
            if values[0] == "v": vertices.append(tuple(float(x)/100 for x in values[1:4]))
            elif values[0] == "vt": uv.append(tuple(float(x) for x in values[1:3]))
            elif values[0] == "usemtl": materials.add(" ".join(values[1:]))
            elif values[0] == "f":
                corners = [tuple(int(x)-1 for x in v.split("/")) for v in values[1:]]
                for k in range(1, len(corners)-1):
                    ids = [corners[j] for j in (0, k, k+1)]
                    points = tuple(vertices[v[0]] for v in ids)
                    triangles.append({"p": points, "uv": tuple(uv[v[1]] for v in ids),
                                      "ids": tuple(v[0] for v in ids),
                                      "n": unit(cross(sub(points[1], points[0]), sub(points[2], points[0])))})
    return {"vertices": vertices, "triangles": triangles, "materials": sorted(materials)}


def barycentric(uv, point):
    a, b, c = uv
    x, y, q = sub(b, a), sub(c, a), sub(point, a)
    den = x[0]*y[1]-y[0]*x[1]
    if abs(den) < 1e-16: return None
    wb = (q[0]*y[1]-y[0]*q[1])/den
    wc = (x[0]*q[1]-q[0]*x[1])/den
    return 1-wb-wc, wb, wc


class UVSurface:
    def __init__(self, triangles):
        self.bins = defaultdict(list)
        self.triangles = []
        for tri in triangles:
            if barycentric(tri["uv"], tri["uv"][0]) is None: continue
            self.triangles.append(tri)
            low = [max(0, min(31, int(min(p[k] for p in tri["uv"])*32))) for k in (0, 1)]
            high = [max(0, min(31, int(max(p[k] for p in tri["uv"])*32))) for k in (0, 1)]
            for x in range(low[0], high[0]+1):
                for y in range(low[1], high[1]+1): self.bins[x, y].append(tri)

    def samples(self, point):
        key = tuple(max(0, min(31, int(v*32))) for v in point)
        result = []
        for tri in self.bins[key]:
            weights = barycentric(tri["uv"], point)
            if min(weights) >= -2e-6:
                result.append((blend(tri["p"], weights), tri["n"], tri, min(weights)))
        return result

    def closest(self, uv, reference):
        hits = self.samples(uv)
        if not hits: raise RuntimeError(f"No UV surface at {uv}")
        return min(hits, key=lambda h: length(sub(h[0], reference)))


class BVH:
    """Plain Python triangle BVH for independently checking backing/body depth."""
    def __init__(self, triangles):
        self.triangles = triangles
        self.bounds = [(tuple(min(p[k] for p in t["p"]) for k in range(3)),
                        tuple(max(p[k] for p in t["p"]) for k in range(3))) for t in triangles]
        self.root = self.build(list(range(len(triangles))))

    def build(self, indices):
        lo = tuple(min(self.bounds[i][0][k] for i in indices) for k in range(3))
        hi = tuple(max(self.bounds[i][1][k] for i in indices) for k in range(3))
        if len(indices) <= 12: return lo, hi, None, None, indices
        axis = max(range(3), key=lambda k: hi[k]-lo[k])
        indices.sort(key=lambda i: self.bounds[i][0][axis]+self.bounds[i][1][axis])
        middle = len(indices)//2
        return lo, hi, self.build(indices[:middle]), self.build(indices[middle:]), None

    @staticmethod
    def box(origin, direction, lo, hi, limit):
        near, far = 0., limit
        for k in range(3):
            if abs(direction[k]) < 1e-14:
                if origin[k] < lo[k]-1e-9 or origin[k] > hi[k]+1e-9: return False
            else:
                a, b = (lo[k]-origin[k])/direction[k], (hi[k]-origin[k])/direction[k]
                near, far = max(near, min(a, b)), min(far, max(a, b))
                if near > far: return False
        return True

    def ray(self, origin, direction, limit=.16):
        best, stack, found = limit, [self.root], False
        while stack:
            lo, hi, left, right, indices = stack.pop()
            if not self.box(origin, direction, lo, hi, best): continue
            if indices is None:
                stack.extend((left, right)); continue
            for i in indices:
                a, b, c = self.triangles[i]["p"]
                e1, e2 = sub(b, a), sub(c, a)
                p = cross(direction, e2); den = dot(e1, p)
                if abs(den) < 1e-15: continue
                inv = 1/den; t = sub(origin, a); u = dot(t, p)*inv
                if u < -1e-8 or u > 1+1e-8: continue
                q = cross(t, e1); v = dot(direction, q)*inv
                if v < -1e-8 or u+v > 1+1e-8: continue
                distance = dot(e2, q)*inv
                if 0 <= distance <= best: best, found = distance, True
        return best if found else None


def range_mm(values): return [min(values)*1000, max(values)*1000] if values else None


def shifted_mesh(mesh,delta):
    return {**mesh,'vertices':[add(p,delta) for p in mesh['vertices']],
            'triangles':[{**t,'p':tuple(add(p,delta) for p in t['p'])} for t in mesh['triangles']]}


def check_status_support(content,lens,body,housing,old_housing,support):
    """Narrow v5_4 check for the source rail seen intersecting D's status."""
    lo,hi=support['pad_world_bounds_m']
    def clip(poly,axis,value,sign):
        result=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da,db=(a[axis]-value)*sign,(b[axis]-value)*sign
            if da>=0:result.append(a)
            if (da>=0)!=(db>=0):result.append(add(a,mul(sub(b,a),da/(da-db))))
        return result
    clipped=[]
    for tri in body['triangles']:
        poly=list(tri['p'])
        for axis,value,sign in [(0,lo[0],1),(0,hi[0],-1),(2,lo[2],1),(2,hi[2],-1)]:
            poly=clip(poly,axis,value,sign)
            if not poly:break
        clipped.extend(poly)
    front=min(p[1] for p in clipped)
    clearance=(front-max(p[1] for p in content['vertices']))*1000
    oldtree=BVH(old_housing['triangles']);overlaps=[]
    for x in [lo[0]+.005,(lo[0]+hi[0])/2,hi[0]-.005]:
        for z in [lo[2]+.005,(lo[2]+hi[2])/2,hi[2]-.005]:
            origin=(x,lo[1]-.02,z);distance=oldtree.ray(origin,(0,1,0),.1)
            if distance is not None:overlaps.append((hi[1]-origin[1]-distance)*1000)
    prefix_vertices=housing['vertices'][:len(old_housing['vertices'])]==old_housing['vertices']
    signature=lambda ts:[(t['ids'],t['uv'],t['p']) for t in ts]
    prefix_faces=signature(housing['triangles'][:len(old_housing['triangles'])])==signature(old_housing['triangles'])
    return {'source_rail_front_y_m':front,'glyph_clearance_to_frontmost_source_mm':clearance,
            'pad_front_clearance_to_source_mm':(front-lo[1])*1000,'old_housing_overlap_mm':range_mm([v/1000 for v in overlaps]),
            'support_contact_rays':len(overlaps),'old_housing_vertex_prefix_preserved':prefix_vertices,
            'old_housing_triangle_uv_prefix_preserved':prefix_faces,
            'passes':clearance>3 and len(overlaps)==9 and min(overlaps)>2.5 and prefix_vertices and prefix_faces}


def actual_uv_seams(mesh):
    groups=defaultdict(list)
    for tri in mesh["triangles"]:
        for uv,point in zip(tri["uv"],tri["p"]):groups[tuple(round(v,5) for v in uv)].append(point)
    gaps=[]
    for points in groups.values():
        if len(points)>1:
            gaps.append(max(length(sub(a,b)) for i,a in enumerate(points) for b in points[i+1:]))
    return {"repeated_uv_groups":len(gaps),"uv_quantization":1e-5,
            "maximum_matched_uv_position_separation_mm":max(gaps,default=0)*1000,
            "passes":bool(gaps) and max(gaps)<.00005}


def check_holo(mesh, glass, frost, bounds, offset, continuous=False):
    distances, residuals, frost_gaps, membership, orientation = [], [], [], [], []
    front_tree=BVH(glass.triangles);actual_glass_gaps=[];glass_ray_misses=0
    vertex_offset_errors=[];offset_lengths=[]
    u0, u1, v0, v1 = bounds
    for tri in mesh["triangles"]:
        uv = [(u0+p[0]*(u1-u0), v0+p[1]*(v1-v0)) for p in tri["uv"]]
        center = blend(uv, (1/3,)*3)
        candidates = glass.samples(center)
        if not candidates: raise RuntimeError("Holo triangle has no matching source glass face")
        _, n, underlying, _ = max(candidates, key=lambda h: h[3])
        if n[1] > 0: n = mul(n, -1)
        orientation.append(dot(n, tri["n"]))
        for weights in [(1,0,0),(0,1,0),(0,0,1),(1/3,)*3]:
            coord, actual = blend(uv, weights), blend(tri["p"], weights)
            bary = barycentric(underlying["uv"], coord)
            membership.append(min(bary))
            surface = blend(underlying["p"], bary)
            delta = sub(actual, surface); distances.append(dot(delta, n))
            residuals.append(length(sub(delta, mul(n, offset))))
            offset_lengths.append(length(delta))
            if max(weights)==1:vertex_offset_errors.append(abs(length(delta)-abs(offset)))
            hit=front_tree.ray(add(actual,mul(n,.03)),mul(n,-1),.06)
            if hit is None:glass_ray_misses+=1
            else:actual_glass_gaps.append(.03-hit)
            frost_point, frost_n, _, _ = frost.closest(coord, actual)
            if frost_n[1] > 0: frost_n = mul(frost_n, -1)
            frost_gaps.append(dot(sub(frost_point, actual), frost_n))
    seams=actual_uv_seams(mesh)
    correspondence_pass=(max(vertex_offset_errors)<.00003 and min(offset_lengths)>abs(offset)*.75
                         and max(offset_lengths)<abs(offset)+.00003 and seams["passes"]) if continuous else max(residuals)<.00003
    return {"triangles": len(mesh["triangles"]), "samples": len(distances),
            "signed_distance_from_glass_mm": range_mm(distances),
            "expected_offset_mm": offset*1000,
            "offset_basis":"continuous shared normals" if continuous else "source flat face normal",
            "offset_magnitude_mm":range_mm(offset_lengths),
            "max_vertex_offset_magnitude_error_mm":max(vertex_offset_errors)*1000,
            "max_correspondence_error_mm": max(residuals)*1000,
            "correspondence_note":"Flat-face vector residual is diagnostic only for shared-normal offsets; vertex offset magnitude, inside direction, nearest-surface rays and seam continuity are gated instead." if continuous else "Exact source triangle plus flat-normal offset.",
            "actual_uv_seams":seams,
            "minimum_source_triangle_barycentric": min(membership),
            "frost_in_front_mm": range_mm(frost_gaps),
            "nearest_glass_along_normal_in_front_mm":range_mm(actual_glass_gaps),
            "nearest_glass_ray_misses":glass_ray_misses,
            "minimum_outward_winding_dot": min(orientation),
            "passes": correspondence_pass and min(membership) > -2e-5
                      and max(distances) < -.001 and min(frost_gaps) > .001
                      and min(orientation) > 0 and glass_ray_misses==0 and min(actual_glass_gaps)>.001}


def seam_displacement(glass, bounds, offset):
    u0, u1, v0, v1 = bounds
    edges = defaultdict(list)
    for tri in glass.triangles:
        if max(p[0] for p in tri["uv"]) < u0 or min(p[0] for p in tri["uv"]) > u1: continue
        if max(p[1] for p in tri["uv"]) < v0 or min(p[1] for p in tri["uv"]) > v1: continue
        n = tri["n"] if tri["n"][1] < 0 else mul(tri["n"], -1)
        for a, b in ((0,1),(1,2),(2,0)): edges[tuple(sorted((tri["ids"][a],tri["ids"][b])))].append(n)
    gaps = [length(mul(sub(ns[0],ns[1]),offset)) for ns in edges.values() if len(ns)==2]
    return {"adjacent_source_edges": len(gaps), "max_possible_flat_normal_seam_displacement_mm": max(gaps)*1000,
            "note": "Diagnostic only: normal-offset triangle pieces can separate at creases. Native visual review must assess visibility."}


def check_display(content, lens, backing):
    lens_surface, back_surface = UVSurface(lens["triangles"]), UVSurface(backing["triangles"])
    gaps, content_depth, lens_depth, orientations = [], [], [], []
    for tri in content["triangles"]:
        for weights in [(1,0,0),(0,1,0),(0,0,1),(1/3,)*3]:
            uv, point = blend(tri["uv"], weights), blend(tri["p"], weights)
            lp, n, _, _ = lens_surface.closest(uv, point)
            bp, _, _, _ = back_surface.closest(uv, lp)
            gaps.append(dot(sub(lp,point),n)); content_depth.append(dot(sub(point,bp),n))
            lens_depth.append(dot(sub(lp,bp),n)); orientations.append(dot(tri["n"],n))
    return {"triangles":len(content["triangles"]), "samples":len(gaps),
            "lens_ahead_of_content_mm":range_mm(gaps), "content_ahead_of_backing_mm":range_mm(content_depth),
            "lens_ahead_of_backing_mm":range_mm(lens_depth), "minimum_matching_winding_dot":min(orientations),
            "passes":max(abs(v-.005) for v in gaps)<.00015 and max(abs(v-.003) for v in content_depth)<.00015
                      and max(abs(v-.008) for v in lens_depth)<.00015 and min(orientations)>0,
            "normal_note":"Positive dot proves outward winding. Alignment variation is a shading diagnostic, not a depth failure."}


def check_body_depth(backing, tree):
    gaps, misses, offenders = [], 0, []
    # UV-degenerate fitted rim faces are deliberately excluded: this checks the
    # clean display area, whose visibility must not be obstructed by source mesh.
    for tri in UVSurface(backing["triangles"]).triangles:
        for weights in [(1/3,)*3,(.8,.1,.1),(.1,.8,.1),(.1,.1,.8)]:
            point = blend(tri["p"],weights); n=tri["n"]
            distance = tree.ray(add(point,mul(n,.06)),mul(n,-1))
            if distance is None: misses += 1
            else:
                gap=distance-.06;gaps.append(gap)
                if gap<-.0001:
                    offenders.append({"display_uv":blend(tri["uv"],weights),"backing_world_m":point,
                                      "body_in_front_mm":-gap*1000,"outward_normal":n})
    return {"samples":len(gaps)+misses,"ray_misses":misses,"backing_ahead_of_body_mm":range_mm(gaps),
            "samples_body_in_front":sum(v<-.0001 for v in gaps),"body_in_front_samples":offenders,
            "passes":misses==0 and min(gaps)>=-.0001}


def inspect_glb(path):
    raw=Path(path).read_bytes();magic,version,size=struct.unpack_from("<4sII",raw)
    if (magic,version,size)!=(b"glTF",2,len(raw)):raise RuntimeError("Invalid GLB header")
    count,kind=struct.unpack_from("<I4s",raw,12)
    if kind!=b"JSON":raise RuntimeError("Missing GLB JSON")
    doc=json.loads(raw[20:20+count]);materials=doc.get("materials",[])
    glyph=[m for m in materials if m.get("name","").startswith("M_Cryo_VectorGlyph_v5")]
    def has_texture(value):
        if isinstance(value,dict):return any("texture" in str(k).lower() or has_texture(v) for k,v in value.items())
        if isinstance(value,list):return any(has_texture(v) for v in value)
        return False
    return {"mesh_count":len(doc.get("meshes",[])),"images_embedded":all("bufferView" in i and "uri" not in i for i in doc.get("images",[])),
            "glyph_materials":len(glyph),"glyph_uses_texture":any(has_texture(m) for m in glyph),
            "passes":len(doc.get("meshes",[]))==21 and len(glyph)==1 and not any(has_texture(m) for m in glyph)}


def main(manifest_path=MANIFEST,receipt_path=RECEIPT,audit_path=AUDIT):
    manifest_path,receipt_path,audit_path=map(Path,(manifest_path,receipt_path,audit_path))
    if audit_path.parent.resolve()!=WORK.resolve() or not re.fullmatch(r"cryo-display-v5(?:_\d+)?-independent-audit\.json",audit_path.name):
        raise RuntimeError("Audit output must be a revision-named JSON inside this work folder")
    manifest_hash=sha(manifest_path)
    if audit_path.exists() and json.loads(audit_path.read_text()).get("manifest_sha256")!=manifest_hash:
        raise RuntimeError("Refusing to overwrite an audit bound to a different manifest; choose the matching revision output")
    manifest=json.loads(manifest_path.read_text());receipt=json.loads(receipt_path.read_text())
    source_path=Path(manifest["source_manifest"]);source=json.loads(source_path.read_text())
    source_models={m["id"]:m for m in source["models"]}
    tracked={str(manifest_path):manifest_hash,str(receipt_path):sha(receipt_path)}
    errors=[];models=[]
    protected=receipt["protected_hashes"]
    changed=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h]
    if changed:errors.append({"protected_inputs_changed":changed})
    if sha(source_path)!=manifest["source_manifest_sha256"]:errors.append("Source manifest SHA mismatch")
    for model in manifest["models"]:
        rows={r["name"]:r for r in model["components"]};old={r["name"]:r for r in source_models[model["id"]]["components"]}
        detail={"id":model["id"],"component_count":len(rows),"checks":{}}
        if len(rows)!=21:errors.append(model["id"]+": component count")
        for row in rows.values():
            value=sha(row["file"]);tracked[row["file"]]=value
            if row.get("display_revision") and value!=row.get("source_sha256"):errors.append(model["id"]+": new OBJ hash "+row["name"])
        unchanged=model["display_v5"]["unchanged_geometry"]
        detail["unchanged_components"]={n:sha(rows[n]["file"])==sha(old[n]["file"]) for n in unchanged}
        if not all(detail["unchanged_components"].values()):errors.append(model["id"]+": preserved OBJ changed")
        mesh={name:load_obj(row["file"]) for name,row in rows.items() if name in ("Glass","Frost","Holo","Holo_Panel","Status","Status_Glass","Console_1_Backing","Console_1_Glass","Console_1_HUD","Console_2_Backing","Console_2_Glass","Console_2_HUD")}
        old_glass=load_obj(old["Glass"]["file"])
        glass_positions_unchanged=mesh["Glass"]["vertices"]==old_glass["vertices"]
        glass_topology_uv_unchanged=[(t["ids"],t["uv"]) for t in mesh["Glass"]["triangles"]]==[(t["ids"],t["uv"]) for t in old_glass["triangles"]]
        detail["checks"]["Glass_preserved_geometry"]={"positions_unchanged":glass_positions_unchanged,
            "triangles_and_uv_unchanged":glass_topology_uv_unchanged,"passes":glass_positions_unchanged and glass_topology_uv_unchanged,
            "note":"Shading normals intentionally differ; original pane positions, topology and UV are checked separately."}
        glass=UVSurface([t for t in mesh["Glass"]["triangles"] if max(t["ids"])<1353])
        frost=UVSurface([t for t in mesh["Frost"]["triangles"] if max(t["ids"])<1353])
        bounds=model["display_v5"]["holo_front_glass_uv_bounds"]
        continuous="Shared interpolated" in model["display_v5"].get("holo_offset_basis","")
        for name,offset in (("Holo",-.0025),("Holo_Panel",-.004)):
            detail["checks"][name]=check_holo(mesh[name],glass,frost,bounds,offset,continuous)
        if not continuous:detail["seam_diagnostic"]=seam_displacement(glass,bounds,-.004)
        status_base=load_obj(old["Status"]["file"])
        body=load_obj(rows["Body"]["file"])
        support=model["display_v5"].get("status_support_v5_4")
        if support:
            status_base=shifted_mesh(status_base,support['translation_world_m'])
            detail['checks']['Status_supported_rail_clearance']=check_status_support(mesh['Status'],mesh['Status_Glass'],body,
                load_obj(rows['Housing']['file']),load_obj(old['Housing']['file']),support)
        detail["checks"]["Status_layers"]=check_display(mesh["Status"],mesh["Status_Glass"],status_base)
        tree=BVH(body["triangles"])
        for prefix in ("Console_1","Console_2"):
            detail["checks"][prefix+"_layers"]=check_display(mesh[prefix+"_HUD"],mesh[prefix+"_Glass"],mesh[prefix+"_Backing"])
            detail["checks"][prefix+"_body_clearance"]=check_body_depth(mesh[prefix+"_Backing"],tree)
        detail["checks"]["GLB"]=inspect_glb(model["finished_glb"])
        for key in ("editable_blend","finished_glb"):
            value=sha(model[key]);tracked[model[key]]=value
            expected=model["display_v5"]["blend_sha256" if key=="editable_blend" else "glb_sha256"]
            if value!=expected:errors.append(model["id"]+": "+key+" hash mismatch")
        for name,check in detail["checks"].items():
            if not check["passes"]:errors.append(model["id"]+": "+name)
        models.append(detail)
        print(json.dumps({"model":model["id"],"failed_checks":[n for n,c in detail["checks"].items() if not c["passes"]]}),flush=True)
    changed_during=[p for p,h in tracked.items() if sha(p)!=h]
    if changed_during:errors.append({"inputs_changed_during_audit":changed_during})
    result={"utc":datetime.now(timezone.utc).isoformat(),"status":"PASS_STATIC_GEOMETRY_PENDING_NATIVE_VISUAL_REVIEW" if not errors else "FAIL_STATIC_GEOMETRY",
            "validator_sha256":sha(__file__),"manifest":str(manifest_path),"manifest_sha256":tracked[str(manifest_path)],
            "author_receipt_sha256":tracked[str(receipt_path)],"protected_hash_count":len(protected),"protected_inputs_unchanged":not changed,
            "audited_files_sha256":tracked,"inputs_unchanged_during_audit":not changed_during,"models":models,"errors":errors,
            "limits":["No Blender or Unreal process launched; no asset mutated.","OBJ units interpreted as centimeters per export header.","Clearance samples and correspondence checks do not prove watertightness or native transparency sorting.","Flat-normal offset seam visibility requires native visual review.","No physical-input, animation, owner-acceptance or runtime-performance claim."]}
    audit_path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"errors":errors,"audit":str(audit_path)}),flush=True)
    return 0 if not errors else 1


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,default=MANIFEST)
    parser.add_argument("--receipt",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    match=re.fullmatch(r"assembly_displays_(v5(?:_\d+)?)\.json",args.manifest.name)
    if not match:parser.error("Expected an assembly_displays_v5[_revision].json manifest")
    revision=match.group(1)
    receipt_path=args.receipt or args.manifest.parent/("display-"+revision+"-geometry.json")
    audit_path=args.output or WORK/("cryo-display-"+revision+"-independent-audit.json")
    raise SystemExit(main(args.manifest,receipt_path,audit_path))
