"""Encode intended Unreal XYZ geometry for the legacy FBX/OBJ importer.

UE5.8 FFbxDataConverter::ConvertPos/ConvertDir always negate Y, independently
of bConvertScene. Reflect position/normal Y and reverse each triangle's corner
order so imported positions and normals match the intended geometry and the
right-handed OBJ still has outward-facing winding. UV/material data is retained.
"""
import hashlib
import math
from pathlib import Path

SPACE = "UNREAL_FBX_REFLECT_Y_REVERSE_WINDING_V1"
MARKER = "# SS_OBJ_SPACE " + SPACE


def flip_y(line):
    fields = line.split()
    assert fields[0] in ("v", "vn") and len(fields) == 4
    assert all(math.isfinite(float(value)) for value in fields[1:])
    fields[2] = fields[2][1:] if fields[2].startswith("-") else "-" + fields[2]
    return " ".join(fields)


def reverse_triangle(line):
    fields = line.split()
    assert fields[0] == "f" and len(fields) == 4, "Only audited triangles are supported"
    return " ".join((fields[0], fields[1], fields[3], fields[2]))


def encode(path):
    path = Path(path)
    source_bytes = path.read_bytes()
    source = source_bytes.decode("utf-8")
    assert MARKER not in source, "Refuse a second handedness conversion"
    counts = {"positions": 0, "normals": 0, "triangles": 0}
    output = [MARKER]
    for line in source.splitlines():
        if line.startswith(("v ", "vn ")):
            changed = flip_y(line)
            assert flip_y(changed) == line, "Position/normal reflection must round trip exactly"
            counts["positions" if line.startswith("v ") else "normals"] += 1
        elif line.startswith("f "):
            changed = reverse_triangle(line)
            assert reverse_triangle(changed) == line, "Corner/UV/normal associations must round trip exactly"
            counts["triangles"] += 1
        else:
            changed = line
        output.append(changed)
    assert all(counts.values()), counts
    encoded = "\n".join(output) + "\n"
    encoded_bytes = encoded.encode("utf-8")
    path.write_bytes(encoded_bytes)
    return {"space": SPACE, **counts,
            "source_line_endings": "CRLF" if b"\r\n" in source_bytes else "LF",
            "unencoded_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "encoded_sha256": hashlib.sha256(encoded_bytes).hexdigest(),
            "position_normal_and_corner_round_trip": True}
