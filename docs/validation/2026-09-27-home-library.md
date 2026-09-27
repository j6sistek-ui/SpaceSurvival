# September27 Cyberpunk library and connected home annex

Scope: owner-requested new ZIP imports, ULAT organization and the **full furnished apartment** connected to the isolated editable outpost. Branch `codex/asteroid-outpost-sandbox`, existing draft PR64. Current gameplay, normal startup, runtime C++, compiled DLL, packaged/itch build and Blender portable export were not changed.

## Imported library

| Archive | Native root | Packages |
| --- | --- | ---: |
| CyberpunkBar.zip | CyberPunkBarAssetSet01 | 196 |
| CyberpunkMegapack.zip | CyberPunkMegapack | 2,163 |
| CyberpunkScfi.zip | CyberPunkAssets | 544 |
| CyberpunkApartment.zip | Cyberpunk_Room | 487 |
| CyberpunkHolograms.zip | CyberpunkHolograms | 101 |

These new ZIPs were in the parent Downloads folder; the previously processed `Downloads/down` batch was unchanged. Existing `StageBuildingDownloads.py` completed dry-run/preflight and an applied SHA256-verified copy: **3,491 packages / 12,615,404,513 bytes**. Distinct absent Content roots avoided overwrites. Config/Saved files and six non-native SciFi source files remain in their ZIPs. Archives were retained. The source manifests and staging receipts are private under `Artifacts/ApartmentHome` and `Artifacts/BuildingLibrary`.

`ConfigureCyberpunkLibrary.py` registered **1,049 new StaticMeshes**, added **1,006 ULAT rows** and retained the previous 1,150: **2,156 total**. Forty-three short-name collisions were skipped because ULAT uses mesh short names for placement, not unique row keys. The five CP groups and `SS_New_CP_*` collections retain access to those assets; no originals were displaced or duplicated to evade that limitation. ULAT's existing engine-global data/table were backed up by `ConfigureUlatLibrary.py`. Fresh native reload verifies the saved row count and all five collection populations. Complete Blueprints remain in Content Browser, because ULAT's palette only accepts StaticMeshes.

## Saved scene identity and placement

- Station: `/Game/OutpostSandbox/L_AsteroidOutpost`, SHA256 `aa6f7e5fa9d4ea42f3d14f818ee7ff701a7cdf64a413a3657dbac62c64f0e44a`.
- Private furnished level: `/Game/BuildingLibrary/Home/L_CrewApartment`, SHA256 `dbac3d7c9a0e73bc90bd641966e46bbb57f16aaad74b4d2de2cf6e4374f1081a`.
- Single-placement Blueprint: `/Game/BuildingLibrary/Assembled/Home/BP_CrewApartment_Complete`, making 43 assembled assets.
- Original apartment map: SHA256 `78c36bc9aeaa530e0e21a7248d71a0f624049b693f4a067c33e3bde532119e66`, unchanged.
- Original station map backup: `Artifacts/ApartmentHome/L_AsteroidOutpost-before-home-20260927T041304Z.umap`, SHA256 `a57659ae6d9d8585cc8964c0d956ff39b7c9f69d6267d356211d22caf659eff7`.

The furnished apartment has 742 actors including four new local fills. It preserves the source layout, furnishings, spline assemblies, materials, particles and local fixtures. Its showcase global atmosphere/lighting/postprocess, camera/sequence rig and opaque exterior city image were removed from the private copy. Nineteen private structural-mesh derivatives provide precise collision without overwriting vendor assets. Physical supports follow the raised entrance and lower floor. Decorative decal planes/rugs use NoCollision; the native SSOutpostDoor owns moving physical blockers and carries the original visual leaves.

The entrance is at `(6120,4100,-120)`cm. The route branches beside the Crew Lounge approach at `(4400,1975,0)`, descends six 20 cm steps, turns north through a covered glass corridor and enters the raised strip; the main furnished floor is at Z-170. Shared-pivot Genesis frame/glass pairs, physical support, guards, roof and local fixtures form a connected addition beneath/alongside the existing skyline bridge. **230 new station actors; 7,552 original actor fingerprints preserved**, including transforms, mesh/material references and collision-enabled states. This is a scoped fingerprint, not a proof of every component property. No station regeneration was performed.

## Focused evidence

- `Survey1`, `Author1`, `Integrate2`, `Repair1`, `Review2`, `Review3` finish with native process exit 0; Python markers/receipts are checked separately from the process status.
- Final `Artifacts/ApartmentHome/Review-20260927T042648Z/review.json`: **68/68 checks pass, zero script errors**. It verifies 27 floor points and 27 upper-body clearance points, a 27-waypoint CharacterMovement walk into the furnished living area and back, full automatic opening, closure after departure, saved ULAT count/five collections/complete Blueprint load, and map/save-file preservation.
- Floor clearance probes exclude the movable closed doorway, which is checked during actual PIE movement. Upper-body probes begin above the legal 45 cm step band; this avoids falsely rejecting a capsule numerically seated inside a descending riser. Floor probes and actual traversal remain separate gates.
- PIE setup teleports the character once to the connector start; subsequent movement uses `AddMovementInput`. No further script teleport is issued. This is scripted collision/door evidence, not physical-device input, every furniture aisle, broad obstacle safety or natural-play acceptance.
- Four saved-scene 1600x900 views in `Artifacts/ApartmentHome/Review-20260927T042319Z`: approach, entrance, living area and reverse desk view. No camera exposure/lighting overrides. Lead and independent agent found readable circulation/furnishings, no obvious floating major furniture or gross intersections in those views. The dark ceiling retains the source industrial character. The closed-door image alone is not collision proof.
- Author and repair source-map guards pass. Fresh validation preserves both saved maps and SaveGames. This does not prove a populated gameplay save/departure scenario; no departure was exercised.

## Retained failures and limits

1. First import preflight rejected `Tree01.st` as non-native before any writes. Filtering only native Content, then rerunning dry-run/apply, resolved it; source files remain in the archive.
2. Integrate1 refused to save because original actor fingerprints changed during asynchronous asset loading. Integrate2 waits for the native loading/compilation barrier before both comparisons; all 7,552 match. The failed receipt is retained, not reported as a save.
3. Review1 exposed a dark apartment and blocked entrance. Two nearly 10 m decorative decal planes had solid collision; their world X=6125.373 minus capsule radius 34 matches the stopped X=6091.272 within 0.101 cm. The private copy disables that decorative collision. The visual leaves also regained mesh-default BlockAll on load; explicit NoCollision profiles prevent that reset. Existing source lights were increased 8x, four soft local fills added, and only the six new corridor pools increased 450→2400 lm. Existing station/global lighting is unchanged.
4. Review2's walk into the home, return and door checks passed, but its last static sample intersected the sofa. The final waypoint moved 40 cm back into the circulation area; Review3 passes the complete revised route. No sofa or collision was removed to hide the failed sample.
5. Legacy vendor `BP_Blinds` construction warnings about optional Frame/Rope material values remain. The furnished window/blinds appearance is present in the reviewed scene; their optional interactive/material behavior is not certified. Original apartment cinematic references `SequenceMaster`, absent from the supplied pack; its sequence actors are omitted from the private home. Other pack example maps and optional Blueprint features have not all been exercised. Logs also retain pre-existing ShipCore startup, connectivity-probe and renderer console-variable warnings; this is **not a warning-free engine automation-suite claim**.
6. No performance benchmark, full game suite, C++ rebuild or package was needed for this asset/Python-only batch. Existing Editor Build5 supplies the unchanged native sandbox actors. Broader outpost visual acceptance, populated-save departure, physical controls and representative performance remain in RPT-20260924-01.

## Source checks and replay boundaries

Six changed Python scripts pass syntax compilation. `Scripts/CheckProject.py` passes 38 structural checks; `Scripts/CheckPrDocumentation.py --repo .` passes canonical counts/navigation; `git diff --check` passes. The prepared PR body also passes the documentation declaration/owner-handoff dry run before publication. The changed scripts are native authoring/verification recipes, not a replacement gameplay build. A final independent source review found that unchanged library registration omitted its verified row count; the report now always records the actual count and the reader accepts the older planned-row field. That repeat-registration repair was source-reviewed and syntax-checked after Review3; it did not change the validated maps or palette.

For a **new** private home, `AuthorHomeApartment.py` includes the final collision/lighting corrections; `AuthorOutpostHomeHub.py` uses `HomeAnnexConnector.py` and refuses to replace an existing annex. `RepairHomeAnnex.py` is the one-time hash-guarded repair of the recorded first authoring result, not a required second pass or an owner refresh command. Never rerun station generation over owner edits. `ReviewOutpostHome.py -HomeWalk -HomeLibrary` checks only the new route/library; add `-HomeCapture` for the four changed-area views.

Vendor roots, native maps/derivatives, source ZIPs, local collections, raw logs/captures and engine-plugin palette remain private/ignored. Git holds scripts, exclusions and concise documentation. Use the existing Play/Edit Outpost launchers; this is not the main game station or a refreshed portable Blender library.
