"""Deterministic original mesh sources. +X forward, +Z up, centimeters.

Produces real OBJ/MTL geometry with normals/material slots and a source manifest.
The generated art is provisional until imported and judged in gameplay.
"""
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Meshes"
PALETTE = {
    "M_Hull": ((0.075, 0.115, 0.15), 0.75, 0.32, 0.0),
    "M_Gold": ((0.48, 0.255, 0.075), 0.8, 0.28, 0.0),
    "M_Rock": ((0.19, 0.16, 0.145), 0.02, 0.87, 0.0),
    "M_Cyan": ((0.025, 0.66, 0.85), 0.1, 0.25, 3.0),
    "M_Amber": ((1.0, 0.33, 0.035), 0.15, 0.3, 2.5),
    "M_Violet": ((0.5, 0.14, 0.87), 0.1, 0.3, 2.7),
    "M_Hazard": ((0.28, 0.22, 0.19), 0.15, 0.7, 0.0),
    "M_Emissive": ((1.0, 1.0, 1.0), 0.0, 0.3, 3.0),
    "M_Space": ((0.0003, 0.0005, 0.0015), 0.0, 1.0, 1.0),
    "M_Star": ((0.55, 0.73, 1.0), 0.0, 1.0, 3.0),
    "M_StarWarm": ((1.0, 0.65, 0.39), 0.0, 1.0, 2.0),
}


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    if length < 1e-8:
        raise ValueError("Degenerate mesh face")
    return tuple(x / length for x in v)


def coordinate(value):
    # Tiny floating-point differences must not alternate signed zero by runtime.
    return f"{0.0 if abs(value) < 0.0000005 else value:.6f}"


class Mesh:
    def __init__(self, name):
        self.name, self.vertices, self.faces = name, [], []

    def part(self, vertices, faces, material="M_Hull", smooth=False):
        offset = len(self.vertices)
        self.vertices.extend(vertices)
        for face in faces:
            # Fan triangulation is used only for convex authored faces.
            for index in range(1, len(face) - 1):
                self.faces.append((tuple(offset + k for k in (face[0], face[index], face[index + 1])), material, smooth))

    def box(self, center, size, material="M_Hull"):
        x, y, z = center
        a, b, c = (n / 2 for n in size)
        self.part([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                   (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],
                  [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], material)

    def prism(self, polygon, low, high, material="M_Hull"):
        # xy polygon must be counterclockwise and convex.
        n = len(polygon)
        verts = [(x,y,z) for z in (low, high) for x,y in polygon]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.part(verts, faces, material)

    def lathe(self, rings, segments=40, material="M_Hull", center=(0,0,0), zscale=1.0):
        verts = [(x+center[0],r*math.cos(j*math.tau/segments)+center[1],r*math.sin(j*math.tau/segments)*zscale+center[2])
                 for x,r in rings for j in range(segments)]
        faces = [(i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j)
                 for i in range(len(rings)-1) for j in range(segments)]
        # Explicit center fans avoid zero-radius degenerate pole rings.
        for first, reverse in ((0,True),(len(rings)-1,False)):
            middle = len(verts)
            verts.append((rings[first][0]+center[0],center[1],center[2]))
            for j in range(segments):
                face=(middle,first*segments+j,first*segments+(j+1)%segments)
                faces.append(tuple(reversed(face)) if reverse else face)
        self.part(verts, faces, material, smooth=True)

    def torus(self, center, major, minor, material="M_Gold", axis="x", segments=40, zscale=1):
        verts=[]
        tube=8
        for a in range(segments):
            u=a*math.tau/segments
            for b in range(tube):
                v=b*math.tau/tube
                p=(minor*math.sin(v),(major+minor*math.cos(v))*math.cos(u),(major+minor*math.cos(v))*math.sin(u))
                if axis=="z":
                    p=(p[1],p[2],p[0])
                p=(p[0],p[1],p[2]*zscale)
                verts.append(tuple(p[i]+center[i] for i in range(3)))
        faces=[(a*tube+b,((a+1)%segments)*tube+b,((a+1)%segments)*tube+(b+1)%tube,a*tube+(b+1)%tube)
               for a in range(segments) for b in range(tube)]
        self.part(verts, faces, material, smooth=True)

    def save(self):
        normals=[]
        averaged={}
        for indices, _, smooth in self.faces:
            a,b,c=(self.vertices[i] for i in indices)
            n=normalize(cross(sub(b,a),sub(c,a)))
            normals.append(n)
            if smooth:
                for i in indices:
                    old=averaged.get(i,(0,0,0))
                    averaged[i]=tuple(old[k]+n[k] for k in range(3))
        averaged={k:normalize(v) for k,v in averaged.items()}
        lines=["# Original SpaceSurvival generated source; centimeters; X forward; Z up", "mtllib Palette.mtl", f"o {self.name}"]
        lines += ["v " + " ".join(coordinate(v) for v in p) for p in self.vertices]
        # Per-face UVs provide valid coordinates for tangents/lightmap generation.
        lines += ["vt 0.05 0.05", "vt 0.95 0.05", "vt 0.05 0.95"]
        faces=[]
        previous=None
        normal_index=1
        for f, ((indices,material,smooth), face_normal) in enumerate(zip(self.faces,normals)):
            if previous!=material:
                faces.append(f"usemtl {material}")
                previous=material
            references=[]
            for i,index in enumerate(indices):
                n=averaged[index] if smooth else face_normal
                lines.append("vn " + " ".join(coordinate(v) for v in n))
                references.append(f"{index+1}/{i+1}/{normal_index}")
                normal_index+=1
            faces.append("f " + " ".join(references))
        filename=OUT/f"{self.name}.obj"
        filename.write_text("\n".join(lines+faces)+"\n",encoding="utf-8")
        bounds=[[round(f(v[i] for v in self.vertices),3) for i in range(3)] for f in (min,max)]
        return {"name":self.name,"vertices":len(self.vertices),"triangles":len(self.faces),"bounds_cm":bounds,
                "materials":list(dict.fromkeys(f[1] for f in self.faces)),
                "sha256":hashlib.sha256(filename.read_bytes()).hexdigest()}


def ship(agile=False):
    m=Mesh("SM_AgileShip" if agile else "SM_AcornShip")
    stretch=1.15 if agile else 1.0
    rings=[(-195,24),(-180,58),(-140,83),(-70,93),(0,85),(85,60),(155,31),(210,3)]
    m.lathe([(x*stretch,r*(0.86 if agile else 1)) for x,r in rings],48,zscale=0.68)
    m.lathe([(-188*stretch,58),(-170*stretch,76),(-130*stretch,90),(-100*stretch,94),(-90*stretch,88)],48,"M_Gold",zscale=0.69)
    for x,r in ((-170,77),(-147,87),(-121,94)):
        m.torus((x*stretch,0,0),r,2.4,"M_Gold",zscale=0.69)
    # An open cockpit keeps the supplied pilot silhouette above the ship.
    m.box((-30,0,49),(92,64,14),"M_Gold")
    m.box((-65,0,75),(12,72,50),"M_Hull")
    for sign in (-1,1):
        poly=[(-155,sign*62),(5,sign*72),(-105,sign*(185 if agile else 145)),(-205,sign*(155 if agile else 110))]
        if sign<0:
            poly.reverse()
        # Re-orient polygon from signed area because mirrored fins change winding.
        area=sum(poly[i][0]*poly[(i+1)%4][1]-poly[(i+1)%4][0]*poly[i][1] for i in range(4))
        if area<0:
            poly.reverse()
        m.prism(poly,-25,-8,"M_Gold")
        y=sign*(105 if agile else 85)
        m.lathe([(-230,14),(-220,22),(-140,25),(-100,10)],24,"M_Hull",(-15,y,-25))
        m.lathe([(-247,17),(-243,17)],24,"M_Cyan",(0,y,-25))
        m.box((45,sign*57,30),(80,5,5),"M_Cyan")
        m.box((125,sign*27,-10),(65,8,8),"M_Gold")
    return m


def asteroid(name, seed, scale=1):
    rng=random.Random(seed)
    m=Mesh(name)
    sides,levels=22,11
    verts=[(0,0,104*scale)]
    for row in range(1,levels):
        phi=math.pi*row/levels
        for column in range(sides):
            angle=math.tau*column/sides
            radius=(88+rng.uniform(-16,16))*scale
            verts.append((radius*math.sin(phi)*math.cos(angle),radius*math.sin(phi)*math.sin(angle),radius*math.cos(phi)))
    bottom=len(verts)
    verts.append((0,0,-94*scale))
    faces=[]
    for j in range(sides):
        faces.append((0,1+j,1+(j+1)%sides))
    for row in range(levels-2):
        for j in range(sides):
            a=1+row*sides+j
            b=1+row*sides+(j+1)%sides
            faces.append((a,a+sides,b+sides,b))
    for j in range(sides):
        faces.append((bottom,1+(levels-2)*sides+(j+1)%sides,1+(levels-2)*sides+j))
    m.part(verts,faces,"M_Rock",smooth=True)
    return m


def debris(name="SM_Debris"):
    m=Mesh(name)
    m.box((0,0,0),(175,22,24))
    m.box((-30,10,25),(25,135,18))
    m.prism([(-90,-50),(70,-50),(55,60),(-45,35)],5,12,"M_Gold")
    m.box((28,10,24),(46,26,16))
    m.box((26,10,33),(32,17,2),"M_Amber")
    return m


def enemy(flanker=False):
    m=Mesh("SM_Flanker" if flanker else "SM_Pursuer")
    m.lathe([(-80,15),(-45,28),(40,23),(110,2)],24,"M_Hull",zscale=0.6)
    for sign in (-1,1):
        p=[(-90,sign*14),(-35,sign*(112 if flanker else 70)),(90,sign*(82 if flanker else 28)),(30,sign*18)]
        area=sum(p[i][0]*p[(i+1)%4][1]-p[(i+1)%4][0]*p[i][1] for i in range(4))
        if area<0:p.reverse()
        m.prism(p,-8,8,"M_Hull")
        m.box((-32,sign*(75 if flanker else 35),8),(52,6,5),"M_Amber")
        m.lathe([(-100,9),(-97,9)],16,"M_Amber",(0,sign*20,0))
    return m


def pickup(kind):
    m=Mesh("SM_Pickup"+kind)
    if kind=="Credit":
        m.torus((0,0,0),25,8,"M_Gold",axis="z",segments=24)
        m.box((0,0,0),(11,30,12),"M_Amber")
    elif kind=="Repair":
        m.box((0,0,0),(50,16,15),"M_Cyan")
        m.box((0,0,0),(16,50,17),"M_Cyan")
    elif kind=="Shield":
        m.prism([(-27,-20),(17,-27),(33,0),(17,27),(-27,20)],-7,7,"M_Cyan")
        m.prism([(-15,-11),(9,-15),(19,0),(9,15),(-15,11)],7,10,"M_Hull")
    else:
        m.prism([(-25,-22),(29,-3),(29,4),(-25,-15)],-7,7,"M_Violet")
        m.prism([(-25,15),(29,-4),(29,3),(-25,22)],-7,7,"M_Violet")
    return m


def props():
    console=Mesh("SM_Console")
    console.box((0,0,10),(90,60,20))
    console.box((-12,0,50),(42,42,80))
    console.box((0,0,98),(86,62,15),"M_Gold")
    console.box((4,0,107),(67,44,3),"M_Cyan")
    crate=Mesh("SM_Crate")
    crate.box((0,0,35),(85,65,70))
    for x in (-33,33):crate.box((x,0,36),(8,69,74),"M_Gold")
    crate.box((0,-34,40),(32,3,15),"M_Amber")
    arm=Mesh("SM_ServiceArm")
    arm.box((0,0,18),(75,75,36))
    arm.box((0,0,115),(24,24,180),"M_Gold")
    arm.box((70,0,200),(160,20,22))
    arm.box((143,0,175),(20,40,45),"M_Cyan")
    ring=Mesh("SM_StationRing")
    ring.torus((0,0,0),100,6,"M_Hull",segments=48)
    ring.torus((1,0,0),91,2,"M_Cyan",segments=48)
    vector=Mesh("SM_VectorThrusters")
    for y in (-19,19):vector.lathe([(-25,8),(-15,14),(20,12),(28,5)],20,"M_Cyan",(0,y,0))
    vector.box((0,0,0),(15,35,13),"M_Gold")
    cooling=Mesh("SM_OverdriveCooling")
    cooling.box((0,0,0),(45,32,25))
    for x in range(-18,19,6):cooling.box((x,0,0),(3,42,34),"M_Violet")
    storm=Mesh("SM_StormRing")
    storm.torus((0,0,0),97,3,"M_Violet",segments=48)
    gravity=Mesh("SM_GravityRing")
    gravity.torus((0,0,0),97,3,"M_Violet",segments=48)
    gravity.torus((0,0,0),67,1.5,"M_Cyan",segments=48)
    depot=Mesh("SM_MobileDepot")
    depot.box((0,0,0),(160,85,70))
    for y in (-53,53):
        depot.box((-15,y,-5),(125,25,45),"M_Gold")
        depot.box((40,y,20),(45,6,4),"M_Cyan")
    depot.torus((40,0,50),34,4,"M_Cyan",axis="z",segments=24)
    beacon=Mesh("SM_EventBeacon")
    beacon.torus((0,0,0),34,4,"M_Cyan",axis="z",segments=24)
    beacon.box((0,0,0),(14,14,55),"M_Gold")
    projectile=Mesh("SM_Projectile")
    projectile.lathe([(-100,2),(-65,7),(65,7),(100,2)],12,"M_Emissive")
    return [console,crate,arm,ring,vector,cooling,storm,gravity,depot,beacon,projectile]


def starfield():
    # One static mesh, 1,200 tiny inward-facing triangles: bounded draw cost.
    # Radius dwarfs gameplay distances. It has no collision or gameplay role.
    m=Mesh("SM_Starfield")
    rng=random.Random(9202)
    distance=4000000
    for index in range(1200):
        z=rng.uniform(-1,1)
        angle=rng.uniform(0,math.tau)
        direction=(math.sqrt(1-z*z)*math.cos(angle),math.sqrt(1-z*z)*math.sin(angle),z)
        side=normalize(cross(direction,(0,0,1) if abs(z)<0.98 else (0,1,0)))
        up=normalize(cross(direction,side))
        center=tuple(distance*v for v in direction)
        size=distance*rng.uniform(0.00014,0.00045)
        vertices=[tuple(center[k]+size*(side[k]*x+up[k]*y) for k in range(3)) for x,y in ((0,1),(-0.866,-0.5),(0.866,-0.5))]
        # Face the center; all stars remain visible with back-face culling.
        m.part(vertices,[(0,2,1)],"M_StarWarm" if index%7==0 else "M_Star")
    return m


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mtl=[]
    for name,(color,metal,rough,emission) in PALETTE.items():
        mtl.extend([f"newmtl {name}","Kd "+" ".join(map(str,color)),"Ks 0.5 0.5 0.5",f"Ns {max(1,100*(1-rough)):.1f}","illum 2",""])
    (OUT/"Palette.mtl").write_text("\n".join(mtl),encoding="utf-8")
    meshes=[ship(),ship(True),asteroid("SM_Asteroid",19),
            asteroid("SM_AsteroidSmall",21),asteroid("SM_AsteroidMedium",23),asteroid("SM_AsteroidMassive",25),
            debris(),debris("SM_Wreckage"),enemy(),enemy(True)]
    meshes += [pickup(k) for k in ("Credit","Repair","Shield","Buff")]+props()+[starfield()]
    result={"status":"Generated provisional source meshes; Unreal aesthetic/scale/collision review pending",
            "coordinate_system":"Centimeters; +X forward; +Z up", "palette":PALETTE,
            "assets":[mesh.save() for mesh in meshes]}
    (OUT/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Generated {len(meshes)} original mesh sources in {OUT}")
    return result


if __name__=="__main__":
    main()
