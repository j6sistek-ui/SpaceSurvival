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
#include "Components/SkeletalMeshComponent.h"
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
    TestEqual(TEXT("The stand-in is asked about first"), AsInt(Content->Heroes[0].Identity),
              AsInt(ESSHeroIdentity::Trooper));
    TestEqual(TEXT("The shipped hero is second"), AsInt(Content->Heroes[1].Identity), AsInt(ESSHeroIdentity::Acornaut));
    TestEqual(TEXT("The hero that is coming is last"), AsInt(Content->Heroes[2].Identity),
              AsInt(ESSHeroIdentity::Squirrel));
    TestEqual(TEXT("The pawns are built with the shipped hero"), AsInt(FSSHeroDefinition::Fallback().Identity),
              AsInt(ESSHeroIdentity::Acornaut));

    const FSSHeroDefinition Trooper = Content->Heroes[0];
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

    const FSSHeroDefinition Acornaut = Content->Heroes[1];
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

    const FSSHeroDefinition Squirrel = Content->Heroes[2];
    TestEqual(TEXT("Squirrel stands on its own origin"), Squirrel.SoleOffset, 0.f, 0.f);
    TestEqual(TEXT("Squirrel scale"), Squirrel.MeshScale, 1.5f, 0.f);
    TestEqual(TEXT("Squirrel is scaled, not fitted"), Squirrel.FitHeight, 0.f, 0.f);
    TestTrue(TEXT("Squirrel bone names are its own, measured in Unreal from the imported base"),
             Squirrel.RootBone == TEXT("Root") && Squirrel.PelvisBone == TEXT("Pelvis") &&
                 Squirrel.LeftFootBone == TEXT("L_Foot") && Squirrel.RightFootBone == TEXT("R_Foot") &&
                 Squirrel.LeftHandBone == TEXT("L_Hand") && Squirrel.RightHandBone == TEXT("R_Hand"));
    TestFalse(TEXT("The squirrel's assets do not exist, so it cannot walk"), Squirrel.Installed(ESSHeroSlot::Walker));
    TestFalse(TEXT("The squirrel's assets do not exist, so it cannot fly"), Squirrel.Installed(ESSHeroSlot::Pilot));
    TestNotEqual(TEXT("An uninstalled hero is skipped, never selected, for the walker"),
                 AsInt(Content->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(ESSHeroIdentity::Squirrel));
    TestNotEqual(TEXT("An uninstalled hero is skipped, never selected, for the pilot"),
                 AsInt(Content->SelectHero(ESSHeroSlot::Pilot).Identity), AsInt(ESSHeroIdentity::Squirrel));
    TestEqual(TEXT("The pilot slot goes to the shipped hero, because the stand-in has no pilot clip"),
              AsInt(Content->SelectHero(ESSHeroSlot::Pilot).Identity), AsInt(ESSHeroIdentity::Acornaut));
    for (const auto &Entry : Content->Heroes)
        AddInfo(FString::Printf(TEXT("HERO_ROSTER id=%s walker=%d pilot=%d mesh=%s"), *Entry.Id.ToString(),
                                Entry.Installed(ESSHeroSlot::Walker) ? 1 : 0,
                                Entry.Installed(ESSHeroSlot::Pilot) ? 1 : 0, *Entry.MeshPath));

    // A roster whose assets are all absent still answers, with the hero the pawns were built with.
    auto *Absent = NewObject<USSPhase1Data>();
    if (!TestNotNull(TEXT("Construct a second content object"), Absent))
        return false;
    for (auto &Entry : Absent->Heroes)
    {
        Entry.MeshPath = TEXT("/Game/SpaceSurvival/Character/SK_NoSuchHero.SK_NoSuchHero");
        Entry.WalkClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchWalk.A_NoSuchWalk");
        Entry.PilotClipPath = TEXT("/Game/SpaceSurvival/Character/A_NoSuchPilot.A_NoSuchPilot");
        TestFalse(TEXT("A hero with no assets on disk is not installed"), Entry.Installed(ESSHeroSlot::Walker));
    }
    TestEqual(TEXT("With nothing installed, selection lands on the hero the pawns were built with"),
              AsInt(Absent->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(FSSHeroDefinition::Fallback().Identity));
    // Presence decides, not position: an installed hero behind two missing ones still wins the slot.
    Absent->Heroes[2].MeshPath = Acornaut.MeshPath;
    Absent->Heroes[2].WalkClipPath = Acornaut.WalkClipPath;
    TestEqual(TEXT("Selection walks past the missing heroes to the installed one behind them"),
              AsInt(Absent->SelectHero(ESSHeroSlot::Walker).Identity), AsInt(ESSHeroIdentity::Squirrel));

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
            AddInfo(FString::Printf(TEXT("HERO_FIT id=%s scale=%.9f scaledSole=%.9f"), *Entry.Id.ToString(),
                                    Entry.RenderedScale(Mesh), Entry.ScaledSoleOffset(Mesh)));
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

    // The seated pilot: an unchanged mount, an unchanged mesh, an unchanged clip.
    TestEqual(TEXT("The ship is still flown by the shipped hero"), AsInt(PilotHero.Identity),
              AsInt(ESSHeroIdentity::Acornaut));
    TestEqual(TEXT("The pilot wears the shipped hero's mesh"), PilotMesh->GetPathName(), FString(AcornautMesh));
    TestEqual(TEXT("The pilot sits at the old mount offset"), Ship->Pilot->GetRelativeLocation(), FVector(-15, 0, 72),
              0.f);
    TestEqual(TEXT("The pilot keeps the old yaw"), Ship->Pilot->GetRelativeRotation(), FRotator(0, -90, 0), 1e-6f);
    TestEqual(TEXT("The pilot keeps the old scale"), Ship->Pilot->GetRelativeScale3D(), FVector(1.5f), 0.f);
    auto *Seated = Ship->Pilot->GetSingleNodeInstance();
    if (!TestNotNull(TEXT("The pilot plays a clip"), Seated))
        return false;
    TestEqual(TEXT("The pilot plays the old authored pilot clip"),
              Seated->GetCurrentAsset() ? Seated->GetCurrentAsset()->GetPathName() : FString(), FString(AcornautPilot));
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
#endif
