"""Original +X inward tunnel in centimetres; no Unreal or external packages.

Open mouth X=-15000; tube and luminous end disk finish at X=125000. Runtime
scale is (1,1,1). One material section and no generated collision geometry.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ANGULAR_SEGMENTS = 128
LONGITUDINAL_SEGMENTS = 96
BACK_CM, FRONT_CM = -15000.0, 125000.0
RADIUS_CM, FAR_RADIUS_CM = 10000.0, 6500.0
MESH_NAME, MATERIAL_NAME = "SM_WormholeTunnel", "M_WormholeTransit"


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    assert length > 1e-12
    return tuple(x / length for x in v)


def centre(u):
    bend = math.sin(math.pi * u) ** 2
    return (BACK_CM + (FRONT_CM - BACK_CM) * u,
            650.0 * bend * math.sin(2.0 * math.pi * u),
            450.0 * bend * math.cos(1.5 * math.pi * u))


def point(u, angle):
    taper = u * u * (3.0 - 2.0 * u)
    radius = RADIUS_CM + (FAR_RADIUS_CM - RADIUS_CM) * taper
    # Low angular harmonics twist gradually. No regularly spaced axial ridges.
    corrugation = (1.0 + 0.073 * math.sin(3.0 * angle - 3.1 * u)
                   + 0.042 * math.sin(5.0 * angle + 4.7 * u + 0.8)
                   + 0.019 * math.sin(8.0 * angle - 5.3 * u + 1.6))
    origin = centre(u)
    return (origin[0], origin[1] + radius * corrugation * math.cos(angle),
            origin[2] + radius * corrugation * math.sin(angle))


def normal(u, angle):
    step = 1e-5
    axial = subtract(point(u + step, angle), point(u - step, angle))
    angular = subtract(point(u, angle + step), point(u, angle - step))
    return normalize(cross(axial, angular))


def build():
    vertices, normals, uvs, faces = [], [], [], []
    stride = ANGULAR_SEGMENTS + 1
    for axial in range(LONGITUDINAL_SEGMENTS + 1):
        u = axial / LONGITUDINAL_SEGMENTS
        for angular in range(stride):
            # Exactly identical seam coordinates/normals with distinct UVs.
            angle = math.tau * (angular % ANGULAR_SEGMENTS) / ANGULAR_SEGMENTS
            vertices.append(point(u, angle))
            normals.append(normal(u, angle))
            uvs.append((u, angular / ANGULAR_SEGMENTS))
    for axial in range(LONGITUDINAL_SEGMENTS):
        for angular in range(ANGULAR_SEGMENTS):
            a = axial * stride + angular
            b, c, d = a + stride, a + stride + 1, a + 1
            faces.extend(((a, b, c), (a, c, d)))
    side_vertices, side_triangles = len(vertices), len(faces)
    cap_start = len(vertices)
    for angular in range(stride):
        angle = math.tau * (angular % ANGULAR_SEGMENTS) / ANGULAR_SEGMENTS
        vertices.append(point(1.0, angle))
        normals.append((-1.0, 0.0, 0.0))
        # Cap U in [2,3] encodes radial fraction; V remains angle.
        uvs.append((3.0, angular / ANGULAR_SEGMENTS))
    for angular in range(ANGULAR_SEGMENTS):
        centre_index = len(vertices)
        vertices.append(centre(1.0))
        normals.append((-1.0, 0.0, 0.0))
        uvs.append((2.0, (angular + 0.5) / ANGULAR_SEGMENTS))
        faces.append((centre_index, cap_start + angular + 1, cap_start + angular))

    for axial in range(LONGITUDINAL_SEGMENTS + 1):
        a, b = axial * stride, axial * stride + ANGULAR_SEGMENTS
        assert vertices[a] == vertices[b] and normals[a] == normals[b]
        assert uvs[a][1] == 0.0 and uvs[b][1] == 1.0
    minimum_dot, minimum_radius = 1.0, float("inf")
    for face in faces:
        a, b, c = (vertices[i] for i in face)
        face_normal = normalize(cross(subtract(b, a), subtract(c, a)))
        for index in face:
            dot = sum(x * y for x, y in zip(face_normal, normals[index]))
            assert dot > 0.9, "Non-inward/degenerate winding or unexpected faceting"
            minimum_dot = min(minimum_dot, dot)
    for index, (vertex, uv) in enumerate(zip(vertices, uvs)):
        assert all(math.isfinite(value) for value in vertex + normals[index] + uv)
        assert abs(sum(value * value for value in normals[index]) - 1.0) < 1e-8
        if index < side_vertices:
            local = subtract(vertex, centre(uv[0]))
            minimum_radius = min(minimum_radius, math.hypot(local[1], local[2]))
            assert sum(local[k] * normals[index][k] for k in (1, 2)) < 0.0
    report = {
        "name": MESH_NAME, "material": MATERIAL_NAME, "units": "centimetres",
        "forward_axis": "+X", "runtime_scale": [1, 1, 1],
        "back_x_cm": BACK_CM, "front_x_cm": FRONT_CM,
        "length_cm": FRONT_CM - BACK_CM, "base_radius_cm": RADIUS_CM,
        "far_base_radius_cm": FAR_RADIUS_CM, "minimum_wall_radius_cm": minimum_radius,
        "angular_segments": ANGULAR_SEGMENTS, "longitudinal_segments": LONGITUDINAL_SEGMENTS,
        "vertices": len(vertices), "triangles": len(faces), "side_triangles": side_triangles,
        "cap_triangles": len(faces) - side_triangles,
        "bounds_min_cm": [min(v[k] for v in vertices) for k in range(3)],
        "bounds_max_cm": [max(v[k] for v in vertices) for k in range(3)],
        "material_sections": 1, "minimum_winding_normal_dot": minimum_dot,
        "uv_contract": "Wall U=longitudinal[0,1], V=angle[0,1]; cap U=2+radius[0,1], V=angle[0,1]",
        "checks": {"inward_winding": True, "unit_normals": True, "closed_uv_seam": True,
                   "finite_geometry": True, "nondegenerate_triangles": True},
        "entrance_open": True, "far_end_disk": True,
    }
    return vertices, normals, uvs, faces, report


def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    vertices, normals, uvs, faces, report = build()
    mesh_path = output / (MESH_NAME + ".obj")
    lines = ["# Original SpaceSurvival inward tunnel; +X; centimetres",
             "mtllib WormholeTransit.mtl", "o " + MESH_NAME]
    lines.extend("v " + " ".join(f"{value:.9f}" for value in v) for v in vertices)
    lines.extend("vt " + " ".join(f"{value:.9f}" for value in uv) for uv in uvs)
    lines.extend("vn " + " ".join(f"{value:.9f}" for value in n) for n in normals)
    lines.extend(("usemtl " + MATERIAL_NAME, "s 1"))
    lines.extend("f " + " ".join(f"{i+1}/{i+1}/{i+1}" for i in face) for face in faces)
    mesh_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (output / "WormholeTransit.mtl").write_text(
        "newmtl " + MATERIAL_NAME + "\nKd 0.8 0.4 0.7\n", encoding="utf-8", newline="\n")
    report["obj_sha256"] = hashlib.sha256(mesh_path.read_bytes()).hexdigest()
    (output / "Geometry.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(generate(parser.parse_args().output), indent=2))
