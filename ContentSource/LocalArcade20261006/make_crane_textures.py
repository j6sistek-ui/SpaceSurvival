"""Author local static crane labels; no minigame or reward behavior implied."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / ".agent/local/ArcadeGeneration/final/textures"


def label(name, lines, size, color):
    if (OUT.parents[1] / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    image=Image.new("RGB",size,(12,16,19))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((8,8,size[0]-9,size[1]-9),radius=18,outline=(83,75,63),width=4)
    for i,text in enumerate(lines):
        fontsize=int(size[1]/len(lines)*.68)
        font=ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf",fontsize)
        while draw.textbbox((0,0),text,font=font)[2] > size[0]*.91:
            fontsize-=1
            font=ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf",fontsize)
        box=draw.textbbox((0,0),text,font=font)
        draw.text(((size[0]-box[2])/2,(i+.5)*size[1]/len(lines)-(box[3]+box[1])/2),text,font=font,fill=color)
    image.save(OUT/(name+".png"))


if __name__=="__main__":
    label("RiftSalvage_Title",["RIFT SALVAGE","RECOVER THE UNKNOWN"],(1024,256),(208,160,232))
    label("RiftSalvage_Status",["TRACTOR LOCK", "READY  /  03"],(512,256),(142,232,171))
    label("RiftSalvage_Controls",["POSITION    /    RECOVER"],(1024,128),(208,185,141))
    label("RiftSalvage_Hatch",["RELIC RETURN", "STAND CLEAR"],(512,256),(188,159,98))
    label("RiftSalvage_Side",["RIFT", "SALVAGE", "OUTER RIM", "RECOVERY UNIT 07"],(512,1024),(156,124,184))
