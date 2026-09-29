#include "SSContentTypes.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/PackageName.h"

bool FSSHeroDefinition::AssetInstalled(const FString &ObjectPath)
{
    return !ObjectPath.IsEmpty() && FPackageName::DoesPackageExist(FPackageName::ObjectPathToPackageName(ObjectPath));
}

bool FSSHeroDefinition::Installed(ESSHeroSlot Slot) const
{
    return AssetInstalled(MeshPath) && AssetInstalled(Slot == ESSHeroSlot::Pilot ? PilotClipPath : WalkClipPath);
}

FSSHeroDefinition FSSHeroDefinition::ResolvedPresentation() const
{
    FSSHeroDefinition Result = *this;
    if (Identity != ESSHeroIdentity::AlienFemale)
        return Result;
    const FSSHeroDefinition Legacy(ESSHeroIdentity::AlienFemale);
    if (MeshPath != Legacy.MeshPath || WalkClipPath != Legacy.WalkClipPath || IdleClipPath != Legacy.IdleClipPath ||
        RunClipPath != Legacy.RunClipPath)
        return Result;
    const FString Base = TEXT("/Game/SpaceSurvival/Licensed/AlienFemalePresentation/");
    const FString Mesh = Base + TEXT("SK_AlienFemalePresentation.SK_AlienFemalePresentation");
    const FString Walk = Base + TEXT("A_AlienFemaleWalk.A_AlienFemaleWalk");
    const FString Idle = Base + TEXT("A_AlienFemaleIdle.A_AlienFemaleIdle");
    const FString Run = Base + TEXT("A_AlienFemaleRun.A_AlienFemaleRun");
    if (AssetInstalled(Mesh) && AssetInstalled(Walk) && AssetInstalled(Idle) && AssetInstalled(Run))
    {
        Result.MeshPath = Mesh;
        Result.WalkClipPath = Walk;
        Result.IdleClipPath = Idle;
        Result.RunClipPath = Run;
    }
    return Result;
}

float FSSHeroDefinition::RenderedScale(const USkeletalMesh *Mesh) const
{
    if (FitHeight <= 0.f || !Mesh)
        return MeshScale;
    const float Height = Mesh->GetBounds().BoxExtent.Z * 2.f;
    return Height > 1.f ? FitHeight / Height : 1.f;
}

double FSSHeroDefinition::ScaledSoleOffset(const USkeletalMesh *Mesh) const
{
    // A declared offset is a float product, as it always was; a fitted one is measured from bounds
    // that are doubles, and stays one. Both reach the caller at the width its arithmetic used.
    if (FitHeight <= 0.f || !Mesh)
        return SoleOffset * MeshScale;
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    return -(Bounds.Origin.Z - Bounds.BoxExtent.Z) * RenderedScale(Mesh);
}

bool FSSHeroDefinition::ResolveBone(const USkeletalMeshComponent *Mesh, FName Bone, FTransform &Out)
{
    Out = Mesh ? Mesh->GetComponentTransform() : FTransform::Identity;
    if (!Mesh || Bone.IsNone() || !Mesh->DoesSocketExist(Bone))
        return false;
    Out = Mesh->GetSocketTransform(Bone);
    return true;
}

bool FSSHullDefinition::Installed() const
{
    // Classic is always installed: ASSShip::HullAssetPath picks between three meshes the game has always
    // shipped, and which one it picks depends on a command-line flag, so there is no single path to test.
    // Anything else has to actually be present, and the Phoenix lives in a git-ignored licensed folder,
    // so a build without it is the ordinary state rather than a fault.
    return Identity == ESSHullIdentity::Classic || FSSHeroDefinition::AssetInstalled(MeshPath);
}

FSSVillainDefinition::FSSVillainDefinition()
{
    // One line per story beat, a few per chatter cue. Short enough for one caption line, and never a hint about
    // timing: waves stay hidden timers. He owns this belt, the Acornaut is trespassing, and he means to end it.
    using Cue = ESSVillainCue;
    const FSSVillainLine Authored[] = {
        {Cue::RunStart, 0, TEXT("An Acornaut in my belt. Turn back, or I bury you in it.")},
        {Cue::WaveStart, 0, TEXT("Another stretch of dark. Another chance to break you.")},
        {Cue::WaveStart, 2, TEXT("Still flying? I have more stone than you have hull.")},
        {Cue::WaveStart, 3, TEXT("Enough stone. Meet my hunters.")},
        {Cue::WaveStart, 4, TEXT("Every rock you dodge, I throw again. Harder.")},
        {Cue::WaveStart, 5, TEXT("Keep coming. I have opened something just for you.")},
        {Cue::WaveStart, 6, TEXT("Patched and back for more. It changes nothing.")},
        {Cue::WaveStart, 7, TEXT("My hunters have learned your tricks.")},
        {Cue::WaveStart, 8, TEXT("You are costing me ships. Your hull will pay for them.")},
        {Cue::WaveStart, 9, TEXT("One more stretch of dark. I will make it your last.")},
        {Cue::Wormhole, 0, TEXT("Feel that pull? My rift. Come and see where I live.")},
        {Cue::Climax, 0, TEXT("My side of the dark. Hunters, take it apart.")},
        {Cue::Compound, 0, TEXT("Gravity, stone and steel. Everything I have, for you.")},
        {Cue::Retreat, 0, TEXT("Run to your station. Patch your little ship. I will wait.")},
        {Cue::Finale, 0, TEXT("Enjoy your station while its walls hold. This is not over.")},
        {Cue::LowHull, 0, TEXT("Hear that groan? Your hull is begging.")},
        {Cue::LowHull, 0, TEXT("Nearly done. Hold still.")},
        {Cue::Death, 0, TEXT("Scattered across my belt, as I promised.")},
        {Cue::Launch, 0, TEXT("Go. Bring me its wings.")},
        {Cue::Launch, 0, TEXT("Another hunter, just for you.")},
        {Cue::Launch, 0, TEXT("Fetch.")},
        {Cue::Hit, 0, TEXT("Did that sting?")},
        {Cue::Hit, 0, TEXT("I felt that one from here.")},
        {Cue::Hit, 0, TEXT("Your hull is thinner than your nerve.")},
        {Cue::Kill, 0, TEXT("One hunter. I have a fleet.")},
        {Cue::Kill, 0, TEXT("Enjoy that. It will cost you.")},
        {Cue::Kill, 0, TEXT("Cheap. Unlike you.")},
    };
    Lines.Append(Authored, UE_ARRAY_COUNT(Authored));
}

FString FSSVillainDefinition::LineFor(ESSVillainCue Cue, int32 Wave, FRandomStream &Random, const FString &Avoid) const
{
    TArray<const FString *> ThisWave, AnyWave;
    for (const FSSVillainLine &Line : Lines)
        if (Line.Cue == Cue && !Line.Text.IsEmpty())
        {
            if (Line.Wave == Wave)
                ThisWave.Add(&Line.Text);
            else if (Line.Wave == 0)
                AnyWave.Add(&Line.Text);
        }
    const TArray<const FString *> &Pool = ThisWave.IsEmpty() ? AnyWave : ThisWave;
    // Not the line he just said, unless it is all he has for this moment.
    TArray<const FString *> Fresh;
    for (const FString *Text : Pool)
        if (*Text != Avoid)
            Fresh.Add(Text);
    const TArray<const FString *> &Choice = Fresh.IsEmpty() ? Pool : Fresh;
    return Choice.IsEmpty() ? FString() : *Choice[Random.RandRange(0, Choice.Num() - 1)];
}
