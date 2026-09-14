"""Source-only structural checks. This cannot establish a UE build or gameplay pass."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = 0

def require(condition, message):
    global checks
    if not condition:
        raise SystemExit("FAIL: " + message)
    checks += 1

project = json.loads((ROOT / "SpaceSurvival.uproject").read_text(encoding="utf-8"))
require(project["Modules"][0]["Name"] == "SpaceSurvival", "runtime module")
require(project["EngineAssociation"].startswith("5."), "Unreal Engine 5 association")
require(hashlib.sha256((ROOT / "model-rigged.glb").read_bytes()).hexdigest() ==
        "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91", "supplied Acornaut source unchanged")
for name in ("AGENTS.md", "docs/GAME_SCOPE.md", "IMPLEMENT.md", "CODEX_LAUNCH_PROMPT.md",
             "Source/SpaceSurvival/Domain/SurvivalCore.cpp", "Tests/CoreTests.cpp"):
    require((ROOT / name).is_file(), name + " exists")
for header in sorted((ROOT / "Source/SpaceSurvival/Public").glob("*.h")):
    text = header.read_text(encoding="utf-8")
    includes = [line for line in text.splitlines() if line.startswith("#include")]
    require(includes[-1].endswith(f'"{header.stem}.generated.h"'), str(header.name) + " generated include last")
for config in ("DefaultEngine.ini", "DefaultGame.ini", "DefaultInput.ini"):
    require((ROOT / "Config" / config).stat().st_size > 0, config + " nonempty")
print(f"PASS {checks} source structural checks. Unreal build, content import and gameplay remain separate gates.")
