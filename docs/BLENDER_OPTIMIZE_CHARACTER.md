# Lighter characters: fewer triangles, a baked texture (Blender 5.2)

Owner's ask, 2026-10-12: a step-by-step guide for reducing a character's triangles and baking a new texture,
to use alone or as the script we walk through together. The script that does all of it is
`Scripts/TripoCrewBlender/optimize_character.py`; the steps below are the same thing by hand, so either can be
checked against the other.

Measured on the Cyborg (`M:\Local AI\Projects\Cyborg_Claude\rig\Cyborg_new.blend`): 124,056 triangles, one
material in the glTF style Tripo exports (Base Color image, a packed metallic/roughness image, a normal map, an
emissive image), 1.78 m tall in metres. The numbers in this guide assume that kind of model.

## Why the earlier bake came out in patches

Four things each produce exactly that, and any one of them is enough:

1. **The bake image was only "active" in one material slot.** Blender bakes every face into the image node that
   is *selected/active in that face's material*. A Tripo body with head/body/arm materials needs the same image
   node added to and made active in **every** slot, or those faces stay black.
2. **Cage Extrusion / Max Ray Distance did not fit the model.** The online numbers (0.01, 0.1) are for a model a
   couple of units big. Use about **1% of the model's height** for extrusion and **5%** for max ray distance
   (1.8 m tall → 0.018 and 0.09). Too small: rays miss and leave holes; zero ray distance works but is slow.
3. **UV islands overlapped or touched.** Smart UV Project with Island Margin 0 lets islands bleed into each other.
   Use 0.02.
4. **The original was hidden from renders.** The camera icon (Disable in Renders) on the high-poly must be on;
   the eye icon alone is not enough. The high-poly must also be *selected* while the low-poly is *active*.

## The cheap way first: decimate only, keep the textures

Decimation keeps the UVs, so the original textures still fit. For a background NPC this is often all you need.

1. Click the character's **mesh** (not the armature). Shift+D, Enter: a copy. Rename it `<Name>_Low`.
2. Modifier Properties (wrench) → Add Modifier → Generate → **Decimate**.
   - Collapse. **Ratio** = target ÷ current (124k → 30k is 0.24). Tick **Triangulate**.
   - Under Delimit tick **UV**, so the collapse never crosses a texture seam.
   - Symmetry only if the character really is mirrored; otherwise leave it off.
3. Drag the Decimate modifier **above the Armature modifier** (it must work on the rest pose).
4. Modifier dropdown (v) → **Apply**. The copy keeps its vertex groups, so the skin weights survive.
5. Hide the original (eye and camera icons). Export the copy the usual way (`export_for_unreal.py`).

Look at it in Unreal. If seams smear or the texture looks stretched, do the bake below.

## The full way: a bake from the original

Steps 1-4 as above, keeping the UV delimit. **Keep the copy's UVs**: decimation preserves them, Tripo laid them
out properly (every triangle has its own space, no overlaps), and a bake into that layout re-projects the original
textures onto the lighter mesh, which is exactly what fixes smeared seams. Measured 2026-10-12 on the Cyborg: the
bake into the original layout filled the whole texture with no holes; a Smart UV Project re-unwrap of the same
mesh made hundreds of slivers packed into one corner with most of the texture empty. Only re-unwrap (step 6) if
the original UVs overlap (mirrored halves sharing texture space) - check with UV → Select Overlap in the UV editor.

### Unwrap the copy (only if the original UVs overlap)

6. With the copy selected: Tab (Edit Mode), A (select all), UV → **Seams from Islands** (keeps the original island
   shapes), then U → **Unwrap**, Angle Based, Margin 0.005. Tab back to Object Mode.
   (The script's `--reunwrap` does this into a new UV layer called `Baked` and removes the old one afterwards.)

### One material, one image, on the copy

7. Material Properties: remove every slot on the copy (the `-` button) and add a **new** material, `<Name>_Baked`.
8. Shading workspace. In the copy's new material: Shift+A → Texture → **Image Texture**, click **New**:
   name `<Name>_BaseColor`, 2048 × 2048, untick Alpha, OK. Leave it **unconnected** for now, but **click it** so it
   is the active node (white outline). This is the one place the patches come from, see above.

### Bake settings

9. Render Properties: Render Engine **Cycles**, Device **CPU** (keep the graphics card for the game; a 2048 bake of
   these passes is a minute or two on the processor). Samples: 4 is plenty for colour/normal/roughness.
10. Bake panel:
    - **Selected to Active**: on. Cage Extrusion **0.018**, Max Ray Distance **0.09** (1% and 5% of 1.8 m).
    - Margin 16 px. Clear Image: on.
11. Selection: click the **original** first, then Shift+click the **copy** (copy = active, lighter outline).
    Make sure the original's camera icon (render visibility) is on.

### The passes

12. **Base Color**: not with Bake Type Diffuse - a Diffuse bake gives metal no colour at all, so the Cyborg's chrome
    legs came out black (measured 2026-10-12). Instead, on the *original's* material, temporarily wire what feeds
    **Base Color** on the Principled node into an **Emission** shader connected to the Material Output; on the copy
    make `<Name>_BaseColor` active; Bake Type **Emit**; Bake; Image → Save As → `<Name>_BaseColor.png`; then put
    the original's output link back. (Diffuse + Color only is fine for a character with no metal.)
13. **Normal**: make a second image `<Name>_Normal` (Non-Color in the image node's colour space), click it so it is
    active, Bake Type Normal (Tangent space). Bake. Save.
14. **Roughness**: a third image `<Name>_Roughness` (Non-Color), active, Bake Type Roughness. Bake. Save.
15. **Metallic** (Blender has no metallic pass): on the *original's* material, temporarily wire what feeds
    **Metallic** on the Principled node into an **Emission** shader connected to the Material Output; on the copy
    make `<Name>_Metallic` (Non-Color) active; Bake Type Emit; Bake; Save; then put the original's output link
    back. Skip this if Metallic is a plain number: type that number into the copy's material instead.
16. **Emissive**, if the original has an emission image: `<Name>_Emissive` (sRGB), Bake Type Emit, Bake, Save.

### Wire the copy

17. In the copy's material connect: BaseColor → Base Color; Roughness → Roughness; Metallic → Metallic;
    Normal → a **Normal Map** node → Normal; Emissive → Emission Color with Strength 1.
18. UV Maps (Object Data Properties): delete the old layer so only the new one is left, and name it `UVMap`.
19. Hide the original, export the copy with `export_for_unreal.py`, reimport over the existing skeleton with
    `Scripts/ReimportCrewSkin.py`. Then look at it **in the game, lit, moving** - the only proof that counts.

## The script does exactly this

`Scripts/TripoCrewBlender/optimize_character.py`: click the mesh, Scripting workspace, open the file, change the
numbers at the top if you like (target triangles, texture size, output folder, `no_bake`), Run Script. Headless:

```
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "M:/Local AI/Projects/Cyborg_Claude/rig/Cyborg_new.blend" --python Scripts/TripoCrewBlender/optimize_character.py -- --object Cyborg --tris 30000 --size 2048 --out "M:/Local AI/Projects/Cyborg_Claude/optimized" --save-as "M:/Local AI/Projects/Cyborg_Claude/Cyborg_optimized.blend"
```

It bakes on the processor (`--threads 4` keeps it polite while a game runs), scales the cage to the model, handles
any number of material slots, and prints what it did. `--no-bake` is the cheap way above; `--reunwrap` is step 6.
Measured on the Cyborg (124,056 → 30,000 triangles): decimate only 3 s; the full bake at 256 px 7 s, at 2048 px
see the renders in the owner's review. The first run on a character you care about is one we do together.
