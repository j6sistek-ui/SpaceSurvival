# Preview and combine animations

Start with the prepared example. It uses your owned Space Crew pack and a separate preview mannequin. It does not change the hero, crew or station.

## First: watch it

1. In Unreal's Content Browser, open **Content → SpaceSurvival → Licensed → AnimationWorkbench_20261016**. Double-click **L_AnimationWorkbench**.
2. In the same folder, double-click **LS_Wrench_Start_Loop_End**.
3. Click **Play** at the bottom of Sequencer. If the timeline is zoomed too far, click inside it and press **Home**.

You will see **Start → Loop → Loop → End**. The two middle blocks repeat the work motion. The whole example takes about 10.5 seconds. The camera is already framed for the floating pose.

## Next: make your own copy

Right-click **LS_Wrench_Start_Loop_End** in the Content Browser and choose **Duplicate**. Open the copy. Drag a block to move it; right-click it → **Properties** to inspect its animation, start and end. Keep blocks touching when you want uninterrupted motion. Test each join with Play before adding more.

| Block | Start frame | End frame |
| --- | ---: | ---: |
| Start | 0 | 75 |
| Loop | 75 | 169 |
| Loop | 169 | 263 |
| End | 263 | 314 |

This example runs at 30 frames per second. Its animations share one skeleton. Other characters may need retargeting; choosing an unrelated clip does not make it compatible automatically. There is no wrench prop or repair target yet, so this demonstrates sequencing rather than finished tool contact or station AI.

For a single animation, double-click the animation asset and use its preview player's Play button. The existing local catalog is `C:/Users/j6sis/Documents/Codex/2026-10-15/task/animation_review_index.html`; search by action before opening a candidate in Unreal. Catalog entries include variants and duplicates, and are not a list of individually tested clips.

The prepared map, sequence and licensed source clips are local assets. The source PR contains this guide and the [validation receipt](../validation/2026-10-16-animation-workbench.md). Sequencer arranges a staged performance; gameplay service still uses the existing character logic.

UI references checked October 16, 2026: Epic's [animation-track properties](https://dev.epicgames.com/documentation/unreal-engine/cinematic-animation-track-in-unreal-engine?lang=en-US) and [Sequencer shortcuts](https://dev.epicgames.com/documentation/unreal-engine/sequencer-hotkeys-in-unreal-engine?lang=en-US).
