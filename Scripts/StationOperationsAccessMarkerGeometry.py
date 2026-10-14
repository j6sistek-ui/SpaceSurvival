"""Pure, bounded geometry for the five physical Operations access markers.

Coordinates are centimetres, local +X points toward the existing desk. This
module creates no Unreal objects or files. The author must prove actual floor
support, original service access and exact saved producer before placement.
"""
import math


OUTER_RADIUS_CM = 78.
INNER_RADIUS_CM = 62.
MAX_HEIGHT_CM = 1.5
SEGMENTS = 12
ARC_STEPS = 8
GAP_DEGREES = 2.


def geometry():
    positions, normals, uvs, triangles, material_ids = [], [], [], [], []

    def face(points, material):
        if len(points) < 3:
            raise ValueError('A physical marker face needs at least three vertices')
        a, b, c = points[:3]
        ab, ac = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
        normal = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
        length = math.sqrt(sum(value*value for value in normal))
        if length < 1.e-8:
            raise ValueError('Degenerate marker face')
        normal = [value/length for value in normal]
        start = len(positions)
        positions.extend([list(point) for point in points])
        normals.extend([normal[:] for _ in points])
        uvs.extend([[point[0]/156.+.5, point[1]/156.+.5] for point in points])
        for index in range(1, len(points)-1):
            triangles.append([start, start+index, start+index+1])
            material_ids.append(material)

    def swept_profile(profile, angle_start, angle_end, material):
        def point(angle, row):
            return [row[0]*math.cos(angle), row[0]*math.sin(angle), row[1]]
        angles = [math.radians(angle_start+(angle_end-angle_start)*i/ARC_STEPS)
                  for i in range(ARC_STEPS+1)]
        for angle_a, angle_b in zip(angles, angles[1:]):
            for index, row in enumerate(profile):
                following = profile[(index+1) % len(profile)]
                face([point(angle_a, row), point(angle_b, row), point(angle_b, following),
                      point(angle_a, following)], material)
        face([point(angles[0], row) for row in profile], material)
        face([point(angles[-1], row) for row in reversed(profile)], material)

    body = [(62., .05), (78., .05), (78., .85), (77.45, 1.38),
            (62.55, 1.38), (62., .85)]
    lens = [(66.7, 1.38), (68.9, 1.38), (68.9, 1.43), (68.82, 1.49),
            (66.78, 1.49), (66.7, 1.43)]
    for segment in range(SEGMENTS):
        middle = segment*360./SEGMENTS
        half = (360./SEGMENTS-GAP_DEGREES)/2.
        swept_profile(body, middle-half, middle+half, 0)
        swept_profile(lens, middle-half, middle+half, 1)
        for offset in (-10., 10.):
            angle = math.radians(middle+offset)
            centre = [73.8*math.cos(angle), 73.8*math.sin(angle)]
            bottom, top = [], []
            for index in range(6):
                theta = math.radians(index*60.)
                point = [centre[0]+.8*math.cos(theta), centre[1]+.8*math.sin(theta)]
                bottom.append(point+[1.38]); top.append(point+[1.47])
            for index in range(6):
                following = (index+1) % 6
                face([bottom[index], bottom[following], top[following], top[index]], 2)
            face(list(reversed(bottom)), 2)
            face(top, 2)
    # Two raised inset branches form a physical desk-directed chevron, not text.
    for polygon in (
        [(71.2, -5.), (75.5, 0.), (73.1, 0.), (70., -3.6)],
        [(75.5, 0.), (71.2, 5.), (70., 3.6), (73.1, 0.)],
    ):
        face([[x, y, 1.49] for x, y in polygon], 1)
    result = {'positions': positions, 'normals': normals, 'uvs': uvs,
              'triangles': triangles, 'material_ids': material_ids,
              'material_roles': ['GRAPHITE_SATIN_FRAME', 'SLOW_ACCENT_LENS', 'TITANIUM_FASTENERS'],
              'bounds_cm': [[min(point[j] for point in positions) for j in range(3)],
                            [max(point[j] for point in positions) for j in range(3)]],
              'desk_direction_local': [1., 0., 0.], 'segment_count': SEGMENTS,
              'outer_radius_cm': OUTER_RADIUS_CM, 'inner_radius_cm': INNER_RADIUS_CM,
              'height_max_cm': MAX_HEIGHT_CM}
    validate(result)
    return result


def validate(data):
    count = len(data['positions'])
    if not (0 < count < 10000 and len(data['triangles']) < 4096):
        raise ValueError('Marker exceeded bounded mesh budget')
    if len(data['normals']) != count or len(data['uvs']) != count or \
            len(data['material_ids']) != len(data['triangles']):
        raise ValueError('Physical marker buffers do not agree')
    for point in data['positions']:
        radius = math.hypot(point[0], point[1])
        if not (62.-1.e-8 <= radius <= 78.+1.e-8 and 0. <= point[2] <= 1.5):
            raise ValueError('Marker leaves reviewed radius/height footprint')
    for triangle, material in zip(data['triangles'], data['material_ids']):
        if material not in (0, 1, 2) or len(set(triangle)) != 3 or \
                any(index < 0 or index >= count for index in triangle):
            raise ValueError('Invalid physical marker triangle/slot')
        a, b, c = [data['positions'][index] for index in triangle]
        ab, ac = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
        cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
        normal = data['normals'][triangle[0]]
        if sum(cross[j]*normal[j] for j in range(3)) <= 1.e-8:
            raise ValueError('Marker winding/normal mismatch')
    if set(data['material_ids']) != {0, 1, 2}:
        raise ValueError('Marker requires physical frame/lens/fastener slots')
