"""Create isolated, vector-mesh cryo displays; never overwrite v4 assets.

Run in installed Blender with -- --apply. Native Unreal supplies animation.
No image is edited or generated here: glyphs use the existing Bahnschrift font.
"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse, hashlib, json, math, struct, sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import upgrade_console_geometry as common

WORK=Path(__file__).resolve().parent
OUT=WORK.parent/'outputs/Cryo_Comparison'
SOURCE=OUT/'assembly_fit_v4_4.json'
DEST=OUT/'assembly_displays_v5_2.json'
FONT=Path('C:/Windows/Fonts/bahnschrift.ttf')
HUD_BOUNDS=(.12,.43,.14,.37)


def world_geometry(ob):
    return [ob.matrix_world@v.co for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons]


def mesh(name, points, faces, uv, material):
    data=bpy.data.meshes.new(name+'_Mesh')
    data.from_pydata(points,[],faces); data.update()
    layer=data.uv_layers.new(name='UVMap')
    for face in data.polygons:
        for li in face.loop_indices:layer.data[li].uv=uv[data.loops[li].vertex_index]
    data.materials.append(material)
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    return ob


def materials():
    make=lambda n,c,m,r,a=1,e=0:common.simple_material(bpy,n,c,m,r,a,e)
    return {'glyph':make('M_Cryo_VectorGlyph_v5',(.32,.81,1),0,.35,1,1.4),
            'holo_panel':make('M_Cryo_HoloInset_v5',(.025,.16,.21),0,.18,.14,0),
            'lens':make('M_Cryo_DisplayLens_v5',(.22,.55,.66),0,.07,.13,0),
            'backing':make('M_Cryo_DisplayBacking_v5',(.003,.009,.014),.25,.32),
            'frame':make('M_Cryo_DisplayFrame_v5',(.012,.055,.075),.65,.27)}


def canonical_quad(ob, polygon):
    """Read each front/rear face by its own UVs; never assume vertex order."""
    uv=ob.data.uv_layers.active
    values={tuple(round(float(v),5) for v in uv.data[li].uv):ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co for li in polygon.loop_indices}
    return [values[p] for p in [(0.,0.),(1.,0.),(1.,1.),(0.,1.)]]


def quad_point(points,u,v):
    return points[0]*(1-u)*(1-v)+points[1]*u*(1-v)+points[2]*u*v+points[3]*(1-u)*v


class Grid:
    def __init__(self, points, nx, ny):
        self.points=points;self.nx=nx;self.ny=ny
        assert len(points)==(nx+1)*(ny+1)
    def sample(self,u,v):
        x=min(self.nx-1,int(max(0,min(1,u))*self.nx)); y=min(self.ny-1,int(max(0,min(1,v))*self.ny))
        fu=u*self.nx-x;fv=v*self.ny-y;i=y*(self.nx+1)+x
        p00,p10,p11,p01=[self.points[k] for k in [i,i+1,i+self.nx+2,i+self.nx+1]]
        # Our generated backing/panel grids use this explicit diagonal.
        if fv<=fu:
            p=p00*(1-fu)+p10*(fu-fv)+p11*fv;n=(p10-p00).cross(p11-p00).normalized()
        else:
            p=p00*(1-fv)+p11*fu+p01*(fv-fu);n=(p11-p00).cross(p01-p00).normalized()
        return p,n
    def geometry(self,offset=0):
        points=[];uv=[];faces=[]
        for j in range(self.ny+1):
            for i in range(self.nx+1):
                p,n=self.sample(i/self.nx,j/self.ny);points.append(p+n*offset);uv.append((i/self.nx,j/self.ny))
        for j in range(self.ny):
            for i in range(self.nx):
                a=j*(self.nx+1)+i;faces.extend([(a,a+1,a+self.nx+2),(a,a+self.nx+2,a+self.nx+1)])
        return points,faces,uv


class GlassPatch:
    """Sample the original actual loop triangles, not a replacement approximation."""
    def __init__(self,ob):
        ob.data.calc_loop_triangles();self.points=[ob.matrix_world@v.co for v in ob.data.vertices]
        normal_matrix=ob.matrix_world.to_3x3().inverted().transposed()
        self.cells={};self.normals=[(normal_matrix@v.normal).normalized() for v in ob.data.vertices];self.ob=ob
        uv=ob.data.uv_layers.active
        for tri in ob.data.loop_triangles:
            if max(tri.vertices)>=1353:continue
            coords=[Vector(uv.data[li].uv) for li in tri.loops]
            x=min(31,int(sum(p.x for p in coords)/3*32));y=min(39,int(sum(p.y for p in coords)/3*40))
            self.cells.setdefault((x,y),[]).append((list(tri.vertices),coords))
        assert len(self.cells)==32*40
    def sample(self,u,v):
        point=Vector((u,v));key=(min(31,int(u*32)),min(39,int(v*40)))
        for indices,coords in self.cells[key]:
            a,b,c=coords;v0=b-a;v1=c-a;v2=point-a
            den=v0.x*v1.y-v1.x*v0.y
            wb=(v2.x*v1.y-v1.x*v2.y)/den;wc=(v0.x*v2.y-v2.x*v0.y)/den;wa=1-wb-wc
            if min(wa,wb,wc)>=-1e-5:
                ps=[self.points[k] for k in indices]
                p=ps[0]*wa+ps[1]*wb+ps[2]*wc
                n=(ps[1]-ps[0]).cross(ps[2]-ps[0]).normalized()
                if n.y>0:n=-n
                return p,n
        raise RuntimeError('Front glass UV sample outside triangle')

    def clipped_ui(self, name, canvas, bounds, offset, material):
        """Clip every glyph/panel face to source glass triangles before offsetting.

        Independent display triangles would bridge the irregular glazing grid.
        Clipping preserves the actual underlying surface at triangle interiors.
        """
        u0,u1,v0,v1=bounds;points=[];faces=[];uv=[]
        def cross(a,b):return a.x*b.y-a.y*b.x
        def clip(poly, triangle):
            area=cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);sign=1 if area>0 else -1
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                if not poly:break
                output=[];prev=poly[-1];dp=sign*cross(b-a,prev-a)
                for cur in poly:
                    dc=sign*cross(b-a,cur-a)
                    if (dc>=-1e-10)!=(dp>=-1e-10):output.append(prev+(cur-prev)*(dp/(dp-dc)))
                    if dc>=-1e-10:output.append(cur)
                    prev=cur;dp=dc
                poly=output
            return poly
        for face in canvas.faces:
            poly=[Vector((u0+canvas.points[k][0]*(u1-u0),v0+canvas.points[k][1]*(v1-v0))) for k in face]
            xmin=max(0,min(31,int(min(p.x for p in poly)*32)));xmax=max(0,min(31,int(max(p.x for p in poly)*32)))
            ymin=max(0,min(39,int(min(p.y for p in poly)*40)));ymax=max(0,min(39,int(max(p.y for p in poly)*40)))
            for y in range(ymin,ymax+1):
                for x in range(xmin,xmax+1):
                    for indices,coords in self.cells[(x,y)]:
                        clipped=clip(poly,coords)
                        if len(clipped)<3:continue
                        ps=[self.points[k] for k in indices];a,b,c=coords;den=cross(b-a,c-a)
                        base=len(points)
                        for p in clipped:
                            wb=cross(p-a,c-a)/den;wc=cross(b-a,p-a)/den;wa=1-wb-wc
                            n=(self.normals[indices[0]]*wa+self.normals[indices[1]]*wb+self.normals[indices[2]]*wc).normalized()
                            if n.y>0:n=-n
                            points.append(ps[0]*wa+ps[1]*wb+ps[2]*wc+n*offset)
                            uv.append(((p.x-u0)/(u1-u0),(p.y-v0)/(v1-v0)))
                        for k in range(1,len(clipped)-1):
                            if abs(cross(clipped[k]-clipped[0],clipped[k+1]-clipped[0]))>1e-12:faces.append((base,base+k,base+k+1))
        return mesh(name,points,faces,uv,material)


class Canvas:
    def __init__(self,aspect):self.aspect=aspect;self.points=[];self.faces=[]
    def polygon(self,points):
        # Convex small 2D shapes only; positive UV winding.
        off=len(self.points);self.points.extend(points)
        for k in range(1,len(points)-1):self.faces.append((off,off+k,off+k+1))
    def line(self,a,b,width=.006):
        # Width is measured relative to panel width, accounting for aspect.
        width=max(width,.0075)
        delta=Vector((b[0]-a[0],(b[1]-a[1])*self.aspect));side=Vector((-delta.y,delta.x)).normalized()*width/2
        sx,sy=side.x,side.y/self.aspect
        self.polygon([(a[0]-sx,a[1]-sy),(b[0]-sx,b[1]-sy),(b[0]+sx,b[1]+sy),(a[0]+sx,a[1]+sy)])
    def rect(self,x,y,w,h):self.polygon([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
    def text(self,value,x,y,height,max_width=.84):
        data=bpy.data.curves.new('TemporaryGlyphs','FONT');data.body=value;data.font=bpy.data.fonts.load(str(FONT),check_existing=True)
        data.size=1;data.resolution_u=6;data.fill_mode='BOTH';data.align_x='LEFT';data.align_y='BOTTOM_BASELINE';data.offset=.008
        ob=bpy.data.objects.new('TemporaryGlyphs',data);bpy.context.collection.objects.link(ob)
        bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles()
        raw=[v.co.copy() for v in m.vertices];minx=min(p.x for p in raw);maxx=max(p.x for p in raw);miny=min(p.y for p in raw);maxy=max(p.y for p in raw)
        scale=min(height*self.aspect/(maxy-miny),max_width/(maxx-minx));off=len(self.points)
        self.points.extend((x+(p.x-minx)*scale,y+(p.y-miny)*scale/self.aspect) for p in raw)
        for tri in m.loop_triangles:
            a,b,c=[raw[i] for i in tri.vertices]
            ids=tuple(off+i for i in tri.vertices)
            if (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)<0:ids=ids[::-1]
            self.faces.append(ids)
        ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True);bpy.data.curves.remove(data)
    def mapped(self,name,sampler,offset,material,max_uv_edge=.025):
        points=[];faces=[];uv=[]
        def emit(a,b,c,depth=0):
            pairs=[(a,b,c),(b,c,a),(c,a,b)];long=max(pairs,key=lambda t:(Vector(t[1])-Vector(t[0])).length)
            if (Vector(long[1])-Vector(long[0])).length>max_uv_edge and depth<10:
                a0,b0,c0=long;mid=tuple((Vector(a0)+Vector(b0))*.5);emit(a0,mid,c0,depth+1);emit(mid,b0,c0,depth+1);return
            base=len(points)
            for coord in [a,b,c]:
                p,n=sampler(*coord);points.append(p+n*offset);uv.append(coord)
            faces.append((base,base+1,base+2))
        for face in self.faces:emit(*(self.points[i] for i in face))
        return mesh(name,points,faces,uv,material)


def design(kind,aspect):
    ui=Canvas(aspect)
    # Deliberate corner brackets, not an opaque rectangular poster.
    for x,y,dx,dy in [(.04,.04,1,1),(.96,.04,-1,1),(.04,.96,1,-1),(.96,.96,-1,-1)]:
        ui.line((x,y),(x+dx*.08,y),.004);ui.line((x,y),(x,y+dy*.06),.004)
    if kind=='holo':
        ui.text('STASIS',.10,.80,.105);ui.text('SUBJECT / 03',.10,.68,.048)
        ui.text('-196 C',.10,.48,.125);ui.text('VITALS STABLE',.10,.34,.052)
        points=[(.10,.20),(.27,.20),(.31,.27),(.36,.12),(.42,.24),(.47,.20),(.88,.20)]
        for a,b in zip(points,points[1:]):ui.line(a,b,.006)
        ui.text('CRYO LINK  /  ONLINE',.10,.07,.035)
    elif kind=='status':
        ui.text('ACORNAUT',.11,.88,.043);ui.text('CRYO 03',.11,.75,.075)
        ui.line((.11,.69),(.88,.69),.005)
        ui.text('CORE TEMP',.11,.60,.04);ui.text('-196 C',.11,.47,.085)
        ui.text('COOLANT',.11,.35,.04)
        for i in range(8):ui.rect(.11+i*.09,.27,.06,.035)
        ui.text('SYSTEM NOMINAL',.11,.14,.035);ui.text('STASIS ACTIVE',.11,.07,.035)
    else:
        ui.text('ACORNAUT / CRYO',.09,.82,.08)
        ui.line((.09,.75),(.91,.75),.005)
        ui.text('COOLANT',.09,.62,.065);ui.text('100%',.09,.39,.18,max_width=.38)
        for i,h in enumerate([.10,.17,.13,.23,.19,.27,.24]):ui.rect(.56+i*.046,.39,.025,h)
        ui.line((.09,.29),(.91,.29),.004)
        ui.text('-196 C',.09,.12,.10,max_width=.33);ui.text('STASIS ACTIVE',.48,.13,.067,max_width=.43)
    return ui


def combine(name,objects,material):
    points=[];faces=[];uv=[]
    for ob in objects:
        ps,fs=world_geometry(ob);base=len(points);points.extend(ps)
        faces.extend(tuple(base+k for k in f) for f in fs)
        pervert={}
        for face in ob.data.polygons:
            for li in face.loop_indices:pervert[ob.data.loops[li].vertex_index]=tuple(ob.data.uv_layers.active.data[li].uv)
        uv.extend(pervert[i] for i in range(len(ps)))
        bpy.data.objects.remove(ob,do_unlink=True)
    return mesh(name,points,faces,uv,material)


def perimeter_frame(grid,material,name):
    points=[];faces=[];uv=[]
    ring=[(i/grid.nx,0) for i in range(grid.nx)]+[(1,j/grid.ny) for j in range(grid.ny)]+[(1-i/grid.nx,1) for i in range(grid.nx)]+[(0,1-j/grid.ny) for j in range(grid.ny)]
    for i,coord in enumerate(ring):
        p,n=grid.sample(*coord);q,_=grid.sample(*ring[(i+1)%len(ring)]);side=n.cross((q-p).normalized())*.003;base=len(points)
        points.extend([p-side,q-side,q+side,p+side,p-side+n*.009,q-side+n*.009,q+side+n*.009,p+side+n*.009]);uv.extend([(0,0),(1,0),(1,1),(0,1)]*2)
        faces.extend(tuple(base+k for k in f) for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    return mesh(name,points,faces,uv,material)


def fitted_console(ob,face,tree,expand_u=.025,expand_v=.055,inset_left=.04):
    corners=canonical_quad(ob,face)
    n=(corners[1]-corners[0]).cross(corners[3]-corners[0]).normalized()
    points=[];deltas=[];inner=[]
    for j in range(9):
        for i in range(13):
            u=-expand_u+(1+2*expand_u)*i/12;v=-expand_v+(1+2*expand_v)*j/8
            p=quad_point(corners,u,v);hit,_,_,dist=tree.ray_cast(p+n*.10,-n,.24)
            assert hit is not None,'Missing screen support under expanded cover'
            delta=(hit-p).dot(n);deltas.append(delta)
            assert abs(delta)<.060,'Coverage has left the measured original bezel recess'
            if .08<u<.92 and .08<v<.92:inner.append(delta)
            points.append(hit+n*.003)
    # Keep typography and lens smooth. A dark fitted rim covers the original
    # perimeter print and closes the space down to irregular source recesses.
    lift=max(0,max(inner)+.001);assert lift<.006,'Interior requires a redesigned mounting depth'
    clean=Grid([quad_point(corners,inset_left+(.96-inset_left)*i/12,.04+.92*j/8)+n*lift for j in range(9) for i in range(13)],12,8)
    cover=Grid(points,12,8)
    return clean,cover,{'expanded_uv':[-expand_u,1+expand_u,-expand_v,1+expand_v],
        'source_projection_delta_mm':[min(deltas)*1000,max(deltas)*1000],
        'inner_projection_delta_mm':[min(inner)*1000,max(inner)*1000],
        'clean_display_lift_mm':lift*1000,'display_inset_uv':[inset_left,.96,.04,.96],
        'normal':list(n),'samples':len(points)}


def backing_with_fitted_rim(clean,cover,material,tree=None):
    ps,fs,uv=clean.geometry(0)
    ring=[(i/clean.nx,0) for i in range(clean.nx)]+[(1,j/clean.ny) for j in range(clean.ny)]+[(1-i/clean.nx,1) for i in range(clean.nx)]+[(0,1-j/clean.ny) for j in range(clean.ny)]
    base=len(ps);steps=8 if tree else 1
    for coord in ring:
        inner,n=clean.sample(*coord);outer=cover.sample(*coord)[0]
        for j in range(steps+1):
            p=inner.lerp(outer,j/steps)
            if tree:
                hit,_,_,_=tree.ray_cast(p+n*.10,-n,.25)
                assert hit is not None,'Fitted coverage rim has lost body support'
                clearance=(p-hit).dot(n)
                if clearance<.001:p+=n*(.001-clearance)
            ps.append(p);uv.append(coord)
    for i in range(len(ring)):
        for j in range(steps):
            a=base+i*(steps+1)+j;b=base+((i+1)%len(ring))*(steps+1)+j;fs.extend([(a,b,b+1),(a,b+1,a+1)])
    return mesh('PartBacking',ps,fs,uv,material)


def main(apply=False,only=None):
    assert not (apply and only),'Partial authoring cannot become canonical manifest'
    source=json.loads(SOURCE.read_text());result=deepcopy(source)
    protect={str(SOURCE):common.sha(SOURCE),str(FONT):common.sha(FONT)}
    for model in source['models']:
        for key in ('source','editable_blend','finished_glb'):protect[model[key]]=common.sha(model[key])
        for row in model['components']:protect[row['file']]=common.sha(row['file'])
    for revision in ['v5','v5_1']:
        trial_manifest=OUT/('assembly_displays_'+revision+'.json')
        if trial_manifest.exists():
            protect[str(trial_manifest)]=common.sha(trial_manifest)
            for m in json.loads(trial_manifest.read_text())['models']:
                for key in ('editable_blend','finished_glb'):protect[m[key]]=common.sha(m[key])
                for row in m['components']:protect[row['file']]=common.sha(row['file'])
    if apply:assert not DEST.exists(),'Preserve existing v5 manifest'
    receipt={'status':'DISPLAY_V5_DRY_RUN','utc':datetime.now(timezone.utc).isoformat(),'source_manifest':str(SOURCE),
        'source_manifest_sha256':common.sha(SOURCE),'author_script_sha256':common.sha(__file__),
        'font':str(FONT),'font_sha256':common.sha(FONT),'models':[]}
    for model in result['models']:
        if only and model['id']!=only:continue
        bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False);bpy.context.view_layer.update()
        original={r['name']:bpy.data.objects[r['name']] for r in model['components']}
        signatures={n:common.mesh_signature(ob) for n,ob in original.items()}
        mats=materials();bodypoints,bodyfaces=world_geometry(original['Body']);tree=BVHTree.FromPolygons(bodypoints,bodyfaces)
        replacements={};details=[]
        smooth_glass=original['Glass'].copy();smooth_glass.data=original['Glass'].data.copy()
        bpy.context.collection.objects.link(smooth_glass);smooth_glass.name='Glass_v5'
        for polygon in smooth_glass.data.polygons:polygon.use_smooth=True
        if smooth_glass.data.has_custom_normals:
            smooth_glass.data.normals_split_custom_set([(0,0,0)]*len(smooth_glass.data.loops))
        assert world_geometry(smooth_glass)==world_geometry(original['Glass'])
        assert [tuple(x.uv) for x in smooth_glass.data.uv_layers.active.data]==[tuple(x.uv) for x in original['Glass'].data.uv_layers.active.data]
        replacements['Glass']=smooth_glass
        for prefix in ['Console_1','Console_2']:
            pieces={key:[] for key in ['Backing','Glass','HUD','Frame']}
            for face in original[prefix+'_Backing'].data.polygons:
                needs_left_rim=(model['id']=='D' and prefix=='Console_2')
                grid,cover,info=fitted_console(original[prefix+'_Backing'],face,tree,inset_left=.06 if needs_left_rim else .04)
                aspect=(grid.sample(0,1)[0]-grid.sample(0,0)[0]).length/(grid.sample(1,0)[0]-grid.sample(0,0)[0]).length
                pieces['Backing'].append(backing_with_fitted_rim(grid,cover,mats['backing'],tree if needs_left_rim else None))
                for suffix,offset,mat in [('Glass',.008,mats['lens'])]:
                    ps,fs,uv=grid.geometry(offset);pieces[suffix].append(mesh('Part'+suffix,ps,fs,uv,mat))
                pieces['HUD'].append(design('console',aspect).mapped('PartHUD',grid.sample,.003,mats['glyph']))
                pieces['Frame'].append(perimeter_frame(grid,mats['frame'],'PartFrame'))
                details.append({'name':prefix,'face':face.index,'content_mm':3,'lens_mm':8,**info})
            for suffix,mat in [('Backing',mats['backing']),('Glass',mats['lens']),('HUD',mats['glyph']),('Frame',mats['frame'])]:
                replacements[prefix+'_'+suffix]=combine(prefix+'_'+suffix+'_v5',pieces[suffix],mat)
        status=original['Status'];q=canonical_quad(status,status.data.polygons[0])
        status_fraction=.78 if model['id']=='A' else 1.
        if status_fraction<1:
            oldq=list(q);q=[oldq[0],quad_point(oldq,status_fraction,0),quad_point(oldq,status_fraction,1),oldq[3]]
        frost_points,frost_faces=world_geometry(original['Frost']);frost_tree=BVHTree.FromPolygons(frost_points,frost_faces)
        status_visibility_rays=0
        for j in range(13):
            for i in range(17):
                p=quad_point(q,i/16,j/12)+Vector((0,-.008,0))
                for camera in [Vector((0,-6.5,1.6)),Vector((-4.2,-5.2,2.2))]:
                    ray=p-camera;hit,_,_,_=frost_tree.ray_cast(camera,ray.normalized(),ray.length-.0001)
                    assert hit is None,'Status display intersects chamber Frost from front/near-side view'
                    status_visibility_rays+=1
        statusgrid=Grid([quad_point(q,i/4,j/6) for j in range(7) for i in range(5)],4,6)
        aspect=(q[3]-q[0]).length/(q[1]-q[0]).length
        replacements['Status']=design('status',aspect).mapped('Status_v5',statusgrid.sample,.003,mats['glyph'])
        ps,fs,uv=statusgrid.geometry(.008);replacements['Status_Glass']=mesh('Status_Glass_v5',ps,fs,uv,mats['lens'])
        glass=GlassPatch(original['Glass']);u0,u1,v0,v1=HUD_BOUNDS
        def holosample(u,v):return glass.sample(u0+u*(u1-u0),v0+v*(v1-v0))
        aspect=(holosample(0,1)[0]-holosample(0,0)[0]).length/(holosample(1,0)[0]-holosample(0,0)[0]).length
        replacements['Holo']=glass.clipped_ui('Holo_v5',design('holo',aspect),HUD_BOUNDS,-.0025,mats['glyph'])
        panel=Canvas(aspect);panel.rect(0,0,1,1)
        replacements['Holo_Panel']=glass.clipped_ui('Holo_Panel_v5',panel,HUD_BOUNDS,-.004,mats['holo_panel'])
        unchanged=[n for n in original if n not in replacements]
        assert all(common.mesh_signature(original[n])==signatures[n] for n in unchanged)
        info={'id':model['id'],'unchanged_geometry':{n:signatures[n] for n in unchanged},'consoles':details,
            'holo_front_glass_uv_bounds':list(HUD_BOUNDS),'holo_glyph_offset_mm':-2.5,'holo_panel_offset_mm':-4.0,
            'status_content_mm':3,'status_lens_mm':8,'new_components':21,'mesh_ui_uses_raster_images':False,
            'status_supported_width_fraction':status_fraction,'status_frost_clear_visibility_rays':status_visibility_rays,
            'glyph_outline_offset_font_units':.008,'minimum_vector_rule_width_fraction':.0075,
            'glass_change':'Smooth shading normals only; exact prior positions, topology, UVs, C tail bulge and enclosure fit preserved',
            'holo_offset_basis':'Shared interpolated source vertex normals; clipped source triangles, continuous boundary positions'}
        receipt['models'].append(info)
        print('DISPLAY_V5_READY',model['id'],json.dumps(details),flush=True)
        if not apply:continue
        folder=Path(next(r['file'] for r in model['components'] if r['role']=='body')).parent.parent/'v5_2_vector_displays'
        folder.mkdir(exist_ok=False);(folder/'meshes').mkdir()
        rows=[];objects=[]
        for row in model['components']+[{'name':'Status_Glass','role':'display_glass'},{'name':'Holo_Panel','role':'holo_panel'}]:
            name=row['name'];row=deepcopy(row)
            if name in replacements:
                if name in original:bpy.data.objects.remove(original[name],do_unlink=True)
                ob=replacements[name];ob.name=name
                file=folder/'meshes'/('SM_'+model['label'].replace(' ','_')+'_'+name+'_v5_2.obj')
                row.update(file=str(file),triangles=common.export_obj(bpy,ob,file))
                row['source_sha256']=common.sha(file);row['display_revision']='v5_vector_geometry'
            else:ob=original[name]
            objects.append(ob);rows.append(row)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects:ob.select_set(True)
        bpy.context.view_layer.objects.active=original['Body']
        stem=model['label'].replace(' ','_')+'_VectorDisplays_v5_2'
        glb=folder/(stem+'.glb');blend=folder/(stem+'_Editable.blend')
        bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_keep_originals=False,export_image_format='AUTO')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),copy=True)
        raw=glb.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length])
        assert len(doc['meshes'])==21
        assert all('bufferView' in image for image in doc.get('images',[]))
        assert all(common.mesh_signature(original[n])==signatures[n] for n in unchanged)
        model.update(components=rows,editable_blend=str(blend),finished_glb=str(glb),display_v5=info)
        info.update(blend_sha256=common.sha(blend),glb_sha256=common.sha(glb),triangles=sum(r['triangles'] for r in rows))
    assert all(common.sha(p)==h for p,h in protect.items()),'Protected source changed'
    receipt.update(protected_file_count=len(protect),protected_hashes=protect,protected_inputs_unchanged=True)
    if apply:
        assert not only,'Partial authoring cannot become canonical manifest'
        result.update(version='v5_2_vector_mesh_displays',source_manifest=str(SOURCE),source_manifest_sha256=common.sha(SOURCE),
            same_finish='Fitted v4_4 enclosures and accepted freeze preserved. Shared crisp mesh typography/vector UI, compact curved inset, screen content behind glass lenses; native Unreal supplies animated scan/glow.')
        DEST.write_text(json.dumps(result,indent=2)+'\n')
        receipt.update(status='VECTOR_DISPLAY_GEOMETRY_AUTHORED_NATIVE_VISUAL_REVIEW_PENDING',manifest=str(DEST),manifest_sha256=common.sha(DEST))
        (OUT/'display-v5_2-geometry.json').write_text(json.dumps(receipt,indent=2)+'\n')
    else:(WORK/'cryo-display-v5-plan.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('DISPLAY_V5_COMPLETE',receipt['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');parser.add_argument('--only',choices=list('ABCD'))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.apply,args.only)
