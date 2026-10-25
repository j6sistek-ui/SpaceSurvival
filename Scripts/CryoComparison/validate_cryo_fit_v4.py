"""Independent, read-only geometry fit validation for a new cryo manifest.

First run with normal Python --prepare to hash original/v2/v3 inputs. Then run
standalone Blender --background --disable-autoexec --python this.py --
--manifest <new manifest> only in the lead's assigned engine-free launch window.
No assets are saved, geometry changed, images edited, or renders requested.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import traceback

WORK = Path(__file__).resolve().parent
OUT = WORK.parent / "outputs/Cryo_Comparison"
OLD = OUT / "assembly_holo_consoles.json"
DEFAULT_GUARD = WORK / "cryo-fit-v4-protected.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4*1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stats_mm(values):
    values = sorted(values)
    return None if not values else {"min": values[0]*1000, "median": values[len(values)//2]*1000,
        "p95": values[min(len(values)-1, int(len(values)*.95))]*1000, "max": values[-1]*1000,
        "samples": len(values)}


def prepare(path):
    if path.exists():
        raise RuntimeError("Refusing to overwrite the protected pre-repair baseline: " + str(path))
    files = {OLD, OUT/"assembly.json", WORK/"glb-baseline.json"}
    for name in ("assembly.json", "assembly_holo_consoles.json"):
        manifest = json.loads((OUT/name).read_text())
        files.update(Path(p).resolve() for p in manifest["shared"].values())
        for model in manifest["models"]:
            files.add(Path(model["source"]).resolve())
            files.update(Path(row["file"]).resolve() for row in model["components"])
            files.update(Path(p).resolve() for p in model["textures"].values())
            for key in ("editable_blend", "finished_glb"):
                if key in model:
                    files.add(Path(model[key]).resolve())
    old = json.loads(OLD.read_text())
    known = {}
    for row in old["console_upgrade_receipt"]["models"]:
        known[row["source_blend"]] = row["source_blend_sha256"]
        known[row["blend"]] = row["blend_sha256"]
        known[row["glb"]] = row["glb_validation"]["sha256"]
    for row in json.loads((WORK/"glb-baseline.json").read_text())["assets"]:
        known[row["file"]] = row["sha256"]
    files.update(Path(p).resolve() for p in known)
    hashes = {str(p.resolve()): sha(p) for p in sorted(files)}
    for p, value in known.items():
        if hashes[str(Path(p).resolve())] != value:
            raise RuntimeError("Prior receipt hash mismatch: " + p)
    result = {"utc": datetime.now(timezone.utc).isoformat(), "files": hashes,
              "historical_receipt_hashes_matched": len(known), "count": len(hashes)}
    path.write_text(json.dumps(result, indent=2)+"\n")
    print("CRYO_FIT_GUARD_READY " + str(path) + " files=" + str(len(hashes)), flush=True)


def check_hashes(guard):
    return [p for p, value in guard["files"].items() if not Path(p).is_file() or sha(p) != value]


def mesh_signature(ob):
    digest = hashlib.sha256()
    def add(values):
        digest.update(struct.pack("<"+"d"*len(values), *values))
    for row in ob.matrix_world:
        add(tuple(row))
    for v in ob.data.vertices:
        add(tuple(v.co))
    for p in ob.data.polygons:
        digest.update(struct.pack("<II?", len(p.vertices), p.material_index, p.use_smooth))
        digest.update(struct.pack("<"+"I"*len(p.vertices), *p.vertices))
    for normal in ob.data.corner_normals:
        add(tuple(normal.vector))
    for layer in ob.data.uv_layers:
        digest.update(layer.name.encode())
        for loop in layer.data:
            add(tuple(loop.uv))
    return digest.hexdigest()


def surface(ob):
    from mathutils.bvhtree import BVHTree
    points = [ob.matrix_world @ v.co for v in ob.data.vertices]
    faces = [tuple(p.vertices) for p in ob.data.polygons]
    ob.data.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in ob.data.loop_triangles]
    tree = BVHTree.FromPolygons(points, triangles, all_triangles=True)
    counts = Counter(tuple(sorted((face[i], face[(i+1)%len(face)]))) for face in faces for i in range(len(face)))
    boundary = [edge for edge, count in counts.items() if count == 1]
    parent = list(range(len(points)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a,b in counts:
        parent[find(a)] = find(b)
    labels = [find(i) for i in range(len(points))]
    return {"points": points, "faces": faces, "triangles": triangles, "tree": tree, "boundary": boundary,
            "labels": labels, "components": len(set(labels)),
            "nonmanifold_edges_gt2": sum(count > 2 for count in counts.values())}


def edge_samples(surf, steps=4):
    for a,b in surf["boundary"]:
        pa,pb = surf["points"][a],surf["points"][b]
        for step in range(steps+1):
            yield pa.lerp(pb, step/steps), surf["labels"][a], (a,b)


def surface_samples(surf):
    yield from surf["points"]
    # Nonplanar quad centroids do not necessarily lie on the rendered surface.
    # Use Blender's actual tessellation for every interior/edge sample.
    for face in surf["triangles"]:
        points = [surf["points"][index] for index in face]
        yield sum(points[1:], points[0].copy()) / len(points)
        for a,b in zip(points, points[1:]+points[:1]):
            yield (a+b)*.5


def distance_segment(point, a, b):
    edge = b-a
    t = max(0., min(1., (point-a).dot(edge)/max(edge.length_squared, 1e-18)))
    return (point-a-edge*t).length


def overlaid_fit(surf, support):
    distances=[]; projected_margins=[]; worst=[]
    for point in surface_samples(surf):
        loc, normal, face, distance = support["tree"].find_nearest(point)
        distances.append(distance)
        margin = min((distance_segment(loc, support["points"][a], support["points"][b])
                      for a,b in support["boundary"]), default=float("inf"))
        projected_margins.append(margin)
        worst.append((distance, tuple(point), tuple(loc)))
    return {"support_distance_mm": stats_mm(distances), "projected_edge_margin_mm": stats_mm(projected_margins),
            "worst_samples_m": [{"distance_mm": d*1000,"point":p,"support":q} for d,p,q in sorted(worst,reverse=True)[:5]]}


def quad_subset(surf, start):
    """Read an appended disconnected quad without comparing it to another bezel."""
    from mathutils.bvhtree import BVHTree
    points=surf["points"][start:start+4]
    faces=[tuple(i-start for i in face) for face in surf["faces"] if all(start<=i<start+4 for i in face)]
    triangles=[tuple(i-start for i in face) for face in surf["triangles"] if all(start<=i<start+4 for i in face)]
    assert len(points)==4 and len(faces)==1 and len(triangles)==2
    face=faces[0]
    return {"points":points,"faces":faces,"triangles":triangles,
            "boundary":[(face[i],face[(i+1)%4]) for i in range(4)],
            "tree":BVHTree.FromPolygons(points,triangles,all_triangles=True)}


def seating_fit(housing, glass, body):
    """Discover open two-rail flange strips by topology, then measure both rails.

    This uses actual Housing vertices/faces, not manifest boundary coordinates.
    Tube gaskets and closed support boxes do not match the strip topology.
    """
    from collections import defaultdict
    groups=defaultdict(list)
    for face in housing["faces"]:
        groups[housing["labels"][face[0]]].append(face)
    strips=[]
    for label,faces in groups.items():
        vertices={i for face in faces for i in face}
        if len(faces)<100 or len(vertices)!=2*(len(faces)+1) or any(len(f)!=4 for f in faces):continue
        uses=defaultdict(list)
        for fi,face in enumerate(faces):
            for i,a in enumerate(face):uses[tuple(sorted((a,face[(i+1)%4])))].append(fi)
        if {i for edge,owners in uses.items() if len(owners)==1 for i in edge}!=vertices:continue
        adjacency=defaultdict(list)
        for edge,owners in uses.items():
            if len(owners)==2:
                a,b=owners;adjacency[a].append((b,edge));adjacency[b].append((a,edge))
        ends=[i for i in range(len(faces)) if len(adjacency[i])==1]
        if len(ends)!=2:continue
        order=[];previous=None;current=ends[0]
        while current is not None:
            order.append(current)
            nexts=[(i,e) for i,e in adjacency[current] if i!=previous]
            previous,current=current,(nexts[0][0] if nexts else None)
        if len(order)!=len(faces):continue
        first_shared=next(e for i,e in adjacency[order[0]] if i==order[1])
        first_face=faces[order[0]]
        rung=tuple(i for i in first_face if i not in first_shared)
        rails=[[rung[0]],[rung[1]]]
        for step,fi in enumerate(order):
            face=faces[fi]
            target=(next(e for i,e in adjacency[fi] if i==order[step+1]) if step+1<len(order)
                    else tuple(i for i in face if i not in rung))
            edges={tuple(sorted((face[i],face[(i+1)%4]))) for i in range(4)}
            if tuple(sorted((rails[0][-1],target[0]))) in edges:pair=target
            else:pair=(target[1],target[0])
            rails[0].append(pair[0]);rails[1].append(pair[1]);rung=pair
        candidates=[]
        for rail in rails:
            points=[housing["points"][i] for i in rail]
            signed=[];distances=[];worst=[]
            for a,b in zip(points,points[1:]):
                for step in range(5):
                    p=a.lerp(b,step/4);q,n,_,d=body["tree"].find_nearest(p)
                    s=(p-q).dot(n);signed.append(s);distances.append(d);worst.append((d,tuple(p),tuple(q),s))
            candidates.append({"points":points,"embedding_error":sum(abs(s+.002) for s in signed)/len(signed),
                               "distance":stats_mm(distances),"signed":stats_mm(signed),"worst":worst})
        bi=min(range(2),key=lambda i:candidates[i]["embedding_error"])
        source=candidates[bi];pane=candidates[1-bi]
        vertex_d=[];vertex_s=[];vertex_worst=[]
        for p in source["points"]:
            q,n,_,d=body["tree"].find_nearest(p);signed=(p-q).dot(n)
            vertex_d.append(d);vertex_s.append(signed);vertex_worst.append((d,tuple(p),tuple(q),signed))
        segments=[((b-a).length,tuple(a),tuple(b)) for a,b in zip(source["points"],source["points"][1:])]
        pane_d=[]
        for a,b in zip(pane["points"],pane["points"][1:]):
            for step in range(5):pane_d.append(glass["tree"].find_nearest(a.lerp(b,step/4))[3])
        strips.append({"label":label,"quad_faces":len(faces),"rail_vertices_each":len(source["points"]),
                       "body_attachment_distance_mm":source["distance"],"body_attachment_signed_mm":source["signed"],
                       "body_endpoint_distance_mm":stats_mm(vertex_d),"body_endpoint_signed_mm":stats_mm(vertex_s),
                       "body_rail_segment_lengths_mm":stats_mm([v[0] for v in segments]),
                       "body_longest_segments_m":[{"length_mm":d*1000,"a":a,"b":b} for d,a,b in sorted(segments,reverse=True)[:3]],
                       "body_endpoint_worst_m":[{"gap_mm":d*1000,"point":p,"body":q,"signed_mm":s*1000}
                                               for d,p,q,s in sorted(vertex_worst,reverse=True)[:3]],
                       "pane_attachment_distance_mm":stats_mm(pane_d),
                       "body_worst_samples_m":[{"gap_mm":d*1000,"point":p,"body":q,"signed_mm":s*1000}
                                               for d,p,q,s in sorted(source["worst"],reverse=True)[:3]]})
    return {"actual_strip_count":len(strips),"strips":strips}


def closed_seating_fit(housing, glass, body, model_id):
    """Test actual closed rail topology and source contact along cross-sections.

    No closest-normal sign is used as an inside/outside classification. A contact
    means a cross-section intersects the intended frame surface before its end;
    this is not a claim that the generated source body is a watertight solid.
    """
    from collections import defaultdict
    from mathutils.bvhtree import BVHTree
    groups=defaultdict(list)
    for face in housing["faces"]:
        groups[housing["labels"][face[0]]].append(face)
    points=housing["points"];source_points=body["points"];strips=[]
    for label,faces in groups.items():
        vertices=sorted({i for face in faces for i in face})
        if len(faces)<100 or len(vertices)%4 or len(faces)!=len(vertices)-2 or any(len(f)!=4 for f in faces):
            continue
        uses=Counter(tuple(sorted((face[i],face[(i+1)%4]))) for face in faces for i in range(4))
        # Verify the emitted ring topology before interpreting any vertex order.
        rings=[vertices[i:i+4] for i in range(0,len(vertices),4)]
        if any(tuple(sorted((ring[k],ring[(k+1)%4]))) not in uses for ring in rings for k in range(4)):
            continue
        if any(tuple(sorted((a[k],b[k]))) not in uses for a,b in zip(rings,rings[1:]) for k in range(4)):
            continue
        cross=[];ring_points=[[points[i] for i in ring] for ring in rings]
        option=min((0,1),key=lambda k:sum((p[k]-p[(k+1)%4]).length+(p[(k+2)%4]-p[(k+3)%4]).length for p in ring_points))
        ordered_ends=[[(p[option],p[(option+1)%4]),(p[(option+3)%4],p[(option+2)%4])] for p in ring_points]
        pane_end=min((0,1),key=lambda k:sum(glass["tree"].find_nearest((ends[k][0]+ends[k][1])*.5)[3] for ends in ordered_ends))
        for ends in ordered_ends:
            # Opposite short edges are the two 4mm rail ends. Choose the end
            # touching Glass by measurement, not by semantic vertex indices.
            # Choose once for the complete strip: near-coplanar body ends can
            # also lie on Glass, so independent per-ring ties must not flip it.
            if pane_end==1:
                ends.reverse()
            cross.append(ends)
        pane_centers=[(row[0][0]+row[0][1])*.5 for row in cross]
        mean=sum(pane_centers[1:],pane_centers[0].copy())/len(pane_centers)
        zspan=max(p.z for p in pane_centers)-min(p.z for p in pane_centers)
        if zspan<1.:
            if mean.z<1.5:
                region_name="bottom cap, all triangle vertices 0.4<Z<1.04m"
                triangles=[t for t in body["triangles"] if all(.4<source_points[i].z<1.04 for i in t)]
            else:
                region_name="top cap, all triangle vertices Z>2.72m"
                triangles=[t for t in body["triangles"] if all(source_points[i].z>2.72 for i in t)]
        else:
            sx=1 if mean.x>0 else -1;sy=1 if mean.y>0 else -1
            if model_id=="C":
                region_name=f"C corner post, signs({sx},{sy}), abs X/Y>0.52m"
                triangles=[t for t in body["triangles"] if all(source_points[i].x*sx>.52 and source_points[i].y*sy>.52 for i in t)]
            else:
                region_name=f"side post, X sign {sx}, abs X>0.64m"
                triangles=[t for t in body["triangles"] if all(source_points[i].x*sx>.64 for i in t)]
        if not triangles:
            raise RuntimeError(f"Empty intended frame region: {model_id}/{label}/{region_name}")
        intended=BVHTree.FromPolygons(source_points,triangles,all_triangles=True)
        center_misses=[];edge_misses=[];center_extensions=[];edge_extensions=[];pane_d=[];thickness=[]
        sampled_sections=0
        for segment,(a,b) in enumerate(zip(cross,cross[1:])):
            for step in range(5):
                t=step/4
                pairs=[(a[0][side].lerp(b[0][side],t),a[1][side].lerp(b[1][side],t)) for side in range(2)]
                center=((pairs[0][0]+pairs[1][0])*.5,(pairs[0][1]+pairs[1][1])*.5)
                pane_d.append(glass["tree"].find_nearest(center[0])[3])
                thickness.append((pairs[0][0]-pairs[1][0]).length)
                sampled_sections+=1
                for lane,(p,q) in [("center",center),("edge0",pairs[0]),("edge1",pairs[1])]:
                    vector=q-p;length=vector.length
                    if length<1e-9:
                        hit=None;extension=None
                    else:
                        direction=vector/length
                        hit,normal,face,distance=intended.ray_cast(p-direction*.0001,direction,length+.0002)
                        extension=None if hit is None else length-(distance-.0001)
                    extensions=center_extensions if lane=="center" else edge_extensions
                    misses=center_misses if lane=="center" else edge_misses
                    if hit is not None and extension>=.0005:
                        extensions.append(extension)
                    else:
                        item={"segment":segment,"segment_fraction":t,"lane":lane,"pane_point":tuple(p),
                              "end_point":tuple(q),"length_mm":length*1000,
                              "hit_extension_mm":None if extension is None else extension*1000}
                        if lane=="center":
                            nearest,_,_,pane_gap=intended.find_nearest(p)
                            contacts=[(intended.find_nearest(p.lerp(q,k/16))[3],k/16) for k in range(17)]
                            gap,fraction=min(contacts)
                            item.update({"pane_to_intended_frame_mm":pane_gap*1000,"nearest_frame_to_pane":tuple(nearest),
                                         "sampled_crosssection_min_gap_mm":gap*1000,"min_gap_fraction":fraction,
                                         "direct_pane_contact_within_2mm":pane_gap<=.002,
                                         "sampled_crosssection_contact_within_2mm":gap<=.002})
                        misses.append(item)
        unresolved=[row for row in center_misses if not row["sampled_crosssection_contact_within_2mm"]]
        strips.append({"label":label,"quad_faces":len(faces),"rings":len(rings),"closed_edges_exactly_two_faces":all(n==2 for n in uses.values()),
                       "intended_source_region":region_name,"intended_source_triangles":len(triangles),
                       "sampled_crosssections":sampled_sections,"center_contact_hits":len(center_extensions),
                       "center_contact_misses":len(center_misses),"center_extension_after_contact_mm":stats_mm(center_extensions),
                       "ray_misses_with_direct_pane_contact_within_2mm":sum(row["direct_pane_contact_within_2mm"] for row in center_misses),
                       "ray_miss_pane_to_frame_mm":stats_mm([row["pane_to_intended_frame_mm"]/1000 for row in center_misses]),
                       "ray_miss_crosssection_min_gap_mm":stats_mm([row["sampled_crosssection_min_gap_mm"]/1000 for row in center_misses]),
                       "unresolved_center_crosssections_over_2mm":len(unresolved),
                       "unresolved_center_crosssections_over_5mm":sum(row["sampled_crosssection_min_gap_mm"]>5 for row in unresolved),
                       "unresolved_worst_samples_m":sorted(unresolved,key=lambda row:row["sampled_crosssection_min_gap_mm"],reverse=True)[:12],
                       "center_miss_samples_m":sorted(center_misses,key=lambda row:row["pane_to_intended_frame_mm"],reverse=True)[:12],
                       "thickness_edge_contact_hits":len(edge_extensions),
                       "thickness_edge_contact_misses":len(edge_misses),"thickness_edge_miss_samples_m":edge_misses[:6],
                       "pane_center_to_glass_mm":stats_mm(pane_d),"pane_end_thickness_mm":stats_mm(thickness)})
    return {"mode":"closed solid rail cross-section contact", "actual_strip_count":len(strips),"strips":strips,
            "interpretation":"Ray contact or sampled centerline clearance within2mm proves the sampled seat reaches the intended frame tolerance. A miss at a directly contacting pane is not treated as a gap. Cross-section clearance uses17 samples; thickness-edge misses remain diagnostic, so this is not full-width or watertight-volume certification."}


def validate(args):
    import bpy
    from mathutils import Vector
    guard=json.loads(args.guard.read_text())
    old=json.loads(OLD.read_text())
    new=json.loads(args.manifest.read_text())
    report={"utc":datetime.now(timezone.utc).isoformat(),"manifest":str(args.manifest.resolve()),
            "manifest_sha256":sha(args.manifest),"basis":"meters, Blender front -Y/Z up; reported distances mm",
            "thresholds_mm":{"direct_glass_edge_body_max":3.,"glass_to_housing_seat_max":1.5,
                             "seat_body_attachment_gap_max":3.,"seat_body_signed_outside_max":.5,
                             "holo_glass_offset_max":3.,"holo_projected_margin_min":2.,
                             "C_seam_gap_max":.5,"console_glass_target":8.,"console_HUD_target":10.,"console_tolerance":1.5},
            "models":[],"failures":[],"warnings":[],"scope":"Independent numerical fit only. Multi-angle visual review remains required."}
    def check(condition, message):
        if not condition:
            report["failures"].append(message)
    before=check_hashes(guard)
    check(not before, "Protected pre-repair files changed before validation: " + str(before))
    v4files={str(args.manifest.resolve()):sha(args.manifest)}
    for model in new["models"]:
        for key in ("editable_blend","finished_glb"):
            p=model[key];v4files[p]=sha(p)
        for comp in model["components"]:
            v4files[comp["file"]]=sha(comp["file"])
    for model in new["models"]:
        model_id=model["id"]
        previous=next(row for row in old["models"] if row["id"]==model_id)
        bpy.ops.wm.open_mainfile(filepath=previous["editable_blend"], load_ui=False)
        before_body=mesh_signature(bpy.data.objects["Body"])
        original_backings={i:surface(bpy.data.objects[f"Console_{i}_Backing"]) for i in (1,2)}
        bpy.ops.wm.open_mainfile(filepath=model["editable_blend"], load_ui=False)
        bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        body_signature=mesh_signature(bpy.data.objects["Body"])
        check(body_signature==before_body, model_id+" Body geometry/UV/normals/transform changed")
        body=surface(bpy.data.objects["Body"]);glass=surface(bpy.data.objects["Glass"])
        housing=surface(bpy.data.objects["Housing"])
        holo=surface(bpy.data.objects["Holo"])
        boundary=[]
        for point,label,edge in edge_samples(glass):
            loc,normal,face,distance=body["tree"].find_nearest(point)
            boundary.append((distance,tuple(point),tuple(loc)))
        info={"id":model_id,"body_geometry_unchanged":body_signature==before_body,"body_geometry_sha256":body_signature,
              "glass_components":glass["components"],"glass_nonmanifold_edges_gt2":glass["nonmanifold_edges_gt2"],
              "glass_boundary_to_body_mm":stats_mm([row[0] for row in boundary]),
              "glass_worst_boundary_samples_m":[{"gap_mm":d*1000,"point":p,"body":q} for d,p,q in sorted(boundary,reverse=True)[:10]],
              "holo":overlaid_fit(holo,glass),"bottom_consoles":[]}
        check(bool(boundary),model_id+" Glass has no measurable boundary")
        if model.get("fit_v4",{}).get("seating_flange"):
            seat_distances=[housing["tree"].find_nearest(p)[3] for p,_,_ in edge_samples(glass,8)]
            info["glass_boundary_to_housing_seat_mm"]=stats_mm(seat_distances)
            closed_flange=model["fit_v4"]["seating_flange"].startswith("Closed")
            info["seating_flange"]=(closed_seating_fit(housing,glass,body,model_id) if closed_flange else seating_fit(housing,glass,body))
            info["glass_body_gap_note"]="Raw body clearance retained; physical attachment uses actual opaque Housing flange and gasket."
            check(max(seat_distances)<=.0015,model_id+" Glass-to-Housing seat gap exceeds1.5mm")
            expected=4*model["fit_v4"]["panes"]
            check(info["seating_flange"]["actual_strip_count"]==expected,model_id+" Expected seating strip count not found")
            for strip in info["seating_flange"]["strips"]:
                if closed_flange:
                    check(strip["closed_edges_exactly_two_faces"],model_id+" Seat rail is not closed at strip"+str(strip["label"]))
                    check(not strip["unresolved_center_crosssections_over_2mm"],model_id+" Seat cross-sections exceed2mm intended-frame clearance at strip"+str(strip["label"]))
                    check(strip["pane_center_to_glass_mm"]["max"]<=1.5,model_id+" Seat/glass attachment gap exceeds1.5mm at strip"+str(strip["label"]))
                else:
                    check(strip["body_attachment_distance_mm"]["max"]<=3.,model_id+" Seat/body attachment gap exceeds3mm at strip"+str(strip["label"]))
                    check(strip["body_attachment_signed_mm"]["max"]<=.5,model_id+" Seat/body outer rail not fully embedded at strip"+str(strip["label"]))
                    check(strip["pane_attachment_distance_mm"]["max"]<=1.5,model_id+" Seat/glass attachment gap exceeds1.5mm at strip"+str(strip["label"]))
        else:
            check(max((d for d,p,q in boundary), default=1)<.003,model_id+" Glass boundary exceeds 3mm body clearance")
        check(info["holo"]["support_distance_mm"]["max"]<=3.,model_id+" Holo exceeds 3mm glass offset")
        check(info["holo"]["projected_edge_margin_mm"]["min"]>=2.,model_id+" Holo projects within 2mm of/beyond a glass boundary")
        for i in (1,2):
            backing=surface(bpy.data.objects[f"Console_{i}_Backing"])
            cglass=surface(bpy.data.objects[f"Console_{i}_Glass"])
            hud=surface(bpy.data.objects[f"Console_{i}_HUD"])
            fit={"index":i,"glass":overlaid_fit(cglass,backing),"hud":overlaid_fit(hud,backing)}
            has_rear=model_id=="D" and i==1 and bool(model.get("fit_v4",{}).get("rear_service_console"))
            if has_rear:
                check(len(backing["points"])==len(cglass["points"])==len(hud["points"])==8,"D rear console topology differs")
                rear=quad_subset(backing,4)
                rear_distances=[body["tree"].find_nearest(p)[3] for p in surface_samples(rear)]
                fit["rear_service_backing_to_body_mm"]=stats_mm(rear_distances)
                check(min(rear_distances)>=.0005 and max(rear_distances)<=.012,"D rear console backing fit outside .5-12mm")
            for key,target,overlay in (("glass",8.,cglass),("hud",10.,hud)):
                offsets=[(p-q).length for p,q in zip(overlay["points"],backing["points"])]
                fit[key]["corresponding_vertex_offset_mm"]=stats_mm(offsets)
                front_overlay=quad_subset(overlay,0) if has_rear else overlay
                fit[key]["original_v3_bezel_projection"]=overlaid_fit(front_overlay,original_backings[i])
                measured=fit[key]["corresponding_vertex_offset_mm"]
                check(measured["min"]>=target-1.5 and measured["max"]<=target+1.5,
                      f"{model_id} console{i} {key} vertex displacement outside {target}±1.5mm")
                check(fit[key]["support_distance_mm"]["min"]>=1.,f"{model_id} console{i} {key} clearance below1mm")
                check(fit[key]["original_v3_bezel_projection"]["projected_edge_margin_mm"]["min"]>=1.,
                      f"{model_id} console{i} {key} not inset by1mm within original v3 bezel")
            info["bottom_consoles"].append(fit)
        if model_id=="C":
            coverage=[]
            for z in (1.,1.8,2.6):
                hits=[];misses=[]
                for angle in range(0,360,2):
                    theta=math.radians(angle)
                    direction=Vector((math.sin(theta),-math.cos(theta),0))
                    loc,normal,face,distance=glass["tree"].ray_cast(Vector((0,0,z)),direction,2.)
                    if loc is None:misses.append(angle)
                    else:hits.append(distance)
                coverage.append({"z_m":z,"hits":len(hits),"missed_degrees":misses,
                                 "radius_range_m":[min(hits),max(hits)] if hits else None})
                check(not misses,f"C enclosure has radial gaps at z={z}: {misses}")
            # Independent topological patch seams. Joined, already-welded glass
            # has no duplicate internal boundaries and is covered by ray tests.
            seam_distances=[]
            for point,label,edge in edge_samples(glass,2):
                a,b=[glass["points"][index] for index in edge]
                if not (.95<point.z<2.7 and abs(a.z-b.z)>.5*(a-b).length):continue
                candidates=[distance_segment(point,glass["points"][i],glass["points"][j])
                    for i,j in glass["boundary"] if glass["labels"][i]!=label]
                if candidates:seam_distances.append(min(candidates))
            info["C_full_perimeter_ray_coverage"]=coverage
            info["C_neighbor_patch_seams_mm"]=stats_mm(seam_distances)
            if seam_distances:check(max(seam_distances)<=.0005,"C adjacent patch seams exceed .5mm")
        report["models"].append(info)
        print("CRYO_V4_FIT_MODEL "+model_id+" "+json.dumps({"body_unchanged":info["body_geometry_unchanged"],
              "glass_gap_mm":info["glass_boundary_to_body_mm"],"holo_gap_mm":info["holo"]["support_distance_mm"]}),flush=True)
    after=check_hashes(guard)
    check(not after,"Protected source/v2/v3 hash changes during audit: "+str(after))
    changed_v4=[p for p,value in v4files.items() if sha(p)!=value]
    check(not changed_v4,"New v4 asset hash changes during audit: "+str(changed_v4))
    report["protected_file_count"]=guard["count"]
    report["old_files_unchanged"]=not before and not after
    report["new_files_unchanged"]=not changed_v4
    report["status"]="NUMERICAL_FIT_PASS_VISUAL_REVIEW_REQUIRED" if not report["failures"] else "NUMERICAL_FIT_REQUIRES_REVIEW"
    args.receipt.write_text(json.dumps(report,indent=2)+"\n")
    print("CRYO_V4_FIT_RESULT "+report["status"]+" "+str(args.receipt)+" "+json.dumps(report["failures"]),flush=True)


if __name__=="__main__":
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--manifest",type=Path)
    parser.add_argument("--guard",type=Path,default=DEFAULT_GUARD)
    parser.add_argument("--receipt",type=Path,default=WORK/"cryo-fit-audit-v4.json")
    args=parser.parse_args(argv)
    if args.prepare:prepare(args.guard)
    elif args.manifest is None:parser.error("--manifest is required for validation")
    else:
        try:validate(args)
        except Exception as error:
            args.receipt.write_text(json.dumps({"status":"AUDIT_ERROR","error":str(error),"traceback":traceback.format_exc()},indent=2)+"\n")
            raise
