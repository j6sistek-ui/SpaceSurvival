"""Static Acornaut attract art from existing owner artwork, with HUD cropped out."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/".agent/local/ArcadeGeneration"
OUT=WORK/"final/textures"
REF=Path("C:/Users/j6sis/.codex/codex-remote-attachments/01a0c239-12ad-7c60-83ce-bd20c0072f9a/E8E9EB81-ED40-4F2E-97E5-BB76092C709A")
SITE=Path("C:/Users/j6sis/acornaut/tmp/zone-art-review/site-src/assets")
MODES=[("Normal","NORMAL",(75,134,240),REF/"1-Photo-1.jpg",(68,244,548,533),"STANDARD GATES"),
       ("DebrisField","DEBRIS FIELD",(151,92,215),REF/"2-Photo-2.jpg",(35,268,555,525),"WAVE SURVIVAL"),
       ("Arcade","ARCADE",(223,152,49),SITE/"poster-arcade.jpg",(0,87,400,861),"RETRO FLIGHT"),
       ("HyperRun","HYPER RUN",(52,195,222),SITE/"poster-race.jpg",(0,87,400,862),"THREAD THE GATES")]


def font(size,bold=True): return ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf",size)


def centered(draw,text,y,size,color,width):
    face=font(size)
    while draw.textbbox((0,0),text,font=face)[2] > width*.90:
        size-=1; face=font(size)
    bb=draw.textbbox((0,0),text,font=face)
    draw.text(((width-bb[2])/2,y),text,fill=color,font=face)


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    provenance=[]
    for key,label,color,source,crop,tag in MODES:
        name="Acornaut"+key
        art=Image.open(source).convert("RGB").crop(crop)
        title=Image.new("RGB",(1024,256),(8,12,24)); d=ImageDraw.Draw(title)
        d.rounded_rectangle((9,9,1014,246),radius=16,outline=color,width=5)
        centered(d,"A C O R N A U T",20,38,(209,222,239),1024)
        centered(d,label,82,112,color,1024)
        title.save(OUT/(name+"_Title.png"))
        screen=Image.new("RGB",(1024,768),(6,10,25)); d=ImageDraw.Draw(screen)
        d.rounded_rectangle((14,14,1009,753),radius=26,outline=color,width=3)
        centered(d,"ACORNAUT",26,46,(217,225,240),1024)
        fitted=ImageOps.contain(art,(936,544),Image.Resampling.LANCZOS)
        screen.paste(fitted,((1024-fitted.width)//2,105+(544-fitted.height)//2))
        centered(d,tag,678,40,color,1024)
        screen.save(OUT/(name+"_Screen.png"))
        badge=Image.new("RGB",(512,512),(12,16,23)); d=ImageDraw.Draw(badge)
        d.ellipse((62,62,450,450),outline=color,width=12)
        centered(d,"A",62,290,color,512)
        centered(d,label,382,42,(201,212,231),512)
        badge.save(OUT/(name+"_Badge.png"))
        side=Image.new("RGB",(512,1024),(15,20,29)); d=ImageDraw.Draw(side)
        d.rounded_rectangle((10,10,501,1013),radius=25,outline=color,width=7)
        centered(d,"ACORNAUT",80,60,(205,216,232),512)
        art2=ImageOps.contain(art,(444,610),Image.Resampling.LANCZOS)
        side.paste(art2,((512-art2.width)//2,220+(610-art2.height)//2))
        centered(d,label,870,65,color,512)
        side.save(OUT/(name+"_Side.png"))
        base=np.asarray(Image.open(OUT/"GreenMetal.png").convert("RGB"),dtype=float)
        grain=base.mean(axis=2,keepdims=True)-base.mean()
        paint=np.clip(np.array(color)[None,None,:]*.38+grain,0,255).astype("uint8")
        Image.fromarray(paint).save(OUT/(name+"_Paint.png"))
        provenance.append({"mode":label,"source":str(source),"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"crop_excludes_hud":list(crop),"kind":"existing owner art/static attract composition","repository_origin":"https://github.com/j6sistek-ui/AcornautSandbox.git" if source.parent==SITE else None,"source_checkout_head":"a0c9a0d3467160553fb726325c0689d0e7c501f0" if source.parent==SITE else None})
    (WORK/"receipts/acornaut_art_provenance.json").write_text(json.dumps(provenance,indent=2))
    print(json.dumps(provenance,indent=2))


if __name__=="__main__": main()
