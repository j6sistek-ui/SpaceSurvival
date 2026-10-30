import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Verify native PNG inputs and make a labelled, unchanged-pixel filmstrip."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,struct,re,urllib.parse
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'NativeSupportedRelease'
bad=[];chunks=[]
for p in O.glob('*/*.png'):
 try:
  with Image.open(p) as im:im.verify()
  data=p.read_bytes();offset=8
  while offset+12<=len(data):
   length=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8].decode('ascii',errors='replace')
   if offset+length+12>len(data):chunks.append({'file':str(p),'offset':offset,'chunk':kind,'declared_bytes':length,'remaining_bytes':len(data)-offset});break
   offset+=length+12
   if kind=='IEND':break
 except Exception as e:bad.append({'file':str(p),'error':str(e)})
for view in ['front','back']:
 frames=[0,40,80,120,160,200,240,280,300,320,360,440]
 sheet=Image.new('RGB',(1280,1040),(18,25,33));draw=ImageDraw.Draw(sheet)
 for i,frame in enumerate(frames):
  im=Image.open(O/view/f'{frame:04d}.png').convert('RGB');im.thumbnail((320,320))
  x=(i%4)*320;y=(i//4)*346;sheet.paste(im,(x,y));draw.text((x+10,y+322),f'{view} | {frame/24:.2f}s | frame {frame}',fill=(230,240,250))
 sheet.save(O/f'{view}_filmstrip.jpg',quality=90)
result={'png_count':len(list(O.glob('*/*.png'))),'decode_failures':bad,'chunk_failures':chunks}
(O/'MediaInputs.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
