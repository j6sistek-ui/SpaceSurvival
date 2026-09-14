# Internal integration contract

Authoritative scope remains docs/GAME_SCOPE.md and IMPLEMENT.md. This file assigns implementation ownership, not design authority.

- `Source/SpaceSurvival/Domain/SurvivalCore.h/.cpp`: engine-independent C++17 rules in namespace `SS`; owned by domain specialist. No UObject references or rendering.
- `Source/SpaceSurvival/Public/SSWorldActors.h`, `Private/SSWorldActors.cpp`: hazards, enemies, projectiles, pickups, optional encounters/depot and Director component; owned by world specialist.
- `Scripts/AuthorContent.py`, `ContentSource/`, content documentation: deterministic Unreal editor content import/authoring; owned by content specialist.
- Lead owns project targets/module, config, `SSGameInstance`, `SSShip`, `SSGameMode`, `SSHUD`, `SSStation`, portable build/verification integration and documentation reconciliation.

Runtime wiring will use the finalized domain header as its contract. SSGameInstance owns `SS::Session Session`; ship flight owns physical position/velocity only and reads durable run values. SSGameMode owns phases, actor lifecycle, station transitions. World actors notify GameMode of kills/events and apply ship damage through SSShip methods. No actor bypasses domain economic/progression validation.

Coordinate before editing another owner's files. Do not commit independently. Never describe generated source/assets as tested gameplay. No installs or remote writes by specialists.
