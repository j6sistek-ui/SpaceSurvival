# Tentacle rig (Kraken, Abyss)

Run on the normalised .blend from `../normalize_skeleton.py`, headless, CPU only:

1. `rig_tentacles.py` - traces every tentacle (Reeb graph of geodesic bands; arm tentacles by tip descent) and
   adds an 8-bone chain down each: 14 lower, 2 per arm.
2. `weight_tentacles.py` - weights each vertex to its own chain by distance ALONG ITS OWN SKIN from the root
   (projection onto the chain tears where a tentacle curls back near its own centreline), fades roots in from
   the hip, deletes skin Tripo fused between different tentacles.
3. `animate_tentacles.py` - TentCrawl / TentIdle / TentTurnL / TentTurnR: smooth rolling ripple phased by each
   tentacle's direction round the body, independent arm tentacles, skin-sampled floor contact.
4. `check_stretch.py <clip> <frame>` and `check_floor.py <clip>` - the acceptance numbers. Shipped state:
   0-1 edges over 3x stretch, floor dip <= 1.5 cm. `check_floor.py` judges every frame of the action.
5. `export_for_unreal.py <outdir> <Name>` writes `<Name>.fbx` (rest-pose mesh, no clips) plus one FBX per clip,
   `<Name>_Crawl.fbx`, `_Idle`, `_TurnL`, `_TurnR` - the files `Scripts/ImportTripoCrew.py` reads with
   `SS_TRIPOCREW_FBX=<outdir>` and `SS_TRIPOCREW_ONLY=Kraken,Abyss`. It also scales the Pelvis bob keys x100 to
   match the centimetre export; the clips imported on 2026-10-08 predate that fix and carry no visible bob
   (re-export and re-import restores it).
