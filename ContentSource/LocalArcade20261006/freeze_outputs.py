"""Pin reviewed local-only arcade exports and retain actual Comfy execution histories."""
import hashlib
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/".agent/local/ArcadeGeneration"
NAMES=("AcornautNormal","AcornautDebrisField","AcornautArcade","AcornautHyperRun","GalaxyPinball","CreditExchange","RiftSalvage")
JOBS={"AsteroidArena_cutout":"278c8cf9-c4d8-4ec0-8968-7ae6cab39079","GalaxyPinball_cutout":"3c58d64e-91b2-42dc-ad62-0b7f2d17f4d8","TokensKiosk_cutout":"f6ac254b-bbbd-4c22-82f2-0775ee583c1b","AsteroidArena_geometry":"0a3f1242-8b50-4417-b36c-7fc3ae240f17","GalaxyPinball_geometry":"d2d3fa6d-8370-4aaf-a161-a999e5239b2f","TokensKiosk_geometry":"928146dc-a8c1-48fd-9d34-4f67c1c9e102"}


def sha(path):
    return hashlib.file_digest(Path(path).open("rb"),"sha256").hexdigest()


def main():
    if (WORK / "FROZEN_MANIFEST.json").exists():
        raise RuntimeError("Frozen1 is preserved; author a new version instead")
    for name,prompt in JOBS.items():
        path=WORK/"receipts"/(name+"_history.json")
        if not path.exists():
            data=json.load(urllib.request.urlopen("http://127.0.0.1:8188/history/"+prompt,timeout=10))
            assert data[prompt]["status"]["completed"]
            assert data[prompt]["status"]["status_str"]=="success"
            path.write_text(json.dumps(data,indent=2))
    manifest={"created_utc":datetime.now(timezone.utc).isoformat(),"local_only":True,"generation_endpoint":"http://127.0.0.1:8188","station_imports":[],"retained_drafts":["AsteroidArena","TokensKiosk"],"status":"exports frozen for native import; no station placement or gameplay acceptance"}
    for name in NAMES:
        path=WORK/"final"/name/"asset.json"
        data=json.loads(path.read_text())
        files={str(p.resolve()) for p in path.parent.glob("*.fbx")}
        files.update(str(p.resolve()) for p in path.parent.glob("*.glb"))
        files.update(str(p.resolve()) for p in path.parent.glob("*.blend"))
        files.update(m["base_color_texture"] for m in data["materials"] if m.get("base_color_texture"))
        data["source_sha256"]={p:sha(p) for p in sorted(files)}
        data["frozen"]=True
        data["frozen_utc"]=manifest["created_utc"]
        data["status"]="frozen static decorative export; native import/room placement not yet verified"
        if name=="RiftSalvage":
            for part in data["fbx_parts"]: part["collision"]="none" if part["name"]=="Glass" else "box"
            for mat in data["materials"]:
                if mat["slot"]=="Rift_Glass":
                    mat["alpha"]=.035
                    mat["transmission"]=0
        path.write_text(json.dumps(data,indent=2))
        manifest["station_imports"].append({"name":name,"manifest_path":str(path.resolve()),"manifest_sha256":sha(path),"dimensions_m":data["dimensions_m"],"triangles":data.get("final_triangles",data.get("triangles"))})
    model_paths=(Path("M:/Local AI/checkpoints/hunyuan3d-dit-v2_fp16.safetensors"),Path("M:/Local AI/background_removal/birefnet.safetensors"))
    manifest["local_models_sha256"]={str(p):sha(p) for p in model_paths}
    (WORK/"FROZEN_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))


if __name__=="__main__": main()
