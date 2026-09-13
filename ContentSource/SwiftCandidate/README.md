# Swift replacement candidate

This is a separate replacement candidate for the existing unlockable Swift. It has passed source checks, a separate Unreal import, fresh saved-mesh validation and three native studio views. It is **not selected by gameplay, packaged or owner-approved**. Phase 1 remains PARTIAL, and the owner's rejection of the earlier graphics remains open.

The Swift uses a new narrow pressure hull, long tapered nose, cranked swept wings, compact longer twin drives, recessed radiator details and small cyan navigation apertures. It shares the starter ship's existing ceramic, graphite, titanium and champagne material family. Its 61 new body parts change the silhouette rather than merely recoloring the Acorn hull. No ship statistic, weapon, utility, mount, collision or progression policy changes.

The complete 24-part authored cockpit is reused from AcornShipCandidate.blend. Fresh Blender validation loaded both original and candidate and compared evaluated positions, transforms, triangles, corner normals and material identities for each retained part. Seat, footwell, consoles, grips, instrument panels, coaming and windscreen match exactly. The origin remains (0, 0, 0), and the existing pilot remains at (-15, 0, 72) cm, Unreal yaw -90 degrees, uniform scale 1.5. The later unadopted grip and hand-pose candidates are not included; a separately reviewed cockpit update can propagate later.

| Property | Result |
|---|---|
| Authored parts | 85: 24 retained cockpit + 61 new body |
| Export triangles / source vertices | 46,456 / 23,578 |
| Materials | Seven existing AC01 groups |
| Bounds, cm | (-243.500, -128.174, -56.931) to (239.000, 128.174, 97.800) |
| Coordinate convention | OBJ cm, +X forward, +Z up; GLB metres with glTF axis transport |
| Collision | No collider or native policy changed |
| Export structure | One GLB mesh, seven primitives, normals and one UV channel; no skin, animation, image or texture |
| Reproduction | Fresh second build produced byte-identical OBJ, GLB and MTL; editable .blend bytes not claimed deterministic |

The complete generator is Generate.py; it reuses only the original project's Acorn authoring helpers and its saved cockpit. It writes inside this folder. SwiftCandidate.blend preserves the editable component objects and modifiers with no embedded character. SwiftCandidate.obj/.mtl and SwiftCandidate.glb are import sources. Report.json and Validation.json bind source hashes, material values, per-part topology and cockpit fingerprints. Reproduction.json proves export byte equality. SourceReceipt.json links these records to the final four rendered images and raw local logs.

Source review corrected zero-slope hull interpolation, ceramic panels intersecting the curved skin, and a clipped top frame. The final Hero.png, Chase.png and Top.png show the full candidate silhouette; Cockpit.png is deliberately a close fit detail. All four were inspected. The preserved open palm and tail surface defects remain visible. The studio uses transient TailCandidateV2 plus the unchanged Pilot animation at time zero; no character or animation file is modified or embedded in the source export. These images use Blender Cycles on eight CPU threads, 32 samples, 1440 x 1050 and AgX, not Unreal lighting. Blender's optional HIP probe warned about a missing library; rendering explicitly used CPU and completed normally.

There are 278 collapsed triangles after the retained cockpit bevel geometry is transformed and joined for export. Per-part attribution locates every one in the original three instrument panes, footwell, seat back or seat cushion. Those authored components were preserved exactly. No new Swift body part has a degenerate triangle. Both OBJ and GLB have finite positions, unit normals and valid UVs/references. Unreal imported 46,120 triangles and 41,450 render vertices, removing 336 source triangles (0.723%). The exact mapping of all removed faces is unproven; do not claim this is a zero-degeneracy mesh.

Remaining checks include LOD and draw cost, actual gameplay lighting/readability, full pilot/disembark clearance, hull and wing collision perception, and owner visual approval. The source stays inside the old Swift envelope, but that alone does not prove collision feel. The existing cockpit's hand-contact and animated release limitations are preserved, not fixed by this asset.

The subsequent native checkpoint is recorded in NativeReceipt.json; the earlier SourceReceipt.json remains the immutable source-only checkpoint, including its historical README hash. AuthorSwiftCandidate.py creates only /Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1 and reuses all seven existing Acorn material packages. It preserves the original Swift assets, all existing Source/Config/Content files, the unchanged pilot mount and native collision policy. ValidateSwiftCandidate.py reloads that saved mesh in a fresh Unreal process and checks section identities, one LOD, bounds, finite unit normals, finite UVs, import transforms and disabled collision. Both scripts write routine output to Saved/Validation/SwiftCandidate.

NativeReview contains deliberately retained, byte-identical copies of the first three routine JSON reports and Hero/Chase/Cockpit PNGs. The native views use D3D12/SM6, 1600 x 1200, an unsaved studio, ordinary casting shadows, fixed TailV2/Pilot at time zero and the unchanged pilot mount. Each view waits at least ten seconds and records the same fully resident 2048 x 2048 character texture (2,752 KB, PF_DXT1, 12 mips); no streaming flag is saved. This is a constant-pose geometry/material comparison, not animation-switch, gameplay, physical input, audio or performance validation.

The import emitted missing-smoothing-group, near-zero-tangent and near-zero-binormal warnings. Built normal and UV checks passed; the warning sources and exact removed-face mapping are unresolved. All three native images were inspected. The narrow silhouette and reused cockpit render, while dark metal readability, white-panel faceting/speckled highlights, open palms and existing tail fragments remain visible. The cockpit closeup intentionally crops the surrounding ship and tail. These are candidates for further integration review, not accepted final art.

From the repository root, using installed Blender:

~~~powershell
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --threads 8 --python ContentSource/SwiftCandidate/Generate.py
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --threads 4 --python ContentSource/SwiftCandidate/Validate.py
& 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe' --background --factory-startup --threads 8 --python ContentSource/SwiftCandidate/Generate.py -- --render
~~~

Coordinate render/Unreal windows with the lead. Check fresh success markers and JSON receipts; Blender may exit zero after a Python exception. Original Swift meshes, Acorn source, supplied character and animation sources are protected by hash. Gameplay adoption requires lead review.
