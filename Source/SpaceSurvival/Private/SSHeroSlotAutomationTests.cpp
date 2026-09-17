#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "SSPhase1Data.h"
#include "SSShip.h"
#include "SSStation.h"
#include "SSStationPoseTransition.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/PoseSnapshot.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "HAL/IConsoleManager.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

#if WITH_DEV_AUTOMATION_TESTS
namespace
{
struct FSSHeroTestWorld
{
    UWorld *World = UWorld::CreateWorld(EWorldType::Game, false);
    FSSHeroTestWorld()
    {
        if (World)
            GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
    }
    ~FSSHeroTestWorld()
    {
        if (World)
        {
            World->DestroyWorld(false);
            GEngine->DestroyWorldContext(World);
        }
    }
};

// Every path and number the walker and the pilot used to carry as a literal, written out once more.
// This table is deliberately a second copy of the data: the roster may be edited, but editing it must
// not be able to move the hero the game renders today without this test saying so out loud.
const TCHAR *const TrooperMesh =
    TEXT("/Game/SciFITrooper_Man_03/SkeletalMesh/SK_SciFITrooper_Man_03.SK_SciFITrooper_Man_03");
const TCHAR *const TrooperWalk = TEXT("/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonWalk.ThirdPersonWalk");
const TCHAR *const TrooperExit =
    TEXT("/Game/SciFITrooper_Man_03/DemoContent/Anims/ThirdPersonJump_End.ThirdPersonJump_End");
const TCHAR *const AcornautMesh = TEXT("/Game/SpaceSurvival/Character/SK_AcornautTailV2.SK_AcornautTailV2");
const TCHAR *const AcornautWalk = TEXT("/Game/SpaceSurvival/Character/A_WalkLegRepair.A_WalkLegRepair");
const TCHAR *const AcornautPilot = TEXT("/Game/SpaceSurvival/Character/A_PilotGripFit.A_PilotGripFit");
const TCHAR *const AcornautExit = TEXT("/Game/SpaceSurvival/Character/A_DisembarkLegRepair.A_DisembarkLegRepair");
const TCHAR *const SquirrelMesh = TEXT("/Game/SpaceSurvival/Licensed/Hero/SK_SquirrelHero.SK_SquirrelHero");
const TCHAR *const SquirrelWalk = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelWalk.A_SquirrelWalk");
const TCHAR *const SquirrelPilot = TEXT("/Game/SpaceSurvival/Licensed/Hero/A_SquirrelPilot.A_SquirrelPilot");
/** Measured in the Swift cockpit, .agent/local/HeroSquirrel/Stage6_Clips/SeatFit.json, and written out
 *  here for the same reason every other number in this table is: so that losing it says so out loud. */
const FVector SquirrelMount(-12.5, 0, 27.933);
// Paths no build has, used to say "this hero is not installed" without waiting for one not to be.
const TCHAR *const NoSuchMesh = TEXT("/Game/SpaceSurvival/Character/SK_NoSuchHero.SK_NoSuchHero");
const TCHAR *const NoSuchWalk = TEXT("/Game/SpaceSurvival/Character/A_NoSuchWalk.A_NoSuchWalk");
const TCHAR *const NoSuchPilot = TEXT("/Game/SpaceSurvival/Character/A_NoSuchPilot.A_NoSuchPilot");

float WalkingFloorGap()
{
    return (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * .5f;
}
int32 AsInt(ESSHeroIdentity Identity)
{
    return static_cast<int32>(Identity);
}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHeroRoster, "SpaceSurvival.Integration.HeroRoster",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSHeroRoster::RunTest(const FString &)
{
    auto *Content = NewObject<USSPhase1Data>();
    if (!TestNotNull(TEXT("Construct the actual runtime content defaults"), Content))
        return false;
    if (!TestEqual(TEXT("Three heroes, in preference order"), Content->Heroes.Num(), 3))
        return false;
    // The real hero is asked about first, so importing it is the whole swap - and on September 17 that
    // import happened. Nothing below asks whether this machine has the files. Whether a hero is installed
    // is a fact about a build, not about the roster: these assets live under the ignored Licensed/ tree,
    // so the same roster answers one way here and another on a machine without the pack, and a test that
    // pinned either answer would be pinning today's content rather than the rule. The rule - order, and
    // what selection does with a given set of files - is proved below on rosters this test builds itself.
    TestEqual(TEXT("The hero the game is about is asked about first"), AsInt(Content->Heroes[0].Identity),
              AsInt(ESSHeroIdentity::Squirrel));
    TestEqual(TEXT("The stand-in is second"), AsInt(Content->Heroes[1].Identity), AsInt(ESSHeroIdentity::Trooper));
    TestEqual(TEXT("The shipped hero is last"), AsInt(Content->Heroes[2].Identity), AsInt(ESSHeroIdentity::Acornaut));
    TestEqual(TEXT("The pawns are built with the shipped hero"), AsInt(FSSHeroDefinition::Fallback().Identity),
              AsInt(ESSHeroIdentity::Acornaut));

    const FSSHeroDefinition Trooper = Content->Heroes[1];
    TestEqual(TEXT("Trooper mesh path"), Trooper.MeshPath, FString(TrooperMesh));
    TestEqual(TEXT("Trooper walk clip"), Trooper.WalkClipPath, FString(TrooperWalk));
    TestEqual(TEXT("Trooper exit clip"), Trooper.DisembarkClipPath, FString(TrooperExit));
    TestTrue(TEXT("The trooper has never been seated, so it cannot take the pilot slot"),
             Trooper.PilotClipPath.IsEmpty());
    TestEqual(TEXT("Trooper is fitted to 180 cm rather than to a scale"), Trooper.FitHeight, 180.f, 0.f);
    TestEqual(TEXT("A fitted hero declares no sole offset of its own"), Trooper.SoleOffset, 0.f, 0.f);
    TestEqual(TEXT("Trooper mesh yaw"), Trooper.MeshYaw, -90.f, 0.f);
    TestEqual(TEXT("Trooper walk speed"), Trooper.WalkSpeed, 180.f, 0.f);
    TestEqual(TEXT("Trooper walk handoff second"), Trooper.WalkHandoffSeconds, .308333333f, 0.f);
    TestTrue(TEXT("The trooper names the mannequin bones its own rig actually has"),
             Trooper.RootBone == TEXT("root") && Trooper.PelvisBone == TEXT("pelvis") &&
                 Trooper.LeftFootBone == TEXT("foot_l") && Trooper.RightFootBone == TEXT("foot_r") &&
                 Trooper.LeftHandBone == TEXT("hand_l") && Trooper.RightHandBone == TEXT("hand_r"));

    const FSSHeroDefinition Acornaut = Content->Heroes[2];
    TestEqual(TEXT("Acornaut mesh path"), Acornaut.MeshPath, FString(AcornautMesh));
    TestEqual(TEXT("Acornaut walk clip"), Acornaut.WalkClipPath, FString(AcornautWalk));
    TestEqual(TEXT("Acornaut pilot clip"), Acornaut.PilotClipPath, FString(AcornautPilot));
    TestEqual(TEXT("Acornaut exit clip"), Acornaut.DisembarkClipPath, FString(AcornautExit));
    TestEqual(TEXT("Acornaut measured sole offset"), Acornaut.SoleOffset, 62.90269494f, 0.f);
    TestEqual(TEXT("Acornaut scale"), Acornaut.MeshScale, 1.5f, 0.f);
    TestEqual(TEXT("Acornaut is scaled, not fitted"), Acornaut.FitHeight, 0.f, 0.f);
    TestEqual(TEXT("Acornaut mesh yaw"), Acornaut.MeshYaw, -90.f, 0.f);
    TestEqual(TEXT("Acornaut pilot mount"), Acornaut.PilotMountOffset, FVector(-15, 0, 72), 0.f);
    TestEqual(TEXT("Acornaut walk handoff second"), Acornaut.WalkHandoffSeconds, .308333333f, 0.f);
    TestEqual(TEXT("Acornaut walk speed"), Acornaut.WalkSpeed, 180.f, 0.f);
    TestTrue(TEXT("Acornaut bone names are the ones the code used to spell out"),
             Acornaut.PelvisBone == TEXT("Pelvis") && Acornaut.LeftFootBone == TEXT("L_Foot") &&
                 Acornaut.RightFootBone == TEXT("R_Foot") && Acornaut.LeftHandBone == TEXT("L_Wrist") &&
                 Acornaut.RightHandBone == TEXT("R_Wrist"));
    // Three heroes, three vocabularies for the same body: that is the whole reason the names are data
    // rather than literals. Only the pelvis is spelled the same way twice, and only case-insensitively.
    TestTrue(TEXT("The stand-in and the shipped hero disagree about what a hand and a foot are called"),
             Trooper.LeftHandBone != Acornaut.LeftHandBone && Trooper.LeftFootBone != Acornaut.LeftFootBone);

    const FSSHeroDefinition Squirrel = Content->Heroes[0];
    TestEqual(TEXT("Squirrel mesh path"), Squirrel.MeshPath, FString(SquirrelMesh));
    TestEqual(TEXT("Squirrel walk clip"), Squirrel.WalkClipPath, FString(SquirrelWalk));
    TestEqual(TEXT("Squirrel pilot clip"), Squirrel.PilotClipPath, FString(SquirrelPilot));
    // An empty exit clip is not a missing asset, it is this hero saying it does not climb out. The ship
    // has no door, so the owner cancelled the exit animation and had the gap logged as RPT-20260917-01:
    // when the docking motion finishes this hero is simply standing outside. Every test that used to
    // assume a climb-out now asks this field first, so this is the line that decides all of them.
    TestTrue(TEXT("The squirrel has no exit clip, by decision rather than by omission"),
             Squirrel.DisembarkClipPath.IsEmpty());
    TestEqual(TEXT("Squirrel stands on its own origin"), Squirrel.SoleOffset, 0.f, 0.f);
    TestEqual(TEXT("Squirrel scale"), Squirrel.MeshScale, 1.5f, 0.f);
    TestEqual(TEXT("Squirrel is scaled, not fitted"), Squirrel.FitHeight, 0.f, 0.f);
    TestEqual(TEXT("Squirrel mesh yaw"), Squirrel.MeshYaw, -90.f, 0.f);
    // The mount is measured, and measuring it was the whole point: this hero's origin is its sole, so
    // inheriting the Acornaut's 72 cm - which is 62.9 cm of somebody else's sole plus a seat - left it
    // floating 44.067 cm above the cushion, a third of its own height. Pinned beside the Acornaut's so
    // that a hero which quietly stops overriding it fails here rather than in a capture.
    TestEqual(TEXT("Squirrel pilot mount, measured in the Swift cockpit"), Squirrel.PilotMountOffset, SquirrelMount,
              0.f);
    TestFalse(TEXT("And it is not the mount it used to inherit, which is what the float was"),
              Squirrel.PilotMountOffset.Equals(Acornaut.PilotMountOffset));
    TestEqual(TEXT("Squirrel walk handoff second"), Squirrel.WalkHandoffSeconds, .308333333f, 0.f);
    TestEqual(TEXT("Squirrel walk speed"), Squirrel.WalkSpeed, 180.f, 0.f);
    TestTrue(TEXT("Squirrel bone names are its own, measured in Unreal from the imported base"),
             Squirrel.RootBone == TEXT("Root") && Squirrel.PelvisBone == TEXT("Pelvis") &&
                 Squirrel.LeftFootBone == TEXT("L_Foot") && Squirrel.RightFootBone == TEXT("R_Foot") &&
                 Squirrel.LeftHandBone == TEXT("L_Hand") && Squirrel.RightHandBone == TEXT("R_Hand"));
    // Both kinds of hero exist, which is what lets the tests below cover both exits rather than whichever
    // one this build happens to install.
    TestTrue(TEXT("The roster carries a hero that climbs out and a hero that does not"),
             !Acornaut.DisembarkClipPath.IsEmpty() && !Trooper.DisembarkClipPath.IsEmpty() &&
                 Squirrel.DisembarkClipPath.IsEmpty());
    for (const auto &Entry : Content->Heroes)
        AddInfo(FString::Printf(TEXT("HERO_ROSTER id=%s walker=%d pilot=%d climbsOut=%d mesh=%s"), *Entry.Id.ToString(),
                                Entry.Installed(ESSHeroSlot::Walker) ? 1 : 0,
                                Entry.Installed(ESSHeroSlot::Pilot) ? 1 : 0, Entry.DisembarkClipPath.IsEmpty() ? 0 : 1,
                                *Entry.MeshPath));
    AddInfo(FString::Printf(TEXT("HERO_ROSTER_SELECTED walker=%s pilot=%s"),
                            *Content->SelectHero(ESSHeroSlot::Walker).Id.ToString(),
                            *Content->SelectHero(ESSHeroSlot::Pilot).Id.ToString()));

    // Presence is what selection reads, and it is read here off a roster whose files this test decides,
    // so the claim holds on the machine that has the licensed pack and on the machine that does not.
    {
        auto *Uninstalled = NewObject<USSPhase1Data>();
        if (!TestNotNull(TEXT("Construct a roster whose front hero has no files"), Uninstalled))
            return false;
        Uninstalled->Heroes[0].MeshPath = FString(NoSuchMesh);
        Uninstalled->Heroes[0].WalkClipPath = FString(NoSuchWalk);
        Uninstalled->Heroes[0].PilotClipPath = FString(NoSuchPilot);
        TestFalse(TEXT("A hero whose files are not on disk is not installed for the walker"),
                  Uninstalled->Heroes[0].Installed(ESSHeroSlot::Walker));
        TestFalse(TEXT("A hero whose files are not on disk is not installed for the pilot"),
                  Uninstalled->Heroes[0].Installed(ESSHeroSlot::Pilot));
        TestNotEqual(TEXT("An uninstalled hero is skipped, never selected, for the walker"),
                     AsInt(Uninstalled->SelectHero(ESSHeroSlot::Walker).Identity),
                     AsInt(Uninstalled->Heroes[0].Identity));
        TestNotEqual(TEXT("An uninstalled hero is skipped, never selected, for the pilot"),
                     AsInt(Uninstalled->SelectHero(ESSHeroSlot::Pilot).Identity),
                     AsInt(Uninstalled->Heroes[0].Identity));
    }
    {
        // A hero that has never been seated is not a candidate for the seat, however far up the roster it
        // sits - the claim the stand-in used to carry, now made without depending on the stand-in being
        // installed. Every entry is given the shipped hero's own assets, which this repository tracks, so
        // the only thing that can decide the seat here is the empty clip.
        auto *Seatless = NewObject<USSPhase1Data>();
        if (!TestNotNull(TEXT("Construct a roster whose front hero has never been seated"), Seatless))
            return false;
        for (auto &Entry : Seatless->Heroes)
        {
            Entry.MeshPath = FString(AcornautMesh);
            Entry.WalkClipPath = FString(AcornautWalk);
            Entry.PilotClipPath = FString(AcornautPilot);
        }
        Seatless->Heroes[0].PilotClipPath = FString();
        TestTrue(TEXT("A hero with a mesh and a walk clip takes the deck"),
                 Seatless->Heroes[0].Installed(ESSHeroSlot::Walker));
        TestFalse(TEXT("The same hero with no pilot clip cannot take the seat"),
                  Seatless->Heroes[0].Installed(ESSHeroSlot::Pilot));
        TestEqual(TEXT("The walker slot goes to the front hero"),
                  AsInt(Seatless->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(Seatless->Heroes[0].Identity));
        TestEqual(TEXT("The pilot slot walks past it to the first hero that has been seated"),
                  AsInt(Seatless->SelectHero(ESSHeroSlot::Pilot).Identity), AsInt(Seatless->Heroes[1].Identity));
    }

    // A roster whose assets are all absent still answers, with the hero the pawns were built with.
    auto *Absent = NewObject<USSPhase1Data>();
    if (!TestNotNull(TEXT("Construct a second content object"), Absent))
        return false;
    for (auto &Entry : Absent->Heroes)
    {
        Entry.MeshPath = FString(NoSuchMesh);
        Entry.WalkClipPath = FString(NoSuchWalk);
        Entry.PilotClipPath = FString(NoSuchPilot);
        TestFalse(TEXT("A hero with no assets on disk is not installed"), Entry.Installed(ESSHeroSlot::Walker));
    }
    TestEqual(TEXT("With nothing installed, selection lands on the hero the pawns were built with"),
              AsInt(Absent->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(FSSHeroDefinition::Fallback().Identity));
    // Presence decides, not position. Give the middle hero real assets while the one in front of it and
    // the one behind it stay missing: it must win, and it is not the hero selection falls back to, so this
    // cannot pass by accident. This is the shape the swap itself relies on. The assets handed over are the
    // shipped hero's, which this repository tracks, so what is being tested is the walk past a missing
    // entry rather than whether a licensed pack happens to be installed on this machine.
    Absent->Heroes[1].MeshPath = FString(AcornautMesh);
    Absent->Heroes[1].WalkClipPath = FString(AcornautWalk);
    TestEqual(TEXT("Selection walks past a missing hero to the installed one behind it"),
              AsInt(Absent->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(ESSHeroIdentity::Trooper));

    // An empty roster is not a reason to have no hero at all.
    auto *Empty = NewObject<USSPhase1Data>();
    if (!TestNotNull(TEXT("Construct a third content object"), Empty))
        return false;
    Empty->Heroes.Empty();
    TestEqual(TEXT("An empty roster still answers with the built-in hero"),
              AsInt(Empty->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(FSSHeroDefinition::Fallback().Identity));
    TestEqual(TEXT("An empty roster's built-in hero still carries the measured sole offset"),
              Empty->SelectHero(ESSHeroSlot::Walker).SoleOffset, 62.90269494f, 0.f);

    // Without a mesh to measure, an unfitted hero is exactly its declared scale and product.
    TestEqual(TEXT("An unfitted hero renders at its declared scale"), Acornaut.RenderedScale(nullptr), 1.5f, 0.f);
    TestEqual(TEXT("An unfitted hero's scaled sole is the measured product"), Acornaut.ScaledSoleOffset(nullptr),
              double(62.90269494f * 1.5f), 0.);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHeroSlotTransforms, "SpaceSurvival.Integration.HeroSlotTransforms",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSHeroSlotTransforms::RunTest(const FString &)
{
    FSSHeroTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated hero world"), Fixture.World))
        return false;
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    auto *Ship = Fixture.World->SpawnActor<ASSShip>();
    if (!TestNotNull(TEXT("Spawn the actual walking pawn"), Walker) ||
        !TestNotNull(TEXT("Spawn the actual ship"), Ship))
        return false;
    // Before either pawn asks what content is installed. Both are built with the shipped hero, so this
    // is the only place the 62.90269494 cm sole reaches a rendered mesh position in a build where the
    // stand-in wins the slot and BeginPlay overwrites it a moment later. Without this the measured
    // constant the whole refactor is about is pinned as data and never as a hero standing on the deck.
    const float BuiltHalfHeight = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    AddInfo(FString::Printf(TEXT("HERO_BUILT z=%.9f scale=%.9f half=%.9f"), Walker->GetMesh()->GetRelativeLocation().Z,
                            Walker->GetMesh()->GetRelativeScale3D().Z, BuiltHalfHeight));
    // The double() is not decoration: MeshLift carries this sum at double width, so the expected value
    // has to as well, or the two disagree in the last bits of a float for no reason anyone can see.
    TestEqual(TEXT("The pawn is built standing the shipped hero's measured sole on the deck plates"),
              Walker->GetMesh()->GetRelativeLocation(),
              FVector(0, 0, double(62.90269494f * 1.5f) - BuiltHalfHeight - WalkingFloorGap() + 2.75f), 1e-5f);
    TestEqual(TEXT("The pawn is built at the shipped hero's scale"), Walker->GetMesh()->GetRelativeScale3D(),
              FVector(1.5f), 1e-6f);
    TestEqual(TEXT("The pawn is built at the shipped hero's yaw"), Walker->GetMesh()->GetRelativeRotation(),
              FRotator(0, -90, 0), 1e-6f);
    TestEqual(TEXT("The seat is built at the shipped hero's mount"), Ship->Pilot->GetRelativeLocation(),
              FVector(-15, 0, 72), 0.f);
    Walker->DispatchBeginPlay();
    Ship->DispatchBeginPlay();
    const FSSHeroDefinition Hero = Walker->GetHero();
    const FSSHeroDefinition PilotHero = Ship->GetPilotHero();
    auto *HeroMesh = Walker->GetMesh()->GetSkeletalMeshAsset();
    auto *PilotMesh = Ship->Pilot->GetSkeletalMeshAsset();
    if (!TestNotNull(TEXT("BeginPlay resolves a walking mesh"), HeroMesh) ||
        !TestNotNull(TEXT("BeginPlay resolves a seated mesh"), PilotMesh))
        return false;
    AddInfo(FString::Printf(TEXT("HERO_SLOTS walker=%s mesh=%s pilot=%s pilotMesh=%s"), *Hero.Id.ToString(),
                            *HeroMesh->GetPathName(), *PilotHero.Id.ToString(), *PilotMesh->GetPathName()));

    // Only one hero can wear a slot at a time, so a live pawn can only prove one of them. Every other
    // installed hero still has to agree with the measurements this game was built around.
    const USSPhase1Data *Content = Walker->Tuning;
    if (!TestNotNull(TEXT("The walking pawn resolved its content"), Content))
        return false;
    AddInfo(FString::Printf(TEXT("HERO_CONTENT asset=%s heroes=%d"), *Content->GetPathName(), Content->Heroes.Num()));
    {
        // The pawn wears the first installed hero in the roster, not merely some installed hero: a
        // roster that failed to load would answer with the fallback and quietly demote the stand-in.
        int32 Expected = INDEX_NONE;
        for (int32 I = 0; I < Content->Heroes.Num() && Expected == INDEX_NONE; ++I)
            if (Content->Heroes[I].Installed(ESSHeroSlot::Walker))
                Expected = I;
        if (TestTrue(TEXT("At least one hero in the roster is installed"), Expected != INDEX_NONE))
            TestEqual(TEXT("The walker wears the first installed hero in the roster"), AsInt(Hero.Identity),
                      AsInt(Content->Heroes[Expected].Identity));
    }
    {
        // The roster test pins the C++ constructor's copy. The game loads DA_Phase1, and the moment that
        // asset carries a serialized Heroes array an edit to it is invisible there. The hero this build
        // is not currently wearing would then have no cover at all, so its numbers are checked here,
        // against the asset the game actually loaded. Its handoff second is the one that matters most:
        // the frozen walk pose and the last frame of the disembark clip are the same pose only at it.
        const FSSHeroDefinition Shipped = Content->Hero(ESSHeroIdentity::Acornaut);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its mesh"), Shipped.MeshPath, FString(AcornautMesh));
        TestEqual(TEXT("The loaded asset's shipped hero keeps its walk clip"), Shipped.WalkClipPath,
                  FString(AcornautWalk));
        TestEqual(TEXT("The loaded asset's shipped hero keeps its pilot clip"), Shipped.PilotClipPath,
                  FString(AcornautPilot));
        TestEqual(TEXT("The loaded asset's shipped hero keeps its exit clip"), Shipped.DisembarkClipPath,
                  FString(AcornautExit));
        TestEqual(TEXT("The loaded asset's shipped hero keeps the handoff second the freeze depends on"),
                  Shipped.WalkHandoffSeconds, .308333333f, 0.f);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its 180 cm/s stride"), Shipped.WalkSpeed, 180.f, 0.f);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its yaw"), Shipped.MeshYaw, -90.f, 0.f);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its measured sole"), Shipped.SoleOffset, 62.90269494f,
                  0.f);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its scale"), Shipped.MeshScale, 1.5f, 0.f);
        TestEqual(TEXT("The loaded asset's shipped hero keeps its mount"), Shipped.PilotMountOffset,
                  FVector(-15, 0, 72), 0.f);
        TestTrue(TEXT("The loaded asset's shipped hero keeps the bone names the code used to spell out"),
                 Shipped.PelvisBone == TEXT("Pelvis") && Shipped.LeftFootBone == TEXT("L_Foot") &&
                     Shipped.RightFootBone == TEXT("R_Foot") && Shipped.LeftHandBone == TEXT("L_Wrist") &&
                     Shipped.RightHandBone == TEXT("R_Wrist"));
        // The imported hero, through the same asset. Its mount is the number a serialized Heroes array
        // could silently take back: DA_Phase1 carries no Heroes array today, so the constructor is what
        // the game reads, and the day it does carry one this is where an out-of-date copy of the mount
        // is caught rather than in a capture of a hero floating over the cushion.
        const FSSHeroDefinition Imported = Content->Hero(ESSHeroIdentity::Squirrel);
        TestEqual(TEXT("The loaded asset's imported hero keeps its mesh"), Imported.MeshPath, FString(SquirrelMesh));
        TestEqual(TEXT("The loaded asset's imported hero keeps its walk clip"), Imported.WalkClipPath,
                  FString(SquirrelWalk));
        TestEqual(TEXT("The loaded asset's imported hero keeps its pilot clip"), Imported.PilotClipPath,
                  FString(SquirrelPilot));
        TestTrue(TEXT("The loaded asset's imported hero still has no exit clip"), Imported.DisembarkClipPath.IsEmpty());
        TestEqual(TEXT("The loaded asset's imported hero keeps its measured mount"), Imported.PilotMountOffset,
                  SquirrelMount, 0.f);
        TestEqual(TEXT("The loaded asset's imported hero still stands on its own origin"), Imported.SoleOffset, 0.f,
                  0.f);
        TestEqual(TEXT("The loaded asset's imported hero keeps its scale"), Imported.MeshScale, 1.5f, 0.f);
    }
    if (Content)
        for (const auto &Entry : Content->Heroes)
        {
            if (!Entry.Installed(ESSHeroSlot::Walker))
                continue;
            auto *Mesh = LoadObject<USkeletalMesh>(nullptr, *Entry.MeshPath);
            if (!TestNotNull(TEXT("An installed hero's mesh loads"), Mesh))
                continue;
            if (Entry.Identity == ESSHeroIdentity::Acornaut)
            {
                TestEqual(TEXT("The shipped hero still renders at 1.5"), Entry.RenderedScale(Mesh), 1.5f, 0.f);
                TestEqual(TEXT("The shipped hero's sole is still 62.90269494 cm below its origin, scaled"),
                          Entry.ScaledSoleOffset(Mesh), double(62.90269494f * 1.5f), 0.);
            }
            else if (Entry.Identity == ESSHeroIdentity::Trooper)
            {
                const FBoxSphereBounds Bounds = Mesh->GetBounds();
                const float Height = Bounds.BoxExtent.Z * 2.f;
                const float Scale = Height > 1.f ? 180.f / Height : 1.f;
                TestEqual(TEXT("The stand-in is still fitted to 180 cm from its own bounds"), Entry.RenderedScale(Mesh),
                          Scale, 0.f);
                TestEqual(TEXT("The stand-in's sole is still the bottom of its scaled bounds"),
                          Entry.ScaledSoleOffset(Mesh), -(Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale, 0.);
            }
            else if (Entry.Identity == ESSHeroIdentity::Squirrel)
            {
                TestEqual(TEXT("The imported hero still renders at 1.5"), Entry.RenderedScale(Mesh), 1.5f, 0.f);
                TestEqual(TEXT("The imported hero's sole is still its own origin, so the scaled offset is zero"),
                          Entry.ScaledSoleOffset(Mesh), 0., 0.);
                // Against the asset, not against the declaration. A hero with no FitHeight has its sole
                // offset read straight off SoleOffset and the mesh is never consulted, so the assertion
                // above is 0 == 0 for as long as the constant says zero - it cannot notice the mesh
                // moving underneath it. This one can. The whole seat measurement rests on this hero's
                // origin being its sole, and this mesh lives under the ignored Licensed tree and is
                // expected to be re-imported; an export that moved the armature would bury the hero in
                // the deck plates or float it over them, in the station and in the seat both, with every
                // other number in this file still agreeing with itself. Measured z_min is -0.0045 cm.
                const FBoxSphereBounds Bounds = Mesh->GetBounds();
                TestEqual(TEXT("The imported hero's mesh really does stand on its own origin"),
                          double(Bounds.Origin.Z - Bounds.BoxExtent.Z), 0., .05);
            }
            AddInfo(FString::Printf(TEXT("HERO_FIT id=%s scale=%.9f scaledSole=%.9f boundsZMin=%.9f"),
                                    *Entry.Id.ToString(), Entry.RenderedScale(Mesh), Entry.ScaledSoleOffset(Mesh),
                                    Mesh->GetBounds().Origin.Z - Mesh->GetBounds().BoxExtent.Z));
        }

    // The walking pawn's mesh component against the arithmetic the code carried before the data existed,
    // spelled out here exactly as it was spelled out there. The tolerance is a ten-thousandth of a
    // millimetre: the only slack is that this arithmetic is now carried at one width rather than two.
    const float HalfHeight = Walker->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
    double ExpectedScale = 0., ExpectedZ = 0.;
    if (Hero.Identity == ESSHeroIdentity::Acornaut)
    {
        ExpectedScale = 1.5f;
        ExpectedZ = double(62.90269494f * 1.5f) - HalfHeight - WalkingFloorGap() + 2.75f;
        TestEqual(TEXT("The shipped hero wears its own mesh"), HeroMesh->GetPathName(), FString(AcornautMesh));
    }
    else if (Hero.Identity == ESSHeroIdentity::Trooper)
    {
        const FBoxSphereBounds Bounds = HeroMesh->GetBounds();
        const float Height = Bounds.BoxExtent.Z * 2.f;
        const float Scale = Height > 1.f ? 180.f / Height : 1.f;
        ExpectedScale = Scale;
        ExpectedZ = -(Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale - HalfHeight - WalkingFloorGap() + 2.75f;
        TestEqual(TEXT("The stand-in wears its own mesh"), HeroMesh->GetPathName(), FString(TrooperMesh));
    }
    else if (Hero.Identity == ESSHeroIdentity::Squirrel)
    {
        // Its origin is its sole, so the sole term is zero and the mesh hangs at nothing but the capsule
        // and the walking floor gap. That is a different number from the other two rather than a
        // simplification of them, and writing it out is what catches this hero quietly inheriting
        // 62.90269494 cm of somebody else's boots - which is exactly what its seat mount did.
        ExpectedScale = 1.5f;
        ExpectedZ = double(0.f * 1.5f) - HalfHeight - WalkingFloorGap() + 2.75f;
        TestEqual(TEXT("The imported hero wears its own mesh"), HeroMesh->GetPathName(), FString(SquirrelMesh));
    }
    else if (!TestTrue(TEXT("A hero this test has no expected numbers for is wearing the walker slot"), false))
        return false;
    AddInfo(FString::Printf(TEXT("HERO_WALKER_MESH z=%.9f expectedZ=%.9f scale=%.9f expectedScale=%.9f half=%.9f"),
                            Walker->GetMesh()->GetRelativeLocation().Z, ExpectedZ,
                            Walker->GetMesh()->GetRelativeScale3D().Z, ExpectedScale, HalfHeight));
    TestEqual(TEXT("The walker mesh sits where the old literal arithmetic put it"),
              Walker->GetMesh()->GetRelativeLocation(), FVector(0, 0, ExpectedZ), 1e-5f);
    TestEqual(TEXT("The walker mesh wears the old scale"), Walker->GetMesh()->GetRelativeScale3D(),
              FVector(ExpectedScale), 1e-6f);
    TestEqual(TEXT("The walker mesh keeps the -90 degree yaw"), Walker->GetMesh()->GetRelativeRotation(),
              FRotator(0, -90, 0), 1e-6f);

    // The seated pilot, against the numbers measured for whichever hero is in the seat rather than
    // against the hero the seat used to hold. Each mount is written out again here for the same reason
    // the walker's sole is: it is a measurement, it cannot be derived from anything else in the build,
    // and inheriting one instead of measuring it is what left a hero 44.067 cm above the cushion.
    FVector ExpectedMount = FVector::ZeroVector;
    FString ExpectedPilotMesh, ExpectedPilotClip;
    float ExpectedPilotScale = 0.f;
    if (PilotHero.Identity == ESSHeroIdentity::Acornaut)
    {
        ExpectedMount = FVector(-15, 0, 72);
        ExpectedPilotMesh = FString(AcornautMesh);
        ExpectedPilotClip = FString(AcornautPilot);
        ExpectedPilotScale = 1.5f;
    }
    else if (PilotHero.Identity == ESSHeroIdentity::Squirrel)
    {
        ExpectedMount = SquirrelMount;
        ExpectedPilotMesh = FString(SquirrelMesh);
        ExpectedPilotClip = FString(SquirrelPilot);
        ExpectedPilotScale = 1.5f;
    }
    // The stand-in has never been seated, so reaching this is either a new hero nobody measured a seat
    // for or the seat having stopped asking the roster at all.
    else if (!TestTrue(TEXT("A hero this test has no seat numbers for is wearing the pilot slot"), false))
        return false;
    AddInfo(FString::Printf(TEXT("HERO_SEAT pilot=%s mount=%s expectedMount=%s declared=%s"), *PilotHero.Id.ToString(),
                            *Ship->Pilot->GetRelativeLocation().ToString(), *ExpectedMount.ToString(),
                            *PilotHero.PilotMountOffset.ToString()));
    TestEqual(TEXT("The pilot wears the seated hero's own mesh"), PilotMesh->GetPathName(), ExpectedPilotMesh);
    TestEqual(TEXT("The seated hero declares the mount measured for it"), PilotHero.PilotMountOffset, ExpectedMount,
              0.f);
    TestEqual(TEXT("The seat applies that mount verbatim, which is all the ship does with it"),
              Ship->Pilot->GetRelativeLocation(), ExpectedMount, 0.f);
    TestEqual(TEXT("The pilot keeps the old yaw"), Ship->Pilot->GetRelativeRotation(), FRotator(0, -90, 0), 1e-6f);
    TestEqual(TEXT("The pilot sits at this hero's own scale"), Ship->Pilot->GetRelativeScale3D(),
              FVector(ExpectedPilotScale), 0.f);
    auto *Seated = Ship->Pilot->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("The pilot plays a clip"), Seated))
        return false;
    TestEqual(TEXT("The pilot plays the seated hero's own authored pilot clip"),
              Seated->GetCurrentAsset() ? Seated->GetCurrentAsset()->GetPathName() : FString(), ExpectedPilotClip);
    TestTrue(TEXT("The pilot clip still loops"), Seated->IsLooping());

    // The walk clip, frozen at the pose the exit clip ends on.
    auto *Walk = Walker->GetMesh()->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("The walker plays a clip"), Walk))
        return false;
    TestEqual(TEXT("The walker plays this hero's own walk clip"),
              Walk->GetCurrentAsset() ? Walk->GetCurrentAsset()->GetPathName() : FString(), Hero.WalkClipPath);
    TestTrue(TEXT("The walk clip still loops"), Walk->IsLooping());
    AddInfo(FString::Printf(TEXT("HERO_WALK_FREEZE seconds=%.9f rate=%.9f"), Walk->GetCurrentTime(),
                            Walker->GetMesh()->GlobalAnimRateScale));
    TestEqual(TEXT("The walk clip is frozen at the same handoff second as before"), Walk->GetCurrentTime(), .308333333f,
              1e-6f);
    TestEqual(TEXT("The hero's handoff second is that same number"), Hero.WalkHandoffSeconds, .308333333f, 0.f);
    TestEqual(TEXT("A standing hero's stride does not advance"), Walker->GetMesh()->GlobalAnimRateScale, 0.f, 0.f);
    TestEqual(TEXT("The stride still plays at its authored rate at 180 cm/s"), Hero.WalkSpeed, 180.f, 0.f);

    // Bone names. The old code spelled them out, and when a rig did not have the name it measured the
    // component instead and filed it as a wrist. Two claims replace that, and neither is vacuous.
    // First: every name a hero declares has to be a name the mesh it is actually wearing has - that is
    // the check the literals could not make, and it fails loudly on a wrong map. Second: where the
    // hero's own spelling IS the spelling the code used to use, the measurement is bit-for-bit the one
    // it used to take; and where it is not, the old spelling has to be genuinely absent from this rig,
    // which is what makes the rename necessary rather than someone's preference. Comparing a renamed
    // bone against the old literal would only assert that the rename had not happened.
    auto Measures = [this](const USkeletalMeshComponent *Mesh, FName Bone, const TCHAR *Literal, const TCHAR *What)
    {
        FTransform Resolved;
        const bool Found = FSSHeroDefinition::ResolveBone(Mesh, Bone, Resolved);
        AddInfo(FString::Printf(TEXT("HERO_BONE what=%s named=%s literal=%s resolved=%d location=%s"), What,
                                *Bone.ToString(), Literal, Found ? 1 : 0, *Resolved.GetLocation().ToString()));
        if (!TestTrue(FString::Printf(TEXT("%s names a bone the mesh this hero is wearing actually has"), What), Found))
            return;
        if (Bone == Literal)
            TestEqual(FString::Printf(TEXT("%s reads exactly what the hard-coded name read"), What), Resolved,
                      Mesh->GetSocketTransform(Literal), 0.f);
        else
            TestFalse(FString::Printf(TEXT("%s is renamed because this rig has no '%s' to read at all"), What, Literal),
                      Mesh->DoesSocketExist(Literal));
    };
    Measures(Ship->Pilot, PilotHero.PelvisBone, TEXT("Pelvis"), TEXT("seated pelvis"));
    Measures(Ship->Pilot, PilotHero.LeftHandBone, TEXT("L_Wrist"), TEXT("seated left wrist"));
    Measures(Ship->Pilot, PilotHero.RightHandBone, TEXT("R_Wrist"), TEXT("seated right wrist"));
    Measures(Walker->GetMesh(), Hero.PelvisBone, TEXT("Pelvis"), TEXT("walking pelvis"));
    Measures(Walker->GetMesh(), Hero.LeftFootBone, TEXT("L_Foot"), TEXT("walking left foot"));
    Measures(Walker->GetMesh(), Hero.RightFootBone, TEXT("R_Foot"), TEXT("walking right foot"));
    Measures(Walker->GetMesh(), Hero.LeftHandBone, TEXT("L_Wrist"), TEXT("walking left wrist"));
    Measures(Walker->GetMesh(), Hero.RightHandBone, TEXT("R_Wrist"), TEXT("walking right wrist"));

    // A name this hero does not have comes back refused, rather than as the component wearing a
    // bone's name. The value is still there for a caller that records anyway; the answer is not.
    FTransform Missing;
    TestFalse(TEXT("An unknown bone name is refused"),
              FSSHeroDefinition::ResolveBone(Walker->GetMesh(), TEXT("SSNoSuchBone"), Missing));
    TestEqual(TEXT("A refused bone still hands back the component transform the old code recorded in silence"), Missing,
              Walker->GetMesh()->GetComponentTransform(), 0.f);
    TestFalse(TEXT("A hero with no name for a bone is refused too"),
              FSSHeroDefinition::ResolveBone(Walker->GetMesh(), NAME_None, Missing));
    TestFalse(TEXT("A bone on no component at all is refused"),
              FSSHeroDefinition::ResolveBone(nullptr, TEXT("Pelvis"), Missing));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHeroPoseRefusal, "SpaceSurvival.Integration.HeroPoseRefusal",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSHeroPoseRefusal::RunTest(const FString &)
{
    // Every refusal has to be nameable, or the walker cannot say what happened to a pilot's pose.
    const ESSPoseRefusal All[] = {
        ESSPoseRefusal::Accepted,
        ESSPoseRefusal::NoMesh,
        ESSPoseRefusal::InvalidSnapshot,
        ESSPoseRefusal::DifferentMesh,
        ESSPoseRefusal::BoneCountMismatch,
        ESSPoseRefusal::BoneNameMismatch,
        ESSPoseRefusal::MalformedTransform,
        // The walker's own three. SetSourcePose never returns these, because in these cases it is
        // never called; they still have to read as sentences, because they are what the log prints.
        ESSPoseRefusal::NotSharedRig,
        ESSPoseRefusal::NoSnapshot,
        ESSPoseRefusal::NoTransitionInstance,
    };
    TSet<FString> Reasons;
    for (ESSPoseRefusal Refusal : All)
    {
        const FString Reason = USSStationPoseTransition::RefusalReason(Refusal);
        TestTrue(TEXT("Every refusal has a reason a person can read"), !Reason.IsEmpty());
        TestFalse(TEXT("No two refusals read the same"), Reasons.Contains(Reason));
        Reasons.Add(Reason);
    }

    FSSHeroTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated refusal world"), Fixture.World))
        return false;
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Spawn the actual walking pawn"), Walker))
        return false;
    // BeginPlay leaves the hero standing in its frozen walk pose, already refreshed. Take the snapshot
    // from that, before the transition instance replaces the single-node one it was posed by.
    Walker->DispatchBeginPlay();
    FPoseSnapshot Own;
    Walker->GetMesh()->SnapshotPose(Own);
    if (!TestTrue(TEXT("Snapshot the walker's own live pose"), Own.bIsValid && Own.LocalTransforms.Num() > 0))
        return false;
    Walker->GetMesh()->SetAnimInstanceClass(USSStationPoseTransition::StaticClass());
    auto *Transition = Cast<USSStationPoseTransition>(Walker->GetMesh()->GetAnimInstance());
    if (!TestNotNull(TEXT("The walker's mesh takes the transition instance"), Transition))
        return false;
    auto Refuse = [this, Transition](const FPoseSnapshot &Pose, ESSPoseRefusal Expected, const TCHAR *What)
    {
        ESSPoseRefusal Refusal = ESSPoseRefusal::Accepted;
        const bool Accepted = Transition->SetSourcePose(Pose, &Refusal);
        TestTrue(FString::Printf(TEXT("%s is accepted only when it should be"), What),
                 Accepted == (Expected == ESSPoseRefusal::Accepted));
        TestEqual(FString::Printf(TEXT("%s reports the refusal it actually hit"), What), static_cast<int32>(Refusal),
                  static_cast<int32>(Expected));
        AddInfo(FString::Printf(TEXT("POSE_REFUSAL what=%s reason=%s"), What,
                                USSStationPoseTransition::RefusalReason(Refusal)));
    };
    Refuse(Own, ESSPoseRefusal::Accepted, TEXT("The walker's own pose"));
    FPoseSnapshot Invalid = Own;
    Invalid.bIsValid = false;
    Refuse(Invalid, ESSPoseRefusal::InvalidSnapshot, TEXT("A snapshot that never took"));
    FPoseSnapshot OtherMesh = Own;
    OtherMesh.SkeletalMeshName = TEXT("SSUnrelatedMesh");
    Refuse(OtherMesh, ESSPoseRefusal::DifferentMesh, TEXT("A pose from another mesh"));
    FPoseSnapshot ShortPose = Own;
    ShortPose.LocalTransforms.Pop();
    ShortPose.BoneNames.Pop();
    Refuse(ShortPose, ESSPoseRefusal::BoneCountMismatch, TEXT("A pose with a bone missing"));
    FPoseSnapshot RenamedBone = Own;
    RenamedBone.BoneNames[0] = TEXT("SSUnrelatedBone");
    Refuse(RenamedBone, ESSPoseRefusal::BoneNameMismatch, TEXT("A pose whose bones are in another order"));
    FPoseSnapshot Malformed = Own;
    Malformed.LocalTransforms[0].SetRotation(FQuat(0, 0, 0, 0));
    Refuse(Malformed, ESSPoseRefusal::MalformedTransform, TEXT("A pose carrying an unusable rotation"));
    // The reason is an extra, not a replacement: the caller that does not ask still gets the answer.
    TestTrue(TEXT("An acceptable pose is still accepted when no reason is asked for"), Transition->SetSourcePose(Own));
    TestFalse(TEXT("A refused pose is still refused when no reason is asked for"),
              Transition->SetSourcePose(OtherMesh));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSSharedRigDisembark, "SpaceSurvival.Integration.SharedRigDisembark",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSSharedRigDisembark::RunTest(const FString &)
{
    // The shared-rig exit is where the pose handoff, the hero-named bones and the data-driven handoff
    // second all live, and while the stand-in is installed nothing reaches it: the walker wears the
    // trooper, the seat keeps the shipped hero, and every disembark takes the other branch. Waiting for
    // the stand-in to be uninstalled would leave that path uncovered for as long as it is here, so the
    // roster is narrowed instead - the other two heroes are given paths that are not on disk, which is
    // precisely what this build looks like the day the licensed body is removed.
    FSSHeroTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated shared-rig world"), Fixture.World))
        return false;
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    auto *Ship = Fixture.World->SpawnActor<ASSShip>();
    if (!TestNotNull(TEXT("Spawn the actual walking pawn"), Walker) ||
        !TestNotNull(TEXT("Spawn the actual ship"), Ship))
        return false;
    auto *Roster = NewObject<USSPhase1Data>(Walker);
    if (!TestNotNull(TEXT("Construct a narrowed roster"), Roster))
        return false;
    for (auto &Entry : Roster->Heroes)
        if (Entry.Identity != ESSHeroIdentity::Acornaut)
        {
            Entry.MeshPath = TEXT("/Game/SpaceSurvival/Character/SK_NoSuchHero.SK_NoSuchHero");
            Entry.WalkClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchWalk.A_NoSuchWalk");
            Entry.PilotClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchPilot.A_NoSuchPilot");
        }
    Walker->Tuning = Roster;
    Ship->Tuning = Roster;
    Walker->DispatchBeginPlay();
    Ship->DispatchBeginPlay();
    const FSSHeroDefinition Hero = Walker->GetHero();
    if (!TestEqual(TEXT("The narrowed roster puts the shipped hero on the deck"), AsInt(Hero.Identity),
                   AsInt(ESSHeroIdentity::Acornaut)) ||
        !TestEqual(TEXT("The narrowed roster keeps the shipped hero in the seat"), AsInt(Ship->GetPilotHero().Identity),
                   AsInt(ESSHeroIdentity::Acornaut)))
        return false;
    TestTrue(TEXT("Both slots resolved one mesh, which is what sharing a rig means"),
             Walker->GetMesh()->GetSkeletalMeshAsset() != nullptr &&
                 Walker->GetMesh()->GetSkeletalMeshAsset() == Ship->Pilot->GetSkeletalMeshAsset());

    // A live seated pose at a nonzero phase, taken the way the station takes one.
    auto *Seat = Ship->Pilot->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("The seat plays its pilot clip"), Seat))
        return false;
    Seat->SetPlaying(false);
    Seat->SetPosition(1.137f, false);
    Ship->Pilot->TickAnimation(0.f, false);
    Ship->Pilot->RefreshBoneTransforms();
    FPoseSnapshot SeatedPose;
    Ship->Pilot->SnapshotPose(SeatedPose);
    if (!TestTrue(TEXT("Capture the actual seated pose"), SeatedPose.bIsValid))
        return false;
    const FTransform Seated = Ship->Pilot->GetComponentTransform();
    FTransform SeatedPelvis;
    TestTrue(TEXT("The seated hero has the pelvis bone its definition names"),
             FSSHeroDefinition::ResolveBone(Ship->Pilot, Ship->GetPilotHero().PelvisBone, SeatedPelvis));
    if (!TestTrue(TEXT("Begin the shared-rig exit"),
                  Walker->BeginDisembark(Seated, Seated.GetLocation() + FVector(650, -350, 0), FRotator(0, 75, 0),
                                         &SeatedPose)))
        return false;

    // The branch nothing reached: the pose was accepted, so the transition instance is what evaluates
    // the exit, and the hero rises out of the seat it was actually sitting in.
    TestNotNull(TEXT("A shared rig consumes the pilot pose through the transition instance"),
                Cast<USSStationPoseTransition>(Walker->GetMesh()->GetAnimInstance()));
    TestTrue(TEXT("The exit starts at the exact seated component transform"),
             Walker->GetMesh()->GetComponentTransform().Equals(Seated, .001));
    FTransform ExitPelvis, Foot;
    TestTrue(TEXT("The walking hero has the pelvis bone its definition names"),
             FSSHeroDefinition::ResolveBone(Walker->GetMesh(), Hero.PelvisBone, ExitPelvis));
    TestTrue(TEXT("The exit begins at the pelvis the pilot was holding, found by the hero's own name"),
             ExitPelvis.GetLocation().Equals(SeatedPelvis.GetLocation(), .1));
    // Foot, not ankle: this hero's L_Foot is its toe and its ankle is L_Ankle, which is exactly why the
    // name is asked for rather than assumed. The trooper spells the same joint foot_l and means the ankle.
    TestTrue(TEXT("The walking hero has the left foot bone its definition names"),
             FSSHeroDefinition::ResolveBone(Walker->GetMesh(), Hero.LeftFootBone, Foot));
    TestTrue(TEXT("The walking hero has the right foot bone its definition names"),
             FSSHeroDefinition::ResolveBone(Walker->GetMesh(), Hero.RightFootBone, Foot));
    AddInfo(FString::Printf(TEXT("SHARED_RIG hero=%s seatedPelvis=%s exitPelvis=%s"), *Hero.Id.ToString(),
                            *SeatedPelvis.GetLocation().ToString(), *ExitPelvis.GetLocation().ToString()));

    // Run the authored clock out and land back in the frozen walk pose, at this hero's own second.
    Walker->Tick(.4f);
    Walker->Tick(2.1f);
    TestFalse(TEXT("The shared-rig exit completes"), Walker->IsDisembarking());
    auto *Walk = Walker->GetMesh()->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("The walk clip resumes"), Walk))
        return false;
    TestEqual(TEXT("It hands back to this hero's own walk clip"),
              Walk->GetCurrentAsset() ? Walk->GetCurrentAsset()->GetPathName() : FString(), Hero.WalkClipPath);
    TestEqual(TEXT("Frozen at the handoff second the hero declares, not at a literal"), Walk->GetCurrentTime(),
              Hero.WalkHandoffSeconds, 1e-6f);
    TestEqual(TEXT("And that second is still the measured one"), Hero.WalkHandoffSeconds, .308333333f, 0.f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHeroReadabilityLight, "SpaceSurvival.Integration.HeroReadabilityLight",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSHeroReadabilityLight::RunTest(const FString &)
{
    FSSHeroTestWorld Fixture;
    if (!TestNotNull(TEXT("Create isolated hero world"), Fixture.World))
        return false;
    auto *Walker = Fixture.World->SpawnActor<ASSWalker>();
    if (!TestNotNull(TEXT("Spawn the actual walking pawn"), Walker))
        return false;
    if (!TestNotNull(TEXT("The pawn carries a key light"), Walker->KeyLight.Get()) ||
        !TestNotNull(TEXT("The pawn carries a rim light"), Walker->RimLight.Get()))
        return false;

    // The two things that keep the rig off the floor, and the reason it is allowed to be as strong as
    // it is. The lighting channel is the first: the lights and the hero's mesh share one, and no other
    // primitive on the pawn or in the station is on it, so the deferred direct pass and Lumen both skip
    // the deck. The channel does not cover volumetric fog, which injects local lights on scattering
    // intensity alone, so the second is that both lamps scatter nothing. Losing either would put a pool
    // of light on the floor around the character and the fix would be the torch it was meant not to be.
    for (const UPointLightComponent *Light : {Walker->KeyLight.Get(), Walker->RimLight.Get()})
    {
        TestFalse(TEXT("A readability light is off the channel the world is lit on"),
                  Light->LightingChannels.bChannel0);
        TestTrue(TEXT("A readability light is on the hero's own channel"), Light->LightingChannels.bChannel1);
        TestEqual(TEXT("A readability light puts nothing into the bay's air, which the channel would not stop"),
                  Light->VolumetricScatteringIntensity, 0.f, 0.f);
        TestFalse(TEXT("A readability light casts no shadow, so it costs no shadow map"), Light->CastShadows);
        TestTrue(TEXT("A readability light is bounded, so it costs a known area"),
                 Light->AttenuationRadius > 0.f && Light->AttenuationRadius <= 600.f);
        TestEqual(TEXT("A readability light is dialled in lumens, not in the engine's unitless default"),
                  static_cast<int32>(Light->IntensityUnits), static_cast<int32>(ELightUnits::Lumens));
    }
    // Built at what the dials say, so a pawn that is registered but never ticked - the editor viewport,
    // or any future path that skips BeginPlay - is not burning the engine's 5000 lumen class default.
    TestEqual(TEXT("The key is built at the key dial's own default"), Walker->KeyLight->Intensity,
              IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HeroLightKey"))->GetFloat(), 1e-3f);
    TestEqual(TEXT("The rim is built at the rim dial's own default"), Walker->RimLight->Intensity,
              IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HeroLightRim"))->GetFloat(), 1e-3f);
    TestTrue(TEXT("The hero keeps the world's lighting"), Walker->GetMesh()->LightingChannels.bChannel0);
    TestTrue(TEXT("The hero also receives the rig"), Walker->GetMesh()->LightingChannels.bChannel1);
    TestFalse(TEXT("The pawn's collision capsule is not on the rig's channel"),
              Walker->GetCapsuleComponent()->LightingChannels.bChannel1);

    // Key toward the camera, rim away from it, on opposite sides and both above the capsule centre.
    // This is the shape of a lit subject rather than a lamp on the lens: the exact centimetres are feel
    // and may move, but a key that crossed to the far side would stop lighting what the camera sees,
    // and a rim on the key's side would stop drawing the edge that the complaint was about.
    const FVector Key = Walker->KeyLight->GetRelativeLocation();
    const FVector Rim = Walker->RimLight->GetRelativeLocation();
    TestTrue(TEXT("The key is on the camera's side of the hero"), Key.X < 0.);
    TestTrue(TEXT("The rim is on the far side of the hero"), Rim.X > 0.);
    TestTrue(TEXT("They are on opposite sides of the view axis"), Key.Y * Rim.Y < 0.);
    TestTrue(TEXT("Both are above the capsule centre"), Key.Z > 0. && Rim.Z > 0.);
    TestTrue(TEXT("The rim is the higher of the two, so it grazes the outline"), Rim.Z > Key.Z);

    Walker->DispatchBeginPlay();
    const FSSHeroDefinition Hero = Walker->GetHero();
    auto *Master = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HeroLightScale"));
    auto *KeyDial = IConsoleManager::Get().FindConsoleVariable(TEXT("ss.HeroLightKey"));
    if (!TestNotNull(TEXT("The master dial exists"), Master) || !TestNotNull(TEXT("The key dial exists"), KeyDial))
        return false;
    const float MasterWas = Master->GetFloat(), KeyWas = KeyDial->GetFloat();
    Walker->Tick(.016f);
    AddInfo(FString::Printf(TEXT("HERO_LIGHT hero=%s scale=%.6f key=%.3f rim=%.3f"), *Hero.Id.ToString(),
                            Hero.ReadabilityLightScale, Walker->KeyLight->Intensity, Walker->RimLight->Intensity));
    // Each hero's measured scale, pinned hard. The product check below reads the same field on both
    // sides, so on its own it would pass at any value at all - and this field is the one number in the
    // rig that answers the owner's complaint, because it is the whole of why the darkest suit gets two
    // and a half times the lamp. Every one of these came off a measurement of that hero's base colour;
    // moving one should mean a new measurement, and should have to say so here.
    TestEqual(TEXT("The darkest hero declares the scale its 0.046 albedo was measured to need"),
              FSSHeroDefinition(ESSHeroIdentity::Squirrel).ReadabilityLightScale, 2.5f, 0.f);
    TestEqual(TEXT("The trooper's glossy plates return five times as much, so it declares a fifth"),
              FSSHeroDefinition(ESSHeroIdentity::Trooper).ReadabilityLightScale, .5f, 0.f);
    TestEqual(TEXT("The pale fallback declares its own, rather than inheriting a lamp sized for a black suit"),
              FSSHeroDefinition(ESSHeroIdentity::Acornaut).ReadabilityLightScale, .5f, 0.f);
    // The dial is the look and the hero's scale is how much of it that hero's albedo needs. Their
    // product is what reaches the lamp, so a hero added later cannot be lit without declaring a scale.
    TestEqual(TEXT("The key burns the dial times this hero's own scale"), Walker->KeyLight->Intensity,
              KeyWas * MasterWas * Hero.ReadabilityLightScale, 1e-3f);
    KeyDial->Set(KeyWas * 2.f, ECVF_SetByCode);
    Walker->Tick(.016f);
    TestEqual(TEXT("Turning the dial mid-session moves the light"), Walker->KeyLight->Intensity,
              KeyWas * 2.f * MasterWas * Hero.ReadabilityLightScale, 1e-3f);
    // Off is off, not black: the owner compares against the station alone by typing ss.HeroLightScale 0,
    // and a light left visible at zero intensity would still cost a pass over its bounds.
    Master->Set(0.f, ECVF_SetByCode);
    Walker->Tick(.016f);
    TestFalse(TEXT("The master dial at zero switches the key off"), Walker->KeyLight->IsVisible());
    TestFalse(TEXT("The master dial at zero switches the rim off"), Walker->RimLight->IsVisible());
    Master->Set(MasterWas, ECVF_SetByCode);
    KeyDial->Set(KeyWas, ECVF_SetByCode);
    Walker->Tick(.016f);
    TestTrue(TEXT("And restoring it brings them back"), Walker->KeyLight->IsVisible() && Walker->RimLight->IsVisible());
    return true;
}
#endif
