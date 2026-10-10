# Joy and Cyborg apartment placement

October10,2026. The owner explicitly places Joy and the rigged purple Cyborg in the existing private apartment beneath Room R, and approves a simple polished-metal pole after relevant source checks find pole clips but no separate prop. This supersedes the earlier no-permanent-placement restriction for these two residents only.

Saved Wayfarer170 has9,058 actors, SHA `7e30f69f57b4c2ecb2600334c39ed18038fda28a90fbffee632660651a80f937`. Seven additions are Joy, Cyborg and five pole parts. Joy uses the saved light-blue Blueprint with corrected groom/binding and looping PoleIdle; Cyborg uses the canonical rigged mesh and looping Idle. The4.5cm pole has floor and ceiling mounts and reuses the installed Genesis nickel parent through one private material instance. No original character, mesh, clip, apartment furniture, LevelInstance, lighting or other NPC is edited. All9,051 existing actor fingerprints match before save;404 protected files remain unchanged, with only the explicitly authorized station map superseded.

## Verification and limits

Actual integrated Survival Play captures171 contain four ordinary1280x722 views. Both resident clips advance across240 samples; Joy's hair remains visible, and the reviewed pose/hand and floor/ceiling pole contacts align. Nine player-sized capsule points have clear space and floor support. The first two172 probe positions were inside the existing sofa; their failure is retained, and173 uses the actual surrounding aisle. This is point clearance, not a continuous or physical-input walk.

Reload175 confirms all seven saved additions, both meshes/looping clips, both Joy groom bindings,9,058 actors, RT0 and clean packages. Its strict whole-world comparison does not pass: three pre-existing hand/pelvis-attached tablet/case props evaluate slightly different world transforms after reload. Their identities, attachments and failure are retained; no broader equality claim. All original actor fingerprints matched immediately before save.

Capture finalization restores HUD, camera, viewport and quality and preserves save files/map bytes/dirty state. The offscreen editor then closes cleanly. Prior temporary motion164 finalized12 frames/644 samples, but moving existing crew obscured some front views; this is representative groom-motion evidence, not all135-clips contact acceptance.

Retained authoring failures:168 used an unavailable actor getter before any edit;169 stopped after its scalar setter reported false despite applying MinRoughness. Inspection confirmed no actors existed;170 validated all five material values through getters and completed from that exact partial state. No blind authoring replay occurred.

## Storage and remaining work

[Sanitized evidence](2026-10-10-apartment-residents-evidence.json) and `Scripts/StationRecipes/ApartmentResidents168` are tracked. Native map/material, before/after backups and full captures remain private under `.agent/local/StationRefinement/ApartmentResidents169` and the Outpost capture archive. GitHub is not a full native backup. No C++ or Blueprint structure changed; existing compiled BP and assets were reused. No cook, release or merge; Build55 and the published game are unchanged.

Separate owner Blender fitting support does not change these game assets: the neutral-pose copy retains its original action unassigned, binds the hair root to the head, and imports the owner's three clothing pieces with textures. Outfit fitting and weights remain separate from game adoption. Central fixed target-v2 and R remain unfinished; other room/cockpit/NPC work stays held. See [KNOWN_ISSUES](../KNOWN_ISSUES.md).
