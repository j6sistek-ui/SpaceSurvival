# Joy foundation review — October 16, 2026

Draft [PR78](https://github.com/j6sistek-ui/SpaceSurvival/pull/78) exposes the existing `claude/joy-bartender` branch that PR74 already depends on. It targets main and preserves the branch's history. Publication and validation did not change its source or the saved game. PR73 and hero/squirrel changes remain held; no PR was merged.

## Exact source and checks

Foundation source: `d178dd4084e8ac9fe7b19c926b8ea7a71ccb3449`; main at review: `d9b299724257fb4827242d6a03752246af5a6880`. The diff contains 46 files, including large texture metadata receipts. Read-only structure checks pass 45 cases and source-digest tests pass 13. Local merge-tree computation and fresh GitHub status show no merge conflict. Exact-head source CI38983446538 and documentation CI38983446536 pass; that does not establish gameplay acceptance.

A separate managed worktree at the exact source built successfully in 167.87 seconds. Its own module is `db10a5d2aaf6380c7809349aaaedc177f9d5b51b9a908ef2403f2ef7728bcc5a`. Private copies of the two required local plugins prevent shared build-output writes. Existing engine/plugin deprecation and non-preferred-toolchain warnings remain.

The single `SpaceSurvival.NpcTalk.Encoding` test runs with NullRHI, no sound, an isolated user directory and NPC AI services disabled. It passes 1 test with 0 failed, 0 not-run and 0 test warnings. The startup log also contains two ShipCore module-start messages logged at Warning severity; this is not a warning-free whole-process claim. No microphone, actual voice/LLM request, rendered world, boarding route or natural input was exercised. Owned process 26148 exits0.

Preservation: all 227 current native files and 273 original plugin files remain unchanged; original source worktree and validation worktree have no tracked edits. Current gameplay remains station`c3dd6ea9` / combined module`b9a9d71e`, a later superset. The isolated test DLL was not copied into the canonical game. No recipe replay, new asset adoption, package or release.

Private evidence: `.agent/local/JoyFoundationReview_20261016/Build.log`, `EncodingLaunch.json`, `EncodingReport/index.json`, `EncodingExit.json`, `PluginSources.json` and `Verification.json`. The temporary validation worktree remains available for focused review; it is not the play destination.

## Review still required

The foundation is broader than Joy's art. It changes talk-helper lifetime/reply handling and automatic GPU budgeting, generic NPC actions/chatter, and boarding/departure to hide the pilot figure and skip authored disembark. It also contains early D-pad bindings superseded by PR74. Review these explicitly against current owner scope before readiness. Historical mipmap/VRAM receipts are retained, not remeasured here. Later accepted voices, tray/contact fixes and controller behavior live in the child stack.

The active entry is RPT-20261016-17 in [KNOWN_ISSUES](../KNOWN_ISSUES.md). Lead owns source/lifecycle/boarding review and scope reconciliation; owner bar appearance/input checks remain separate and do not pause independent work.

## Subsequent helper repair

PR78 itself remains unchanged. PR74 carries the later complete helper identity repair and combined-module build; see [October17 evidence](2026-10-17-npc-helper-reuse.md). It does not authorize the older boarding/pilot changes or establish live audio acceptance.
