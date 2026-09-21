#include "SSShip.h"
#include "SSShipPaint.h"
#include "SSVFXPresentation.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShipPresentation.h"
#include "SSShipVisualRig.h"
#include "SSWorldActors.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Camera/CameraComponent.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Sound/SoundBase.h"
#include "Engine/StaticMesh.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Animation/AnimSequence.h"
#include "GyroManagerComp.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "ThrusterManagerComp.h"

namespace
{
// Speed cues on the player camera rather than on the level's volume, so they follow the player and cannot
// disturb the authored exposure. No settings-menu entry yet: chromatic fringe and vignette both have real
// accessibility implications and belong behind a player toggle, but the settings UI is being reworked and
// this should land there rather than as a console variable left for someone to find.
TAutoConsoleVariable<int32> SpeedPostFX(TEXT("ss.SpeedPostFX"), 1,
                                        TEXT("Chromatic fringe and vignette under thrust (0 disables)."));
} // namespace
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/PackageName.h"

ASSShip::ASSShip()
{
    PrimaryActorTick.bCanEverTick = true;
    Collision = CreateDefaultSubobject<USphereComponent>(TEXT("FlightCollision"));
    Collision->InitSphereRadius(105.f);
    RootComponent = Collision;
    Collision->SetCollisionObjectType(ECC_Pawn);
    Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Collision->SetCollisionResponseToAllChannels(ECR_Ignore);
    Collision->SetCollisionResponseToChannel(ECC_WorldStatic, ECR_Block);
    HullMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AcornHull"));
    HullMesh->SetupAttachment(RootComponent);
    HullMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SkeletalHull = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SkeletalHull"));
    SkeletalHull->SetupAttachment(RootComponent);
    SkeletalHull->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // Empty and hidden by default. A build without a skeletal hull installed never sees this component,
    // and the static HullMesh below is exactly what it has always been.
    SkeletalHull->SetVisibility(false);
    Pilot = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("AcornautPilot"));
    Pilot->SetupAttachment(HullMesh);
    Pilot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // The player is always close to this single shared hero texture.
    Pilot->bForceMipStreaming = true;
    // Seated with the fallback hero, because a constructor cannot ask what content is installed.
    // BeginPlay reapplies these three from whichever hero this build actually seats.
    Pilot->SetRelativeLocation(PilotHero.PilotMountOffset);
    Pilot->SetRelativeRotation(FRotator(0, PilotHero.MeshYaw, 0));
    Pilot->SetRelativeScale3D(FVector(PilotHero.RenderedScale(nullptr)));
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("ChaseBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 900.f;
    CameraBoom->SocketOffset = FVector(0, 0, 125);
    // On, now that the boom can be long. It was off because a 900 cm arm behind a 4.8 m hull never had
    // anything to hit; a hull five times longer needs an arm five times longer, and the first Wave 10
    // capture with one put the camera inside an asteroid with the ship nowhere in frame.
    CameraBoom->bDoCollisionTest = true;
    CameraBoom->ProbeSize = 60.f;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 9.f;
    CameraBoom->CameraLagMaxDistance = 35.f;
    CameraBoom->bUseCameraLagSubstepping = true;
    CameraBoom->CameraLagMaxTimeStep = 1.f / 120.f;
    CameraBoom->bInheritRoll = false;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ChaseCamera"));
    Camera->SetupAttachment(CameraBoom);
    Camera->FieldOfView = 80.f;
    // Frame the entire banked hull below the sightline. The previous upward view
    // clipped the rear hull even without lag at a 16:9 viewport.
    Camera->SetRelativeRotation(FRotator(-4, 0, 0));
    // A restrained chase-side fill keeps the player silhouette readable in deep shadow.
    auto *ReadabilityLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ShipReadabilityFill"));
    ReadabilityLight->SetupAttachment(RootComponent);
    ReadabilityLight->SetRelativeLocation(FVector(-350, -180, 220));
    ReadabilityLight->SetIntensityUnits(ELightUnits::Lumens);
    ReadabilityLight->SetIntensity(1500.f);
    ReadabilityLight->SetAttenuationRadius(900.f);
    ReadabilityLight->SetLightColor(FLinearColor(.7f, .82f, 1.f));
    ReadabilityLight->SetCastShadows(false);
    EngineAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("EngineAudio"));
    EngineAudio->SetAutoActivate(false);
    EngineAudio->SetupAttachment(RootComponent);
    Presentation = CreateDefaultSubobject<USSShipPresentation>(TEXT("PurchasedShipModules"));
    VisualRig = CreateDefaultSubobject<USSShipVisualRig>(TEXT("AuthoredShipRig"));
}
FVector ASSShip::GyroInputFor(FVector2D Steer, float Turn)
{
    // Gyro input is a body-frame torque vector: X turns about forward (roll), Y about right (pitch), Z about
    // up (yaw). That is what the plugin's own ApplyFinalTorque does with it. The plugin's header says
    // (Pitch, Yaw, Roll), and the first version of this believed it, so the pitch stick rolled the Phoenix
    // and the yaw stick pitched it - which the ship's own approach log showed as both commands saturated
    // for a hundred seconds with neither error closing.
    //
    // Axes AND signs come from SpaceSurvival.Flight.ShipCoreGyroAxes, which measured them: +Z torque gives
    // +yaw, but +Y gives -pitch and +X gives -roll. The kinematic path treats +Steer.X as +yaw and
    // +Steer.Y as +pitch, and the stick has to mean the same thing on both hulls, so pitch is negated here
    // and yaw is not. ShipStickToGyro pins this function's output directly.
    const float Yaw = FMath::Clamp(Steer.X, -1.f, 1.f) * Turn;
    const float Pitch = -FMath::Clamp(Steer.Y, -1.f, 1.f) * Turn;
    // A little roll into the turn, because a ship that yaws flat reads as a cursor. Negated for the same
    // reason as pitch, so a right (+yaw) turn produces positive rotator roll. Two things about it are
    // feel checks with hands on the stick, not rules: whether that reads as leaning into the turn, and
    // whether the gyro - which damps rate but holds no attitude - lets a held turn settle into a steady
    // roll rate rather than a lean. Flip the sign or zero the .35 if either reads wrong; it is a dial.
    const float Lean = -FMath::Clamp(Steer.X, -1.f, 1.f) * .35f * Turn;
    return FVector(Lean, Pitch, Yaw);
}
void ASSShip::DriveShipCore(float Dt, double Acceleration, double Maneuver, double Response, float Speed,
                            float Authority, float Interference)
{
    if (!Thrusters || !Gyros || !Collision)
        return;
    const float Mass = FMath::Max(1.f, Collision->GetMass());

    // Thrust from the upgraded stat, so buying Engine tiers still moves the ship. All six axes get the
    // SAME number on purpose: the plugin ships Z stronger than X and Y, 20e6 against 15e6, which would
    // quietly make vertical strafe a third livelier than horizontal for no reason anybody chose.
    const float AxisThrust = float(Acceleration) * Mass;
    Thrusters->SetAllThrustersForce(AxisThrust);

    // Top speed. The limiter defaults OFF, so without this the Engine upgrade's speed half would do
    // nothing at all while still costing credits, and the ship would accelerate without limit.
    Thrusters->SetSpeedLimiterActive(true);
    const float Limit = FMath::Max(Speed, float(Maneuver));
    Thrusters->SetMaxSpeedLimit(Limit, FMath::Max(100.f, Limit * .12f));

    // Turning authority and how hard it stops turning. Response is re-homed onto the gyro's proportional
    // gain rather than dropped: it was a rate constant on linear velocity error and there is no such dial
    // on a rigid body, so it becomes the rate constant on ANGULAR error. That is a re-purposing and not a
    // translation, and the Thrusters upgrade stays observable as crisper turning because of it.
    Gyros->ProportionalGain = FMath::Max(.5, Response);
    const float TurnRate = FMath::DegreesToRadians(Tuning->SteeringDegrees * Authority * Interference);
    Gyros->MaxTotalTorque = FMath::Max(1.f, TurnRate * float(Gyros->ProportionalGain) * 2.f);

    // Inertial dampeners: release the stick and the ship settles instead of coasting forever. This is the
    // single biggest contributor to the feel the owner asked for, and the plugin defaults it on - but
    // SetInertialDampeners dereferences its mesh pointer with no null check while its own _Server twin
    // guards it, and standalone always takes the unguarded path. Only call it once the body is confirmed.
    if (Collision->IsSimulatingPhysics())
        Thrusters->SetInertialDampeners(true);

    // Input. Throttle is a TRIM, not a thrust direction, and getting that wrong is what stopped the Phoenix
    // ever reaching a landing pad. On the hand-written model throttle scales a target speed - Speed above is
    // already max(MinimumSpeed, stat * (1 + .3 * throttle) * boost * brake) - so throttle -1 means "cruise at
    // seventy percent", still travelling forward. Feeding that same -1 in here as an axis meant "full
    // reverse", so the classic hull closed on the pad while the Phoenix backed away from it, and the
    // dampener then braked at the full thrust clamp on top because input and velocity disagreed in sign.
    //
    // So drive the error instead: thrust forward when under the trimmed speed, back when over it. That is
    // what a throttle trim IS on a body that has to be pushed, it gives the same meaning to the same input
    // on both paths, and it is the settle-into-a-cruise behaviour the flight feel is aiming at. The band is
    // a share of the target rather than a constant so it scales with the Engine upgrade instead of going
    // stale, and the floor keeps it sane when the target approaches zero in the station zone.
    const float ForwardSpeed = FVector::DotProduct(Collision->GetPhysicsLinearVelocity(), GetActorForwardVector());
    const float Trim = FMath::Clamp((Speed - ForwardSpeed) / FMath::Max(100.f, Speed * .15f), -1.f, 1.f);
    const FVector Thrust(Trim, FMath::Clamp(StrafeInput.X, -1.f, 1.f), FMath::Clamp(StrafeInput.Y, -1.f, 1.f));
    Thrusters->SetThrustersInput(Thrust);
    // ShipCore accepts angular acceleration, not a turn rate. Convert the same degrees/second used by
    // input into its rate-damped solver. Banking targets an attitude; a held turn must not roll forever.
    const float BankError = FMath::FindDeltaAngleDegrees(GetActorRotation().Roll, Steer.X * 28.f);
    const FVector TargetRate(-FMath::DegreesToRadians(BankError) * 3.f, -Steer.Y * TurnRate, Steer.X * TurnRate);
    Gyros->SetGyrosInput(TargetRate * float(Gyros->ProportionalGain / Gyros->MaxTotalTorque));

    // Gravity wells and the wormhole still push, but their numbers were accelerations integrated by hand.
    // Against a real body they are forces, so they carry the mass with them.
    if (!Forces.IsNearlyZero())
        Collision->AddForce(Forces.GetClampedToMaxSize(4500.f) * Mass);
}
void ASSShip::OnHullImpact(UPrimitiveComponent *, AActor *OtherActor, UPrimitiveComponent *, FVector,
                           const FHitResult &)
{
    // The same 15 damage on the same .8 s cooldown the swept path charged, so the Phoenix is not quietly
    // invulnerable to the asteroid field every other hull has always had to respect.
    if (!ShipCoreDriven || !OtherActor || OtherActor == this || ImpactCooldown > 0)
        return;
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    ReceiveDamage(15.f * float(GI->Session.DamageScale()));
    ImpactCooldown = .8f;
}
FVector ASSShip::GetVelocity() const
{
    // Sixteen production sites read this - Director spawn lead, enemy aim lead, hazard intercept, the
    // collision-course warning, the dust field. Under ShipCore the hand-kept member is never written, so
    // leaving it as the answer would freeze every one of them at the BeginPlay cruise seed while nothing
    // errored and the game just quietly got easier.
    if (ShipCoreDriven && Collision && Collision->IsSimulatingPhysics())
        return Collision->GetPhysicsLinearVelocity();
    return Velocity;
}
float ASSShip::DockApproachRadius() const
{
    // How close counts as "at the pad". 1200 cm is origin-to-origin and was measured against a 482.5 cm
    // hull, whose whole body sits inside that ball. It asks a longer ship to put its centre where its nose
    // already is. Nose reach plus the classic margin, so every ship is judged by where its body is.
    //
    // Nose reach, not half the length. The Phoenix's pivot is 141.16 cm aft of its centre, so its nose is
    // at 1100.84 and its tail at 1383.16 - the halves are not equal and using one for the other is wrong in
    // both directions at once.
    const float NoseReach = SkeletalHull && SkeletalHull->IsVisible()
                                ? FSSHullDefinition(ESSHullIdentity::StellarPhoenix).ScaledOriginToNose()
                                : 0.f;
    return FMath::Max(1200.f, NoseReach + 1200.f);
}
ESSHullIdentity ASSShip::SelectedHullIdentity()
{
    // The Phoenix is the ship. Every rule it used to fail has been read, measured and either rewritten as
    // something true of any hull or moved into the hull's own row, so this is a default rather than a flag
    // that happens to work: the whole suite passes on it.
    //
    // Two ways to fly the classic hull remain, and both matter. -SSClassic asks for it, which is how the
    // two are compared side by side; and Installed() still answers for the licensed pack, so a fresh
    // checkout or a CI machine that does not have it flies the classic hull rather than failing to find a
    // mesh. -SSPhoenix keeps working and now simply asks for what it already gets.
    const FSSHullDefinition Phoenix(ESSHullIdentity::StellarPhoenix);
    return !FParse::Param(FCommandLine::Get(), TEXT("SSClassic")) && Phoenix.Installed()
               ? ESSHullIdentity::StellarPhoenix
               : ESSHullIdentity::Classic;
}
float ASSShip::FlightCollisionRadius()
{
    // Read from the class default object, so it tracks the constructor and any hull swap that changes it
    // instead of needing five other files edited in step. Unscaled deliberately: nothing scales the flight
    // pawn today, and a scaled answer here would silently differ from the constructor's authored number.
    const auto *Default = GetDefault<ASSShip>();
    return Default && Default->Collision ? Default->Collision->GetUnscaledSphereRadius() : 105.f;
}
const TCHAR *ASSShip::HullAssetPath(SS::Ship Kind)
{
    if (Kind == SS::Ship::Starter && FParse::Param(FCommandLine::Get(), TEXT("SSShipRefresh")) &&
        FPackageName::DoesPackageExist(TEXT("/Game/SpaceSurvival/ShipRefresh/SM_LudoStarter")))
        return TEXT("/Game/SpaceSurvival/ShipRefresh/SM_LudoStarter.SM_LudoStarter");
    if (Kind == SS::Ship::Starter &&
        FPackageName::DoesPackageExist(
            TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/SM_PlayerHavolkStarter")))
        return TEXT(
            "/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/Meshes/SM_PlayerHavolkStarter.SM_PlayerHavolkStarter");
    return Kind == SS::Ship::Agile ? TEXT("/Game/SpaceSurvival/Meshes/SM_SwiftCandidateV1.SM_SwiftCandidateV1")
                                   : TEXT("/Game/SpaceSurvival/Meshes/SM_AcornShipGripFit.SM_AcornShipGripFit");
}
void ASSShip::UpdateEngineMix()
{
    const auto *GI = GetGameInstance<USSGameInstance>();
    EngineAudio->SetVolumeMultiplier(SSAudio::EffectsGain(this, .35f));
    EngineAudio->SetPitchMultiplier(GI && GI->Session.run.boosting ? 1.3f : .9f + .15f * ThrottleInput);
}
void ASSShip::RefreshPaint()
{
    if (const auto *GI = GetGameInstance<USSGameInstance>();
        GI && HullMesh && HullMesh->IsVisible() && (!SkeletalHull || !SkeletalHull->GetSkeletalMeshAsset()))
        SSPaint::Apply(HullMesh, GI->Session.account);
}
void ASSShip::BeginPlay()
{
    Super::BeginPlay();
    if (!Tuning)
        Tuning = LoadObject<USSPhase1Data>(nullptr, TEXT("/Game/SpaceSurvival/Data/DA_Phase1.DA_Phase1"));
    if (!Tuning)
        Tuning = NewObject<USSPhase1Data>(this);
    auto *GI = GetGameInstance<USSGameInstance>();
    HullMesh->SetStaticMesh(
        LoadObject<UStaticMesh>(nullptr, HullAssetPath(GI ? GI->Session.run.ship : SS::Ship::Starter)));
    Presentation->SetHull(HullMesh);
    PilotHero = Tuning->SelectHero(ESSHeroSlot::Pilot);
    auto *PilotMesh = LoadObject<USkeletalMesh>(nullptr, *PilotHero.MeshPath);
    auto *PilotClip =
        PilotHero.PilotClipPath.IsEmpty() ? nullptr : LoadObject<UAnimSequence>(nullptr, *PilotHero.PilotClipPath);
    const FSSHeroDefinition Shipped = Tuning->FallbackHero();
    // The same guard the walker keeps, for the same reason: a clip can only play on the skeleton it was
    // authored against. An installed hero whose assets fail to load, or whose pilot clip belongs to
    // another rig, gives the seat back to the shipped hero instead of evaluating somebody else's body.
    if (PilotHero.Identity != Shipped.Identity &&
        (!PilotMesh || !PilotClip || PilotMesh->GetSkeleton() != PilotClip->GetSkeleton()))
    {
        UE_LOG(LogTemp, Warning,
               TEXT("SSPilot: hero '%s' cannot take the seat and is demoted to '%s'. mesh=%s clip=%s"),
               *PilotHero.Id.ToString(), *Shipped.Id.ToString(), *PilotHero.MeshPath, *PilotHero.PilotClipPath);
        PilotHero = Shipped;
        PilotMesh = LoadObject<USkeletalMesh>(nullptr, *PilotHero.MeshPath);
        PilotClip =
            PilotHero.PilotClipPath.IsEmpty() ? nullptr : LoadObject<UAnimSequence>(nullptr, *PilotHero.PilotClipPath);
    }
    Pilot->SetSkeletalMesh(PilotMesh);
    Pilot->SetRelativeLocation(PilotHero.PilotMountOffset);
    Pilot->SetRelativeRotation(FRotator(0, PilotHero.MeshYaw, 0));
    Pilot->SetRelativeScale3D(FVector(PilotHero.RenderedScale(PilotMesh)));
    const auto *LoadedHull = HullMesh->GetStaticMesh().Get();
    const bool ClosedCockpit =
        LoadedHull &&
        (LoadedHull->GetPathName().StartsWith(TEXT("/Game/SpaceSurvival/ShipRefresh/")) ||
         LoadedHull->GetPathName().StartsWith(TEXT("/Game/SpaceSurvival/Licensed/PlayerShipVisualPass/")));
    // Preserve the animated component and its exit-pose handoff under the closed hull.
    Pilot->SetVisibility(!ClosedCockpit);
    Pilot->PlayAnimation(PilotClip, true);
    // A skeletal hull, if this build has one. The static hull stays loaded and simply stops being drawn:
    // the module presentation and the chase-framing test still read it, and neither has to
    // learn about a second kind of hull before the flight model itself moves.
    // Which hull that is comes from SelectedHullIdentity and nowhere else. An early version switched hulls
    // wherever the pack happened to be installed and did it inline, which hid the static hull that
    // USSShipPresentation hangs the exhausts, muzzle flashes and fitted upgrade modules off - so the
    // presentation suite went red on the one machine that owns the pack. The presentation now asks the hull
    // whether it wears those modules, and the choice is made in one place that every test can also ask.
    if (const FSSHullDefinition Hull(ESSHullIdentity::StellarPhoenix);
        SelectedHullIdentity() == ESSHullIdentity::StellarPhoenix)
    {
        const bool HasRig = VisualRig->Initialize(this, Hull);
        if (HasRig)
        {
            SkeletalHull->SetVisibility(false);
            SkeletalHull = VisualRig->GetHull();
        }
        else if (auto *Mesh = LoadObject<USkeletalMesh>(nullptr, *Hull.MeshPath))
        {
            // A missing Blueprint is a visible fallback, never a second physics/input implementation.
            SkeletalHull->SetSkeletalMesh(Mesh);
            SkeletalHull->SetRelativeRotation(FRotator(0, Hull.MeshYaw, 0));
            SkeletalHull->SetRelativeScale3D(FVector(Hull.HullScale));
            SkeletalHull->SetVisibility(true);
            if (auto *Clip = LoadObject<UAnimSequence>(nullptr, *Hull.FlightPoseClipPath))
                SkeletalHull->PlayAnimation(Clip, false);
            UE_LOG(LogTemp, Warning, TEXT("SSHull: Phoenix Blueprint rig unavailable; mesh fallback active."));
        }
        if (SkeletalHull && SkeletalHull->GetSkeletalMeshAsset())
        {
            HullMesh->SetVisibility(false);
            Pilot->SetVisibility(false);
            // These are the pack's own camera numbers, read out of BP_Spaceship rather than searched for.
            // The pack ships a playable demo level, so the framing its author intended was on disk the
            // whole time: a 3000 arm, the eye 250 above the ship, and a shallow tilt - the spring arm
            // pitched -18 with the camera pitched +5 back, about -13 net.
            //
            // What was here before was found by flying it and looking, and it was a long way out: a 4050
            // arm with the eye 3000 up and a -27 tilt, which is eight times the height at twice the angle.
            // That is why the ship sat small and distant in every capture, and it is the direct cause of
            // the crosshair drift in #47 - a ray pointing 27 degrees down while the ship travels level
            // cannot hold a fixed point, and at -13 it very nearly can.
            // High eye, shallow tilt: the ship settles into the lower third where its top is visible, and
            // the centre stays clear sky.
            HullChaseScale = Hull.ChaseScale;
            // Start the boom where this hull needs it, rather than letting it crawl out there. Tick
            // interpolates TargetArmLength toward ChaseDistance * HullChaseScale at rate 3, so a hull that
            // wants 4050 cm spends its first second climbing out of the constructor's 900 - which for a
            // 24.84 m ship means the camera opens the run inside the hull. ChaseFraming caught it on frame
            // zero at a depth of 698 cm; a player would have caught it by looking.
            CameraBoom->TargetArmLength *= Hull.ChaseScale;
            // Lift and tilt the view. Dead astern is this hull's worst angle: from directly behind, a
            // 24.84 m ship is a slab and its swept wings are edge-on and invisible. Looking slightly down
            // on it shows the planform, which is where the wings actually read.
            CameraBoom->SetRelativeLocation(FVector(0, 0, Hull.ChaseBoomZ));
            CameraBoom->TargetOffset = FVector(0, 0, Hull.ChaseHeight);
            CameraBoom->SocketOffset = FVector::ZeroVector;
            CameraBoom->SetRelativeRotation(FRotator(Hull.ChaseArmPitch, 0, 0));
            Camera->SetRelativeRotation(FRotator(Hull.ChasePitch, 0, 0));
            Camera->FieldOfView = Hull.ChaseFov;
            // Three dials for looking at the thing, because finding a flattering chase angle is an eye
            // question and rebuilding between guesses costs minutes each. -SSChase multiplies the boom,
            // -SSChaseHeight moves the eye up or down, -SSChasePitch tilts it. All optional; with none
            // passed this is exactly the geometry above.
            float Override = 0.f;
            if (FParse::Value(FCommandLine::Get(), TEXT("SSChase="), Override) && Override > 0.f)
                HullChaseScale = Override;
            if (FParse::Value(FCommandLine::Get(), TEXT("SSChaseHeight="), Override))
                CameraBoom->SocketOffset = FVector(0, 0, Override);
            if (FParse::Value(FCommandLine::Get(), TEXT("SSChasePitch="), Override))
                Camera->SetRelativeRotation(FRotator(Override, 0, 0));
            // ---- ShipCore takes the controls ----
            // The plugin is force-based on a simulating rigid body, and its components check exactly once
            // in BeginPlay: if the root is not already simulating they null their pointer, deactivate
            // themselves and never look again. So the body has to be ready BEFORE they are attached.
            Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
            Collision->SetNotifyRigidBodyCollision(true);
            // A 24.84 m hull at boost crosses more than a station wall's thickness in one frame, and this
            // game has never had a swept rigid body before. Without CCD it tunnels.
            Collision->SetUseCCD(true);
            // 4687.5 kg is not a preference. ShipCore divides thrust by mass to get acceleration, its
            // default forward thrust is 15,000,000, and this game's base acceleration is 3200 cm/s^2, so
            // this is the mass at which the plugin's stock numbers reproduce the flight the game already
            // had. Left to itself the engine would derive about 581 kg from the sphere's radius, and then
            // a readability tweak to that radius would silently move acceleration.
            Collision->SetMassOverrideInKg(NAME_None, 4687.5f, true);
            // Off on the body, not in world settings. The world's gravity belongs to the walking hero,
            // whose CharacterMovement needs it to land on the deck; this ship is the only thing in the
            // game that simulates, so it is the only thing that should opt out.
            Collision->SetEnableGravity(false);
            Collision->SetLinearDamping(0.f);
            Collision->SetAngularDamping(0.f);
            Collision->SetSimulatePhysics(true);
            if (Collision->IsSimulatingPhysics())
            {
                // bAutoActivate BEFORE registering, on both. Neither constructor sets it and neither
                // TickComponent checks IsActive(), so a component added from C++ sits there inactive while
                // looking perfectly configured - invisible in the Blueprint workflow the plugin was
                // written for, where the editor activates components for you.
                Thrusters = NewObject<UThrusterManagerComp>(this, TEXT("ShipCoreThrusters"));
                Thrusters->bAutoActivate = true;
                // This is a space game. The plugin disables gravity on the body and then re-applies WORLD
                // gravity by hand as a force every frame, so leaving this alone makes the ship fall.
                Thrusters->bCustomGravity = true;
                Thrusters->CustomGravity = FVector::ZeroVector;
                Thrusters->RegisterComponent();
                Gyros = NewObject<UGyroManagerComp>(this, TEXT("ShipCoreGyros"));
                Gyros->bAutoActivate = true;
                Gyros->RegisterComponent();
                ShipCoreDriven = true;
                Collision->OnComponentHit.AddDynamic(this, &ASSShip::OnHullImpact);
                UE_LOG(LogTemp, Display, TEXT("SSHull: ShipCore driving, mass %.1f kg"), Collision->GetMass());
            }
            else
            {
                // Say so rather than flying the old model while the log implies otherwise.
                Collision->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
                UE_LOG(LogTemp, Warning, TEXT("SSHull: body refused to simulate; ShipCore is NOT driving."));
            }
            UE_LOG(LogTemp, Display, TEXT("SSHull: flying '%s', %.0f cm, chase x%.2f"), *Hull.Id.ToString(),
                   Hull.ScaledLength(), HullChaseScale);
        }
    }
    RefreshPaint();
    EngineAudio->SetSound(SSAudio::PresentationSound(TEXT("Engine")));
    UpdateEngineMix();
    EngineAudio->Play();
    Velocity = GetActorForwardVector() * Tuning->CruiseSpeed;
    // And give the same cruise to the body, when there is one. GetVelocity reads the physics body under
    // ShipCore, so seeding only the member above left the ship reporting a dead stop at BeginPlay while
    // looking correct in every other respect - the Director spawn lead, the enemy aim lead and eleven
    // flight tests all ask this question in the first frame. The -SSPhoenix flag hid it; making the hull
    // the default is what surfaced it.
    if (ShipCoreDriven && Collision && Collision->IsSimulatingPhysics())
        Collision->SetPhysicsLinearVelocity(Velocity);
}
void ASSShip::SetFlightInput(FVector2D Steering, FVector2D Strafe, float Throttle, bool Boost, bool Brake)
{
    Steer = Steering.GetClampedToMaxSize(1.f);
    StrafeInput = Strafe.GetClampedToMaxSize(1.f);
    ThrottleInput = FMath::Clamp(Throttle, -1.f, 1.f);
    BoostInput = Boost;
    BrakeInput = Brake;
}
void ASSShip::AddExternalForce(FVector Force)
{
    Forces += Force.GetClampedToMaxSize(2500.f);
}
void ASSShip::HoldBody(bool Hold)
{
    if (!ShipCoreDriven || !Collision)
        return;
    // ShipCore's managers are components with their own tick, and they push into the body on their own
    // schedule rather than only when this class asks them to. Switching the body off underneath them leaves
    // them calling AddForce, AddTorque and GetMass against a body that is not simulating for as long as the
    // hold lasts - 110 engine warnings across one ten-wave journey, every one of them a push thrown away.
    // Holding the ship therefore has to stop the things pushing it, not only the thing being pushed.
    if (Thrusters)
        Thrusters->SetComponentTickEnabled(!Hold);
    if (Gyros)
        Gyros->SetComponentTickEnabled(!Hold);
    if (Hold)
    {
        // Docking and mooring were written for a kinematic pawn: they move the actor with SetActorLocation
        // and declare the ship stopped by zeroing the hand-kept Velocity member. Neither reaches a
        // simulating body. Chaos keeps integrating the velocity it already had, so the ship slides off the
        // pad while the interpolation drags it back, and a moored ship drifts away from the station it is
        // moored to. Stopping the body makes the scripted move the only thing moving the ship, which is
        // exactly what that code already assumes.
        Collision->SetPhysicsLinearVelocity(FVector::ZeroVector);
        Collision->SetPhysicsAngularVelocityInDegrees(FVector::ZeroVector);
        Collision->SetSimulatePhysics(false);
    }
    else
    {
        // Hand the body back the speed the kinematic path decided on, rather than letting it resume with
        // whatever it was carrying when it was frozen - which, after a stay at the station, is a stale
        // approach velocity pointing at the pad.
        Collision->SetSimulatePhysics(true);
        Collision->SetPhysicsLinearVelocity(Velocity);
        Collision->SetPhysicsAngularVelocityInDegrees(FVector::ZeroVector);
    }
}
void ASSShip::SetDockingTarget(FVector Target, FRotator Rotation, float Duration)
{
    TransitionStart = GetActorLocation();
    TransitionRotation = GetActorRotation();
    TransitionElapsed = 0.f;
    TransitionDuration = FMath::Max(.1f, Duration);
    DockTarget = Target;
    DockRotation = Rotation;
    Docking = true;
    TakingOff = false;
    Moored = false;
    HoldBody(true);
    if (VisualRig)
        VisualRig->PlayLanding(TransitionDuration);
}
void ASSShip::BeginTakeoff(FVector HoverTarget, FRotator Rotation, float Duration)
{
    TransitionStart = GetActorLocation();
    TransitionRotation = GetActorRotation();
    TransitionElapsed = 0.f;
    TransitionDuration = FMath::Max(.1f, Duration);
    DockTarget = HoverTarget;
    DockRotation = Rotation;
    TakingOff = true;
    Docking = Moored = false;
    Velocity = Forces = FVector::ZeroVector;
    HoldBody(true);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetActorTickEnabled(true);
    EngineAudio->Play();
    SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    if (VisualRig)
        VisualRig->PlayTakeoff(TransitionDuration);
}
bool ASSShip::BeginMooring()
{
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (Docking || !GI || !GI->Session.IsFlying())
        return false;
    Moored = true;
    Velocity = Forces = FVector::ZeroVector;
    HoldBody(true);
    SoftTarget = nullptr;
    SetFlightInput(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    return true;
}
void ASSShip::EndMooring()
{
    // Wings back out and gear back up on leaving the pad, which is the same clip flight starts in. The
    // docking clip left the ship in its landing configuration, and nothing else would ever undo it.
    if (VisualRig && VisualRig->HasBlueprintRig())
        VisualRig->PlayTakeoff();
    else if (ShipCoreDriven && SkeletalHull && SkeletalHull->IsVisible())
        if (const FSSHullDefinition Hull(ESSHullIdentity::StellarPhoenix); !Hull.FlightPoseClipPath.IsEmpty())
            if (auto *Pose = LoadObject<UAnimSequence>(nullptr, *Hull.FlightPoseClipPath))
                SkeletalHull->PlayAnimation(Pose, false);
    if (!Moored)
        return;
    Moored = false;
    Forces = FVector::ZeroVector;
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (GI && GI->Session.IsFlying())
        Velocity = GetActorForwardVector() * float(GI->Session.Stats().speed);
    HoldBody(false);
}
float ASSShip::SoftAssistWeight(float Alignment, float ConeDegrees, float MaximumStrength)
{
    if (!FMath::IsFinite(Alignment) || !FMath::IsFinite(ConeDegrees) || ConeDegrees <= 0.f ||
        !FMath::IsFinite(MaximumStrength))
        return 0.f;
    const float Edge = FMath::Cos(FMath::DegreesToRadians(FMath::Clamp(ConeDegrees, .01f, 45.f)));
    const float Position = FMath::Clamp((Alignment - Edge) / FMath::Max(1.f - Edge, SMALL_NUMBER), 0.f, 1.f);
    return FMath::Clamp(MaximumStrength, 0.f, .4f) * Position;
}
void ASSShip::FinishDocking()
{
    SetActorLocation(DockTarget);
    SetActorRotation(DockRotation);
    Pilot->SetVisibility(false);
    if (auto *ReadabilityLight = FindComponentByClass<UPointLightComponent>())
        ReadabilityLight->SetVisibility(false);
    EngineAudio->Stop();
    if (VisualRig)
        VisualRig->UpdateFlight(FVector2D::ZeroVector, FVector2D::ZeroVector, 0.f, false, false);
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Velocity = Forces = FVector::ZeroVector;
    HoldBody(true);
    // Down: gear out and the rear ramp open. One authored motion does both - Cargo_Door_Bone swings 83.7
    // degrees alongside Foot_Bone through 90.3 - so the ship a player walks back up to is already standing
    // on its legs with its door open, rather than resting its belly on the pad with everything stowed.
    // Played last, because SetActorTickEnabled(false) below stops this actor but not its animation.
    if (VisualRig && VisualRig->HasBlueprintRig())
    {
        VisualRig->PlayLanding();
        VisualRig->SetStationCollision(true);
    }
    else if (ShipCoreDriven && SkeletalHull && SkeletalHull->IsVisible())
        if (const FSSHullDefinition Hull(ESSHullIdentity::StellarPhoenix); !Hull.LandingDeployClipPath.IsEmpty())
            if (auto *Deploy = LoadObject<UAnimSequence>(nullptr, *Hull.LandingDeployClipPath))
                SkeletalHull->PlayAnimation(Deploy, false);
    SetActorTickEnabled(false);
}
void ASSShip::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (Docking || TakingOff)
        DockTarget += InOffset;
    TransitionStart += InOffset;
}
void ASSShip::Tick(float Dt)
{
    Super::Tick(Dt);
    UpdateEngineMix();
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !Tuning)
        return;
    auto &S = GI->Session;
    FireCooldown = FMath::Max(0.f, FireCooldown - Dt);
    ImpactCooldown = FMath::Max(0.f, ImpactCooldown - Dt);
    FireVisualSeconds = FMath::Max(0.f, FireVisualSeconds - Dt);
    ShakeSeconds += Dt;
    if (Moored)
    {
        // Existing hazards and damage remain active; GameMode freezes wave progress.
        Velocity = Forces = FVector::ZeroVector;
        SoftTarget = nullptr;
        S.TickFlight(Dt, false, false);
        DrivePresentationPower = 0.f;
        DrivePresentationBoosting = DrivePresentationBraking = false;
        DrivePresentationDamage = float(S.run.damageFeedback);
        return;
    }
    if (Docking || TakingOff)
    {
        TransitionElapsed += Dt;
        const float T = FMath::Clamp(TransitionElapsed / TransitionDuration, 0.f, 1.f);
        const auto Smooth = [](float A) { return A * A * (3.f - 2.f * A); };
        const FVector Hover = DockTarget + FRotationMatrix(DockRotation).GetUnitAxis(EAxis::Z) * 700.f;
        const FVector Position = TakingOff  ? FMath::Lerp(TransitionStart, DockTarget, Smooth(T))
                                 : T < .55f ? FMath::Lerp(TransitionStart, Hover, Smooth(T / .55f))
                                            : FMath::Lerp(Hover, DockTarget, Smooth((T - .55f) / .45f));
        SetActorLocationAndRotation(
            Position, FQuat::Slerp(TransitionRotation.Quaternion(), DockRotation.Quaternion(), Smooth(T)));
        Velocity = FVector::ZeroVector;
        DrivePresentationPower = .18f;
        DrivePresentationBoosting = DrivePresentationBraking = false;
        DrivePresentationDamage = float(S.run.damageFeedback);
        if (VisualRig)
            VisualRig->UpdateFlight(FVector2D::ZeroVector, FVector2D::ZeroVector, DrivePresentationPower, false, false);
        if (TakingOff && T >= 1.f)
        {
            TakingOff = false;
            WasInStationZone = false;
            StationThrottle = 0.f;
            Collision->SetCollisionEnabled(ShipCoreDriven ? ECollisionEnabled::QueryAndPhysics
                                                          : ECollisionEnabled::QueryOnly);
            HoldBody(false);
        }
        return;
    }
    const auto *GM = GetWorld()->GetAuthGameMode<ASSGameMode>();
    const bool InStationZone = GM && GM->IsInStationZone();
    if (!S.IsFlying() && !(GM && GM->IsDepartingStation()))
    {
        Forces = FVector::ZeroVector;
        DrivePresentationPower = 0.f;
        DrivePresentationBoosting = DrivePresentationBraking = false;
        DrivePresentationDamage = float(S.run.damageFeedback);
        return;
    }
    S.TickFlight(Dt, BoostInput && !BrakeInput, InStationZone ? false : BrakeInput, GM && GM->IsDepartingStation());
    if (InStationZone)
    {
        S.run.braking = BrakeInput;
        S.run.brakeHeat = FMath::Max(0.0, S.run.brakeHeat - Dt * 20.0);
        S.run.brakeOverheated = false;
    }
    const auto Stats = S.Stats();
    const float BoostFactor = S.run.boosting ? Tuning->BoostMultiplier : 1.f;
    const float BrakeFactor = S.run.braking ? .47f : 1.f;
    float Speed =
        FMath::Max(Tuning->MinimumSpeed, float(Stats.speed) * (1.f + .3f * ThrottleInput) * BoostFactor * BrakeFactor);
    if (InStationZone)
    {
        if (!WasInStationZone)
            StationThrottle = FMath::Clamp(GetVelocity().Size() / FMath::Max(1.f, float(Stats.speed)), 0.f, 1.f);
        StationThrottle = FMath::Clamp(StationThrottle + ThrottleInput * Dt * .5f - (BrakeInput ? Dt : 0.f), 0.f, 1.f);
        Speed = float(Stats.speed) * StationThrottle * BoostFactor;
    }
    WasInStationZone = InStationZone;
    DrivePresentationPower = FMath::Clamp(.42f + .28f * FMath::Max(0.f, ThrottleInput) +
                                              .3f * float(GetVelocity().Size() / FMath::Max(1.f, Tuning->CruiseSpeed)),
                                          .25f, 1.35f);
    DrivePresentationBoosting = S.run.boosting;
    DrivePresentationBraking = S.run.braking;
    DrivePresentationDamage = FMath::Clamp(float(S.run.damageFeedback), 0.f, 1.f);
    if (VisualRig)
        VisualRig->UpdateFlight(Steer, StrafeInput, DrivePresentationPower, S.run.boosting, S.run.braking);
    const float Authority = float(Stats.maneuver) / 1700.f;
    const float Interference = S.run.interferenceSeconds > 0 ? .7f : 1.f;
    if (ShipCoreDriven)
    {
        // Nothing to drive while the body is held. HoldBody switches the body off for the length of a
        // scripted move - docking onto a pad, sitting moored at the station - and that move owns the ship
        // until it hands it back. ShipCore has no way to know, so without this its thrusters and gyros go on
        // calling AddForce, AddTorque and GetMass against a body that is not simulating: 110 engine warnings
        // in a single ten-wave journey, every one of them a push that was thrown away. The kinematic branch
        // below must not run either - it would move the actor out from under the scripted move - which is
        // why this is a guard inside the branch rather than a condition on it.
        if (Collision && Collision->IsSimulatingPhysics())
            DriveShipCore(Dt, Stats.acceleration, Stats.maneuver, Stats.response, Speed, Authority, Interference);
    }
    else
    {
        // Bounded substeps preserve steering/acceleration and swept movement at low FPS.
        const int32 Steps = FMath::Clamp(FMath::CeilToInt(Dt / (1.f / 120.f)), 1, 32);
        const float Step = Dt / Steps;
        for (int32 I = 0; I < Steps; ++I)
        {
            auto Rotation = GetActorRotation();
            Rotation.Yaw += Steer.X * Tuning->SteeringDegrees * Authority * Interference * Step;
            Rotation.Pitch = FMath::Clamp(
                Rotation.Pitch + Steer.Y * Tuning->SteeringDegrees * Authority * Interference * Step, -85.f, 85.f);
            Rotation.Roll = 0;
            SetActorRotation(Rotation);
            const FVector Desired =
                GetActorForwardVector() * Speed +
                (GetActorRightVector() * StrafeInput.X + GetActorUpVector() * StrafeInput.Y) * float(Stats.maneuver);
            const FVector ResponseDelta = (Desired - Velocity) * (1.f - FMath::Exp(-float(Stats.response) * Step));
            Velocity += ResponseDelta.GetClampedToMaxSize(float(Stats.acceleration) * Step);
            Velocity += Forces.GetClampedToMaxSize(4500.f) * Step;
            FHitResult Hit;
            AddActorWorldOffset(Velocity * Step, true, &Hit);
            if (Hit.bBlockingHit)
            {
                if (ImpactCooldown <= 0)
                {
                    ReceiveDamage(15.f * float(S.DamageScale()));
                    ImpactCooldown = .8f;
                }
                Velocity = FVector::VectorPlaneProject(Velocity, Hit.Normal) * .65f;
            }
        }
    }
    Forces = FVector::ZeroVector;
    const float Bank = -Steer.X * 28.f - StrafeInput.X * 12.f;
    HullMesh->SetRelativeRotation(
        FMath::RInterpTo(HullMesh->GetRelativeRotation(), FRotator(-StrafeInput.Y * 5.f, 0, Bank), Dt, 6.f));
    CameraBoom->TargetArmLength = FMath::FInterpTo(
        CameraBoom->TargetArmLength,
        (FMath::Max(900.f, Tuning->ChaseDistance) + (S.run.boosting ? 110.f : 0.f)) * HullChaseScale, Dt, 3.f);
    // Relative to whatever this hull is framed at, rather than to the one hull the 80/86 pair was chosen
    // for - otherwise a wider hull snaps back to the narrow framing on its first frame of boost.
    const float BaseFov = FSSHullDefinition(SelectedHullIdentity()).ChaseFov;
    Camera->FieldOfView = FMath::FInterpTo(Camera->FieldOfView, S.run.boosting ? BaseFov + 6.f : BaseFov, Dt, 3.f);
    // Boost engaging is an event, but every drive effect in the game is a sustained level, so acceleration
    // reads as a state change rather than as a shove. This is the transient: full on the frame boost is pressed,
    // gone in about a third of a second.
    if (S.run.boosting && !WasBoosting)
        BoostPunch = 1.f;
    WasBoosting = S.run.boosting;
    BoostPunch = FMath::Max(0.f, BoostPunch - Dt * 2.8f);
    FVector CameraOffset = FVector::ZeroVector;
    if (GI->Session.settings.cameraShake)
    {
        if (S.run.damageFeedback > 0)
        {
            // Two non-harmonic axes so the motion does not trace a line, peaking at 0.20 degrees for the
            // lightest hit and 0.796 at the heaviest against the 900 cm boom, deliberately under one degree.
            const float Amplitude = (3.f + 22.f * ShakeSeverity) * float(S.run.damageFeedback);
            CameraOffset += FVector(0, FMath::Sin(ShakeSeconds * 70.f) * Amplitude,
                                    FMath::Cos(ShakeSeconds * 53.f) * Amplitude * .7f);
        }
        // Squared so the kick eases out rather than ending abruptly. The camera falls back along the boom and
        // catches up, which is the shove; the rumble underneath it is deliberately slower than the damage
        // shake's 70 and 53 hertz, so a hit taken while boosting still reads as a separate, sharper event.
        const float Punch = BoostPunch * BoostPunch;
        const float Amplitude = (S.run.boosting ? 2.2f : 0.f) + 9.f * Punch;
        CameraOffset += FVector(-16.f * Punch, FMath::Sin(ShakeSeconds * 34.f) * Amplitude,
                                FMath::Cos(ShakeSeconds * 27.f) * Amplitude * .6f);
    }
    Camera->SetRelativeLocation(CameraOffset);
    if (SpeedPostFX.GetValueOnGameThread() != 0)
    {
        // Follows the boost punch and the held boost, not the damage clock: these are speed cues, and a hit
        // already has its own louder language in the shake and the red drive pulse.
        const float Push = FMath::Clamp(BoostPunch * .6f + (S.run.boosting ? .5f : 0.f), 0.f, 1.f);
        Camera->PostProcessBlendWeight = 1.f;
        Camera->PostProcessSettings.bOverride_SceneFringeIntensity = true;
        Camera->PostProcessSettings.SceneFringeIntensity = 1.6f * Push;
        // .4 is the engine's own default, so cruising looks exactly as it did and only thrust tightens it.
        Camera->PostProcessSettings.bOverride_VignetteIntensity = true;
        Camera->PostProcessSettings.VignetteIntensity = .4f + .35f * Push;
    }
    else
        Camera->PostProcessBlendWeight = 0.f;
    UpdateEngineMix();
    // Exhausts follow the drive, which is the same value the HUD crosshair and the dust field read, so the
    // plume grows under throttle and boost rather than burning flat. Scale rather than a Niagara parameter
    // on purpose: the pack's parameter names are its own and guessing one would fail silently.
    const float PlumeDrive = FMath::Clamp(.55f + .9f * DrivePresentationPower, .4f, 1.8f);
    for (UNiagaraComponent *Plume : HullExhausts)
        if (IsValid(Plume))
            Plume->SetRelativeScale3D(FVector(PlumeDrive));
    SoftTarget = nullptr;
    float Best = FMath::Cos(FMath::DegreesToRadians(Tuning->SoftAimDegrees));
    const FVector Aim =
        Camera ? (CrosshairWorldPoint() - Camera->GetComponentLocation()).GetSafeNormal() : AimDirection();
    for (TActorIterator<ASSWorldBody> It(GetWorld()); It; ++It)
    {
        if (!It->IsWeaponTarget())
            continue;
        const FVector Delta = It->GetActorLocation() - GetActorLocation();
        if (Delta.SizeSquared() > FMath::Square(Tuning->WeaponRange))
            continue;
        const FVector SightOrigin = Camera ? Camera->GetComponentLocation() : GetActorLocation();
        const float Dot = FVector::DotProduct(Aim, (It->GetActorLocation() - SightOrigin).GetSafeNormal());
        if (Dot <= Best)
            continue;
        FHitResult Hit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(this);
        GetWorld()->LineTraceSingleByChannel(Hit, MuzzleWorldPosition(), It->GetActorLocation(), ECC_Visibility,
                                             Params);
        if (!Hit.bBlockingHit || Hit.GetActor() == *It)
        {
            Best = Dot;
            SoftTarget = *It;
        }
    }
}
void ASSShip::RequestDodge()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (Moored || Docking || TakingOff || !GI || !GI->Session.Dodge())
        return;
    FVector2D Direction = StrafeInput.IsNearlyZero() ? Steer : StrafeInput;
    if (Direction.IsNearlyZero())
        Direction = FVector2D(1, 0);
    Direction.Normalize();
    const FVector Dodge =
        (GetActorRightVector() * Direction.X + GetActorUpVector() * Direction.Y) * Tuning->DodgeImpulse;
    Velocity += Dodge;
    // The same member-versus-body gap that swallowed collision damage and hazard shoves, and the same fix:
    // the line above moves the hand-kept integrator's velocity, which a simulating body never reads, so on
    // a force-driven hull the dodge key did nothing whatsoever. The body's velocity is moved by exactly the
    // vector the kinematic line adds, so one dodge is one dodge on either drive rather than a figure scaled
    // by whichever hull's mass happens to be flying. It is set rather than queued as an impulse because a
    // dodge is an instantaneous change of velocity and reads back as one immediately, which is both what the
    // kinematic path has always done and what anything asking "did the dodge take" can actually observe.
    if (ShipCoreDriven && Collision && Collision->IsSimulatingPhysics())
        Collision->SetPhysicsLinearVelocity(Collision->GetPhysicsLinearVelocity() + Dodge);
    // No collision immunity is granted; every world body still applies damage.
}
void ASSShip::ReceiveDamage(float Amount, SS::DamageType Type)
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI)
        return;
    // Phase the shake from this impact instead of from world time, and scale it by severity.
    // Severity belongs here, in the single damage funnel, because Session::ApplyDamage re-arms
    // damageFeedback on every damage event: storing it on contact alone would fire a full-strength
    // shake for an enemy laser graze arriving seconds later.
    ShakeSeconds = 0.f;
    ShakeSeverity = FMath::Clamp((Amount - 8.f) / 60.f, .15f, 1.f);
    GI->Session.ApplyDamage(Amount, Type);
    UGameplayStatics::PlaySoundAtLocation(
        this, SSAudio::PresentationSound(TEXT("Impact")), GetActorLocation(),
        float(GI->Session.settings.masterVolume * GI->Session.settings.effectsVolume));
}
void ASSShip::ReceiveImpact(float Amount, FVector AwayFromContact)
{
    ReceiveDamage(Amount, SS::DamageType::Kinetic);
    const auto *GI = GetGameInstance<USSGameInstance>();
    if (!GI || !GI->Session.IsFlying() || !FMath::IsFinite(Amount) || Amount <= 0.f || AwayFromContact.ContainsNaN())
        return;
    // A contact changes velocity once, in cm/s. Gravity remains an acceleration
    // integrated over time; treating a single impact that way weakened it at high FPS.
    const FVector Push = AwayFromContact.GetSafeNormal() * FMath::Min(1400.f, Amount * 20.f);
    Velocity += Push;
    // And give it to the body, which is the thing that moves under ShipCore. This is the third time the
    // same gap has been found: GetVelocity read a member the solver never writes, collision damage came
    // off a swept hit a simulating body never performs, and this - the only push hazards ever apply - was
    // landing in a member the solver never reads. The Phoenix took the damage and did not move. A wave of
    // asteroids would have hurt it and never once shoved it, which is the kind of defect that reads as
    // "the collisions feel weightless" rather than as anything a test named.
    //
    // bVelChange is what makes it the same push rather than a similar one: the kinematic line above adds
    // centimetres per second directly, and an impulse scaled by mass would be a different quantity wearing
    // the same number. Hazard contact does not arrive through OnComponentHit - ASSWorldBody does its own
    // analytic closest-approach test and calls this - so nothing else covers it.
    if (ShipCoreDriven && Collision && Collision->IsSimulatingPhysics())
        Collision->AddImpulse(Push, NAME_None, true);
}
