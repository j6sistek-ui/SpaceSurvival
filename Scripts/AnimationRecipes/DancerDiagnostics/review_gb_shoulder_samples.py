import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Contact sheet of original diagnostic captures; no geometry/pixel retouching."""
from PIL import Image,ImageDraw
from pathlib import Path
out=Image.new('RGB',(1600,680),'#111820');draw=ImageDraw.Draw(out)
for row,view in enumerate(('front','back')):
 for col,frame in enumerate((0,100,200,300,400)):
  source=R/'NativeGBShoulderResponse'/('g1_'+view)/f'{frame:04d}.png'
  with Image.open(source) as im:out.paste(im.convert('RGB').resize((320,320)),(col*320,row*340))
  draw.text((col*320+8,row*340+321),f'{view}: {frame/24:.3f}s',fill='white')
out.save(R/'GBShoulderResponse/NativeSamples.png')
