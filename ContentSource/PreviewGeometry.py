"""Optional Pillow source-mesh contact sheet; not an Unreal render or approval."""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def normalized(v):
    length=math.sqrt(dot(v,v))
    return tuple(n/length for n in v)


def main():
    manifest=json.loads((ROOT/"Meshes"/"manifest.json").read_text())
    assets=[item for item in manifest["assets"] if item["name"]!="SM_Starfield"]
    cell_width,cell_height=360,290
    image=Image.new("RGB",(cell_width*5,80+cell_height*5),(7,12,21))
    draw=ImageDraw.Draw(image)
    font=ImageFont.load_default(size=16)
    large=ImageFont.load_default(size=22)
    draw.text((24,20),"SpaceSurvival / generated source geometry",font=large,fill=(220,232,246))
    draw.text((24,49),"Orthographic source QA only - no Unreal materials, lighting, hero, or gameplay represented",font=font,fill=(132,157,183))
    view=normalized((0.5,-0.67,0.55))
    right=normalized((0.67,0.5,0))
    up=normalized((view[1]*right[2]-view[2]*right[1],view[2]*right[0]-view[0]*right[2],view[0]*right[1]-view[1]*right[0]))
    light=normalized((0.3,-0.4,1))
    for index,item in enumerate(assets):
        ox=(index%5)*cell_width
        oy=80+(index//5)*cell_height
        draw.rounded_rectangle((ox+8,oy+8,ox+cell_width-8,oy+cell_height-8),radius=14,fill=(13,23,37),outline=(27,44,65))
        verts,faces=[],[]
        material="M_Hull"
        for line in (ROOT/"Meshes"/(item["name"]+".obj")).read_text().splitlines():
            words=line.split()
            if not words:continue
            if words[0]=="v":verts.append(tuple(map(float,words[1:])))
            elif words[0]=="usemtl":material=words[1]
            elif words[0]=="f":faces.append(([int(word.split("/")[0])-1 for word in words[1:]],material))
        projected=[(dot(v,right),-dot(v,up)) for v in verts]
        minx,maxx=min(p[0] for p in projected),max(p[0] for p in projected)
        miny,maxy=min(p[1] for p in projected),max(p[1] for p in projected)
        scale=min(285/(maxx-minx),195/(maxy-miny))
        center=((minx+maxx)/2,(miny+maxy)/2)
        faces.sort(key=lambda f:sum(dot(verts[i],view) for i in f[0]))
        for indices,mat in faces:
            a,b,c=[verts[i] for i in indices]
            e=tuple(b[i]-a[i] for i in range(3)); f=tuple(c[i]-a[i] for i in range(3))
            normal=normalized((e[1]*f[2]-e[2]*f[1],e[2]*f[0]-e[0]*f[2],e[0]*f[1]-e[1]*f[0]))
            if dot(normal,view)<0:continue
            rgb,_,_,emission=manifest["palette"][mat]
            brightness=0.32+0.68*max(0,dot(normal,light))
            brightness=max(brightness,min(1,emission))
            color=tuple(min(255,round(255*(value*brightness)**(1/2.2))) for value in rgb)
            points=[(ox+180+(projected[i][0]-center[0])*scale,oy+127+(projected[i][1]-center[1])*scale) for i in indices]
            draw.polygon(points,fill=color)
        draw.text((ox+20,oy+238),item["name"],font=font,fill=(214,228,242))
        draw.text((ox+20,oy+259),f"{item['triangles']:,} triangles / provisional",font=font,fill=(132,157,183))
    output=ROOT/"GeometryPreview.png"
    image.save(output)
    print(output)


if __name__=="__main__":
    main()
