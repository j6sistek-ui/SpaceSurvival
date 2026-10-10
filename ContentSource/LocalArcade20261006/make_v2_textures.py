"""Local authored V2 surface maps and static service displays; no AI/cloud calls."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.agent/local/ArcadeGeneration/final/textures_v2'
OUT.mkdir(parents=True,exist_ok=True)


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',size)


def label(d,xy,text,size=30,fill=(195,212,221)):
    d.text(xy,text,font=font(size),fill=fill)


def save(im,name):
    im.save(OUT/(name+'.png'))


def surface(name,color,roughness,brushed=False):
    rng=np.random.default_rng(20261006+len(name))
    noise=rng.normal(0,1.4,(1024,1024,1))
    streak=rng.normal(0,1.1,(1024,1,1)) if brushed else rng.normal(0,.4,(1,1024,1))
    base=np.clip(np.array(color)[None,None,:]+noise+streak,0,255).astype('uint8')
    save(Image.fromarray(base),name)
    rough=np.clip(roughness*255+noise[:,:,0]*1.5+streak[:,:,0]*2,0,255).astype('uint8')
    save(Image.fromarray(rough),name+'_Roughness')


def main():
    if (ROOT/'.agent/local/ArcadeGeneration/FROZEN_V2_MANIFEST.json').exists():
        raise RuntimeError('V2 textures are frozen; author another version rather than overwrite them')
    surface('V2_Graphite',(51,64,74),.29)
    surface('V2_Titanium',(157,170,178),.23,True)
    surface('V2_Bronze',(134,101,64),.27,True)
    surface('V2_Ceramic',(23,29,36),.39)
    im=Image.new('RGB',(1536,864),(6,14,21)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,1535,109),fill=(15,34,45))
    label(d,(58,25),'WAYFARER  /  STATION SERVICES',40)
    d.ellipse((1400,41,1421,62),fill=(90,218,178))
    label(d,(1140,31),'TERMINAL  07',28,(100,173,188))
    label(d,(58,160),'Credit exchange',92,(216,235,238))
    label(d,(63,277),'ACCOUNT ACCESS',29,(82,177,198))
    d.line((62,330,1475,330),fill=(44,76,88),width=2)
    for y,n,title,sub in [(391,'01','Identify your account','Use the scanner below'),(581,'02','Review station services','Exchange information and support')]:
        d.rounded_rectangle((63,y,174,y+108),radius=6,fill=(20,53,66),outline=(56,138,159),width=2)
        label(d,(81,y+20),n,58,(119,204,219))
        label(d,(215,y+7),title,46)
        label(d,(218,y+68),sub,28,(112,147,158))
    # An abstract station/account mark, not a fictional balance or score.
    d.rounded_rectangle((1133,401,1440,694),radius=16,outline=(57,110,125),width=3)
    d.ellipse((1235,445,1335,545),outline=(127,192,203),width=6)
    d.arc((1185,514,1388,675),180,360,fill=(127,192,203),width=6)
    d.rectangle((0,773,1535,863),fill=(13,29,38))
    label(d,(62,796),'STATION LEDGER',25,(113,155,165))
    label(d,(970,796),'SERVICE DIRECTORY  /  07',24,(113,155,165))
    save(im,'CreditExchangeV2_Display')
    im=Image.new('RGB',(1536,256),(14,27,34));d=ImageDraw.Draw(im)
    label(d,(60,26),'CREDIT EXCHANGE',120,(192,222,229))
    label(d,(65,169),'W A Y F A R E R   /   A C C O U N T   S E R V I C E S',32,(94,151,166))
    save(im,'CreditExchangeV2_Title')
    im=Image.new('RGB',(512,512),(5,16,22));d=ImageDraw.Draw(im)
    for pad in (58,73): d.rounded_rectangle((pad,pad,512-pad,512-pad),radius=90,outline=(56,135,161),width=3)
    for i in range(5):
        x=180+i*31
        d.rounded_rectangle((x,175-abs(i-2)*9,x+16,286),radius=8,outline=(110,197,212),width=3)
    d.arc((170,238,342,354),0,180,fill=(110,197,212),width=5)
    label(d,(117,377),'ACCOUNT SCAN',29,(131,187,197))
    save(im,'CreditExchangeV2_Scanner')
    im=Image.new('RGB',(1024,512),(30,39,45));d=ImageDraw.Draw(im)
    label(d,(60,43),'WS  /  07',103,(134,154,164))
    label(d,(62,180),'STATION SERVICE UNIT',37,(111,133,145))
    d.line((60,257,959,257),fill=(75,95,107),width=3)
    label(d,(62,290),'AUTHORIZED MAINTENANCE',29,(112,133,143))
    for i in range(32):
        x=66+i*12
        d.rectangle((x,375,x+(3 if i%3 else 7),438),fill=(102,124,134))
    label(d,(600,378),'CE-07 / WFR',28,(115,137,148))
    save(im,'CreditExchangeV2_ServicePlate')
    im=Image.new('RGB',(2048,96),(18,26,31));d=ImageDraw.Draw(im)
    label(d,(90,20),'ACCOUNT SCAN',43,(134,189,202))
    label(d,(1480,20),'NAVIGATION',43,(134,189,202))
    save(im,'CreditExchangeV2_Controls')
    im=Image.new('RGB',(1024,512),(27,33,38));d=ImageDraw.Draw(im)
    label(d,(48,39),'RIFT  /  SALVAGE',85,(198,168,116))
    label(d,(49,160),'DEEP FIELD RECOVERY',39,(136,156,166))
    d.line((49,250,970,250),fill=(81,99,110),width=2)
    label(d,(49,291),'CONTAINMENT UNIT  07',35,(158,174,180))
    label(d,(50,376),'MINERALS   /   RELICS   /   LOST TECHNOLOGY',23,(130,151,160))
    save(im,'RiftSalvageV2_Plate')
    print(json.dumps({'output':str(OUT),'maps':len(list(OUT.glob('*.png'))),'provenance':'Locally authored procedural surface maps and static labels; no generation service'}))


if __name__=='__main__': main()
