"""Pure geometry checks for floor-only material masks; no Unreal or filesystem writes.

Triangle normals are geometric evidence, not a claim about interpolated shader
vertex normals. Native shader compilation and saved-world pixels remain gates.
"""
import math


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def face_data(geometry):
    result = []
    for index, face in enumerate(geometry['triangles']):
        p = [geometry['vertices'][i] for i in face]
        a = [p[1][i]-p[0][i] for i in range(3)]
        b = [p[2][i]-p[0][i] for i in range(3)]
        n = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        length = math.sqrt(sum(v*v for v in n))
        if length <= 1.e-10:
            continue
        result.append({'id': index, 'p': p, 'nz': abs(n[2]/length), 'area': length*.5,
                       'z': [min(q[2] for q in p), max(q[2] for q in p)],
                       'center': [sum(q[i] for q in p)/3 for i in range(3)]})
    return result


def merge(intervals, tolerance=0.):
    result = []
    for low, high in sorted(intervals):
        require(low <= high, 'Invalid mask interval')
        if result and low <= result[-1][1]+tolerance:
            result[-1][1] = max(result[-1][1], high)
        else:
            result.append([low, high])
    return result


def subtract(intervals, cuts):
    result = intervals
    for a, b in merge(cuts):
        next_result = []
        for low, high in result:
            if b < low or a > high:
                next_result.append([low, high])
            else:
                if low < a:
                    next_result.append([low, a-1.e-6])
                if b < high:
                    next_result.append([b+1.e-6, high])
        result = next_result
    return result


def selected(z, intervals):
    return any(low <= z <= high for low, high in intervals)


def mask(geometry, kind, normal_min=.9):
    """Exact foundations or upper envelope of a measured isolated floor mesh.

    For child floors a bounded XY grid finds the top triangle over each face's
    centroid. Rejected flat lower faces are removed from height intervals. Any
    remaining selected/rejected height ambiguity fails before asset creation.
    """
    faces = face_data(geometry)
    require(0 < len(faces) <= 100000, 'Floor mask geometry exceeds reviewed cap')
    if kind == 'owner_deck_top':
        intervals, normal_min = [[-.01, .01]], .9
        chosen = [f for f in faces if f['nz'] >= normal_min and all(selected(z, intervals) for z in f['z'])]
        require(chosen and all(f['z'][0] > -.001 for f in chosen), 'Owner top interval selected an underside')
        require(all(not selected(f['center'][2], intervals) for f in faces
                    if f['nz'] >= normal_min and f['z'][1] < -199), 'Owner underside entered mask')
    elif kind == 'owner_ring_upper':
        intervals, normal_min = [[4.72, 4.90]], .7
        chosen = [f for f in faces if f['nz'] >= normal_min and selected(f['center'][2], intervals)]
        require(chosen and all(f['z'][0] > 4.70 and f['z'][1] < 4.91 for f in chosen),
                'Ring interval includes a lower layer or tall wall cap')
        require(all(not selected(f['center'][2], intervals) for f in faces
                    if f['nz'] >= normal_min and (f['z'][1] < 4.1 or f['z'][0] > 5.)),
                'Ring lower layer/wall cap entered mask')
    else:
        require(kind == 'child_top_envelope', 'Unknown floor role')
        horizontal = [f for f in faces if f['nz'] >= normal_min]
        require(horizontal, 'No measured walking surface at reviewed normal threshold')
        xy_min = [min(p[i] for f in faces for p in f['p']) for i in (0, 1)]
        xy_max = [max(p[i] for f in faces for p in f['p']) for i in (0, 1)]
        steps = [max((xy_max[i]-xy_min[i])/32, 1.e-5) for i in (0, 1)]
        def cell(x, i):
            return max(0, min(31, int((x-xy_min[i])/steps[i])))
        grid = {}
        for f in horizontal:
            for x in range(cell(min(p[0] for p in f['p']), 0), cell(max(p[0] for p in f['p']), 0)+1):
                for y in range(cell(min(p[1] for p in f['p']), 1), cell(max(p[1] for p in f['p']), 1)+1):
                    grid.setdefault((x, y), []).append(f)
        chosen, rejected = [], []
        query_count = 0
        for f in horizontal:
            x, y, z = f['center']
            top = z
            for other in grid[(cell(x, 0), cell(y, 1))]:
                query_count += 1
                require(query_count <= 35000000, 'Floor upper-envelope query cap exceeded')
                a, b, c = other['p']
                denom = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(denom) < 1.e-10:
                    continue
                wa = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denom
                wb = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denom
                wc = 1-wa-wb
                if min(wa, wb, wc) >= -1.e-7:
                    top = max(top, wa*a[2]+wb*b[2]+wc*c[2])
            (chosen if top-z <= .002 else rejected).append(f)
        require(chosen, 'No measured top-envelope faces')
        intervals = merge([[f['z'][0]-.001, f['z'][1]+.001] for f in chosen])
        # Coplanar duplicated thin planes have no distinct volumetric underside.
        # Exclude genuine lower flat levels, including an endpoint of a ramp.
        cuts = [[f['z'][0]-.001, f['z'][1]+.001] for f in rejected if f['z'][1]-f['z'][0] <= .002]
        intervals = subtract(intervals, cuts)
        ambiguous = [f for f in rejected if selected(f['center'][2], intervals)]
        missing = [f for f in chosen if not selected(f['center'][2], intervals)]
        require(not ambiguous and not missing,
                'Height/normal-only mask is ambiguous; rejected='+str(len(ambiguous))+' missing='+str(len(missing)))
    require(0 < len(intervals) <= 96, 'Unbounded/disconnected floor mask intervals')
    # No interpolation or texture sampling changes. Absolute normal handles
    # retained negative scales/inverted winding; local height selects the layer.
    # Simpler sequential max statements avoid nested generated expression risk.
    code = 'float h=0.0;\n'+''.join('h=max(h,step('+format(lo,'.9g')+',P.z)*step(P.z,'+
           format(hi,'.9g')+'));\n' for lo,hi in intervals)
    code += 'return h*step('+format(normal_min,'.9g')+',abs(normalize(N).z));'
    return {'kind': kind, 'normal_min': normal_min, 'source_local_height_intervals_cm': intervals,
            'selected_triangle_count': len(chosen), 'selected_area_cm2': sum(f['area'] for f in chosen),
            'total_nondegenerate_triangles': len(faces), 'code': code,
            'normal_evidence': 'Triangle geometric normals; shader uses actual VertexNormalWS. Pixels pending.',
            'underside_sidewall_geometry_unchanged': True}
