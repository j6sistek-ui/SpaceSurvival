# September22 approved UI integration

Scope: owner-authorized page11 HUD/settings/pause mapping and latest amendment removing the hull/shield/brake backing panel and percentage labels. Locked main unchanged; service panels reuse common frame/actions. No new control preset/remapper. Exact source/provenance: ContentSource/FigmaUIRefresh/README.md. Figma unchanged.

## Source and focused evidence

- 27 exact transparent KIT/background PNG exports imported after guarded dry-run; PNG dimensions/hashes and TTF/OFL copies validated. Private author receipt Artifacts/UIRefresh/author.json records27 runtime output hashes. Raw sources/new runtime family are tracked; existing licensed library preserved.
- Editor Build1 passed46.19s; first render47d612f737ca4b55a73b5ac7f4712be0 FAILED after six blank-text menu frames and a HUD-only bounds-index crash. Installed CanvasItem.h requires a UFont FontObject; filename-only Slate font could measure/load but could not draw. Runtime UFont provider fixes text. HUD capture no longer indexes title bounds.
- Build2 passed17.02s; rendered79ccc277a2fd4628ba74771c60051c2c PASS: General/Graphics/Audio/Controls/Pause/Wardrobe/HUD, native centers mapped, process0, source/artifact/production-save guards and no test saves. All seven raw images inspected; text visible, no vitals box or percentages. HUD is a labeled sample overlay on the unchanged station world, not an actual flight acceptance run.
- Focused automation: SpaceSurvival.Menu plus TitleMenuNavigation and MenuBackBoostRelease,5/5, zero warnings/fail/notRun,3.657210s. Artifacts/UIRefresh/Focused. No full gameplay-suite rerun.
- Final visual refinement preserves complete keyboard/controller help and makes pause focus explicit with spaced buttons. Build3 passed4.79s; packaged capture must verify those final pixels. No domain/input routing changed after the five tests.

## Limits

Native values/actions replace illustrative text. Settings retain cycle-on-activation behavior; slider art indicates values. Common service frames are an adaptation, not all page11 unique compositions or wardrobe portraits. Static exports do not implement animated shaders. Physical-device interaction, other resolutions/UI scales, audio, natural gameplay and performance are separate from this focused visual batch. Package5 remains unchanged until the following packaged checkpoint is recorded.

## Package6 checkpoint — September22 02:46 UTC

Source `63f0996832467ec8338e9449078e368b43bec48d` includes final help/focus and title fallback. Build.ps1 packaging passed2m59s:3054 cooked+8skipped,0errors/1known ShipCore warning. Game/editor targets compiled. Log Artifacts/BuildLogs/UIRefresh-Package6.log; inner EXE SHA `127d8e43a7396c89d41a052814e53cd17d66ebfd754258d73556c556dcfea83e`. No runtime source/assets changed after packaging.

Audit551281e6acd84b708cb7bc68d5b861df PASS:338 frozen inputs,152 selected exports including all27 UI textures,366 dependency closure,3054 actual packages,53files/5627889259bytes. No missing/forbidden dependencies; payload unchanged. UFS manifest includes KeaniaOne-Regular.ttf and OFL.txt. Exact font/PNG source validation passes.

One packaged batch b1408a2bc9cb4014ad9575a24bdcc29e PASS: all seven raw PNGs inspected, native menu-center bounds,process0,source/artifact/production-save guards,no test saves. Shipped font visible; Controls retains keyboard/controller help; Pause focus/spacing visible; vitals have no panel/percentages. HUD is a sample overlay on station, not an actual flight maneuver. Log has0Error/Fatal and3baseline warnings (ShipCore,motion-blur priority,motion-vector thread flag).

**Visible performance issue retained:** Pause shows streaming pool about1897MiB over budget; HUD shows video memory248.236MB over budget. These screen warnings are absent from the log Warning count. Cause,persistence and ordinary-play impact are UNCONFIRMED. No FPS/performance or clean-play pass. Lead records follow-up in RPT-20260921-04 without a profiling sweep.

Launcher DryRun passes1600x900/separate profile; no visible window opened. Source/core/docs CI pass63f0996. Local source37, asset/font, changed-file format, docs and whitespace pass. Exact upstream OFL retains its trailing space; scoped Git attributes preserve its bytes. No full gameplay rerun, Figma edit, merge or upload. Later handoff changes are docs-only.
