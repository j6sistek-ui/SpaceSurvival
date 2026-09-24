import json,zipfile,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'README.txt').write_text((Path(__file__).parent/'HANDOFF.txt').read_text(encoding='utf-8'), encoding='utf-8')
for prefix,manifest in [('Preview_','tail_preview_frames.json'),('FurPreview_','fur_preview_frames.json')]:
 rows=json.loads((OUT/manifest).read_text())
 for name,kinds in [('Idle',['Idle']),('Walk',['Walk']),('Run',['Run']),('Jump',['JumpStart','JumpAir','JumpLand'])]:
    images=[];times=[]
    for row in rows:
        if row['clip'] not in kinds:continue
        im=Image.open(row['file']).convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,440,480,480),fill=(14,20,29));d.text((12,450),'TAIL '+row['clip'].upper()+'  |  body held still for inspection',fill='white');images.append(im);times.append(row['duration_ms'])
    images[0].save(OUT/(prefix+name+'.gif'),save_all=True,append_images=images[1:],duration=times,loop=0)
files=['SquirrelHero_Rigged.blend','SquirrelHero_Rigged.fbx','SquirrelHero_Rigged.glb','README.txt','sci-fi_squirrel_3d_model_basecolor.tga','sci-fi_squirrel_3d_model_normal.tga','validation.json','roundtrip.json','tail_clips.json']
files+=['Tail_'+x+'.fbx' for x in ['Idle','Walk','Run','JumpStart','JumpAir','JumpLand']]
files+=['Preview_'+x+'.gif' for x in ['Idle','Walk','Run','Jump']]
files+=['FurPreview_'+x+'.gif' for x in ['Idle','Walk','Run','Jump']]
files+=['SquirrelHero_SoftFur.'+ext for ext in ['blend','fbx','glb']]
files+=['Tail_FineFibers_RGBA.png','Tail_SoftCore_Color.png','fur_revision.json','fur_validation.json','tail_weight_revision.json','SoftFur_Back.png']
with zipfile.ZipFile(OUT/'SquirrelHero_Rig_Package.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in files:z.write(OUT/name,name)
manifest={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in files}
(OUT/'package_manifest.json').write_text(json.dumps(manifest,indent=2))
print('PACKAGE_OK',len(files))
