# MotionBoard

Local animation preview and rough clip ordering. This does not modify Unreal,
retarget characters, repair skin weights or create final connected choreography.

With Docker Desktop running and the private library prepared, run this from the
project root:

```powershell
docker compose -f Tools/MotionBoard/compose.yaml up --build -d
```

Open `http://127.0.0.1:8769`. Docker uses the Python standard-library image with no
package installs. The frontend and library are mounted read-only; only board
state is writable. The container listens internally for Docker forwarding, while
its published port is restricted to host `127.0.0.1`. Do not change that mapping
to a LAN address. Stop it with:

```powershell
docker compose -f Tools/MotionBoard/compose.yaml down
```

Use **All cards** above the animation cards to set every card preview to
**¼×, ½×, 1× or 2×**. The browser remembers that preference. Changing it or
pausing card previews does not change the main preview, slot trims, durations
or exported proposal timing.

Select a numbered slot, then choose its **Playback mode**:

- **Stretch to duration** plays the trimmed excerpt once, changing its speed to
  fit **Play for**. This is the unchanged default for older boards.
- **Repeat for seconds** repeats the trim at **Playback speed** until the chosen
  total time. A 0.5-second clip at 1× repeated for 10 seconds plays 20 cycles.
- **Repeat count** derives total time from trim length × count ÷ speed.
  A 0.5-second clip repeated 10 times at 1× occupies 5 seconds. Fractional counts
  finish partway through the final cycle.

Start/end remain source seconds. The calculated total is timeline seconds.
Reverse reverses each trimmed cycle; it does not reverse slot order. Interior
loop boundaries restart the trim; the final endpoint shows the completed or
partial cycle. Seams are hard cuts, with no blending or contact repair. Exported
proposal JSON includes each item's mode/count/speed and a derived `playbackPlan`
with local loop boundaries and absolute slot times; source motion is unchanged.
Old items are not rewritten on load. If an existing saved trim extends beyond
a newer export, timing edits preserve it and show a warning that the preview
holds the export's last frame; newly entered trim ends must fit the current clip.

Existing Python 3.11+ is also supported without Docker:

```powershell
python Tools/MotionBoard/server.py
```

Use `--port 8770` for a native-only alternate port. Native mode binds loopback.
Do not run Docker and native mode against the same state folder simultaneously.

Private model, vendor dependencies, manifest and saves live under
`SourceAssets/MotionBoard/` (ignored by Git): `Meshy_Reference.glb`,
`vendor/`, `manifest.json`, `libraries/<id>.glb`, and `state/board.json`.
`MOTION_BOARD_ASSETS` and `MOTION_BOARD_STATE` explicitly override the asset and
state directories; Docker sets these to `/assets` and `/state` respectively.
Old prototype `board.json` files in the asset root are not silently migrated or
overwritten. Preserve them; proposal JSON import is not yet available in the frontend.
The manifest lists each approved library's id, name, relative URL and source hash.
Only explicitly allowlisted frontend/vendor files and manifest-listed GLBs are
served; this is not a general file browser or upload service. Browser-local files
are handled by the frontend and are not uploaded by this server.
Choose animated `.glb` or `.fbx` files from a PC folder in the frontend; there is no broad
drive scan. Native Unreal `.uasset` animation packs require a compatible mesh and
an export before this browser can preview them. SensualMoves, dance and Flips
packs are not claimed available until their exported library files are prepared
and registered in the manifest.

Save replaces `board.json` atomically. Two tabs cannot silently overwrite each
other: a stale save receives HTTP409; reload the current board before retrying.
Source clips keep their names; an item with `clip: null` is a transition note.
Trims and reversed/slowed clips are rough previews, not validated retargets,
physical contacts, animation blends or export-ready routines. A private GLB with
valid keys still needs visual review on its own rig.

API: `GET /api/info`, `GET /api/project`, and `PUT /api/project` with
`{"revision": 0, "project": {"version": 1, "title": "My routine", "items": []}}`.
PUT requires the page's matching Origin and JSON Content-Type; it returns the new
revision or HTTP409. Requests are bounded to 2MiB, eight occupied slots and 128
library records. Optional item `slot` is an integer0–7; explicit slots must be
unique. Empty slots are omitted from the items array, rather than saved as null.
The shared board revision is separate from source asset hashes.
Optional item fields are `playbackMode` (`stretch`, `repeat-duration`, or
`repeat-count`), `playbackSpeed` (0.05–8, default 1), and `repeatCount` (>0–10000).
`duration` always stores total timeline seconds; count-mode saves must agree
with the derived total. A slot is limited to 3600 seconds and 10000 cycles.

Run the backend regression tests in the running Docker service:

```powershell
docker compose -f Tools/MotionBoard/compose.yaml exec -T motionboard python server_test.py -v
```

Tests use temporary asset/state directories and a temporary loopback server; they
never read or modify the owner's saved board. They cover request/path isolation,
eight-slot validation, stale-revision HTTP409, corrupt-save preservation and
atomic replacement. They do not validate browser animation rendering.

Run frontend CPU checks with the existing Node runtime:

```powershell
cd Tools/MotionBoard
npm run check
```

The shared timing tests cover legacy stretch, repeated/partial/reversed cycles,
exact boundaries, source trim preservation, pause/reload and card-speed
independence. Private framing/FBX fixture checks skip explicitly when their
local inputs are absent. No test starts Unreal or changes an owner's board.
