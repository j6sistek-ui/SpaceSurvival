import json,zipfile,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
rows=json.loads((OUT/'tail_preview_frames.json').read_text())
for name,kinds in [('Idle',['Idle']),('Walk',['Walk']),('Run',['Run']),('Jump',['JumpStart','JumpAir','JumpLand'])]:
    images=[];times=[]
    for row in rows:
        if row['clip'] not in kinds:continue
        im=Image.open(row['file']).convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,440,480,480),fill=(14,20,29));d.text((12,450),'TAIL '+row['clip'].upper()+'  |  body held still for inspection',fill='white');images.append(im);times.append(row['duration_ms'])
    images[0].save(OUT/('Preview_'+name+'.gif'),save_all=True,append_images=images[1:],duration=times,loop=0)
(OUT/'README.txt').write_text((Path(__file__).resolve().parent/'HANDOFF.txt').read_text(), encoding='utf-8')
files=['SquirrelHero_Rigged.blend','SquirrelHero_Rigged.fbx','SquirrelHero_Rigged.glb','README.txt','sci-fi_squirrel_3d_model_basecolor.tga','sci-fi_squirrel_3d_model_normal.tga','validation.json','roundtrip.json','tail_clips.json']
files+=['Tail_'+x+'.fbx' for x in ['Idle','Walk','Run','JumpStart','JumpAir','JumpLand']]
files+=['Preview_'+x+'.gif' for x in ['Idle','Walk','Run','Jump']]
with zipfile.ZipFile(OUT/'SquirrelHero_Rig_Package.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in files:z.write(OUT/name,name)
manifest={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in files}
(OUT/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
print('PACKAGE_OK',len(files))
