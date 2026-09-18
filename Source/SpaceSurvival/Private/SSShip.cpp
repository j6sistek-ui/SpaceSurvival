#include "SSShip.h"
#include "SSShipPaint.h"
#include "SSVFXPresentation.h"
#include "SSAudio.h"
#include "SSGameInstance.h"
#include "SSGameMode.h"
#include "SSPhase1Data.h"
#include "SSShipPresentation.h"
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
    Thrusters->SetMaxSpeedLimit(Speed, FMath::Max(100.f, Speed * .12f));

    // Turning authority and how hard it stops turning. Response is re-homed onto the gyro's proportional
    // gain rather than dropped: it was a rate constant on linear velocity error and there is no such dial
    // on a rigid body, so it becomes the rate constant on ANGULAR error. That is a re-purposing and not a
    // translation, and the Thrusters upgrade stays observable as crisper turning because of it.
    Gyros->MaxTotalTorque = FMath::Max(.5, Maneuver / 340.0);
    Gyros->ProportionalGain = FMath::Max(.5, Response);

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
    const FVector Thrust(FMath::Clamp(Trim + (BoostInput ? 1.f : 0.f), -1.f, 1.f),
                         FMath::Clamp(StrafeInput.X, -1.f, 1.f), FMath::Clamp(StrafeInput.Y, -1.f, 1.f));
    Thrusters->SetThrustersInput(Thrust);
    const float Turn = Authority * Interference;
    Gyros->SetGyrosInput(FVector(FMath::Clamp(-Steer.Y, -1.f, 1.f) * Turn, FMath::Clamp(Steer.X, -1.f, 1.f) * Turn,
                                 // A little roll into the turn, because a ship that yaws flat reads as a
                                 // cursor. The gyro damps roll rate but has no attitude reference, so this
                                 // is a lean and not a bank that holds.
                                 FMath::Clamp(-Steer.X, -1.f, 1.f) * .35f * Turn));

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
    // hull, whose whole body sits inside that ball. A 2484 cm hull's nose reaches 1242 cm past its own
    // origin, so the same number asks a ship to put its centre where its nose already is. Half a hull plus
    // the classic margin, so every ship is judged by where its body is rather than by one ship's length.
    const float HalfLength = SkeletalHull && SkeletalHull->IsVisible()
                                 ? FSSHullDefinition(ESSHullIdentity::StellarPhoenix).ScaledLength() * .5f
                                 : 0.f;
    return FMath::Max(1200.f, HalfLength + 1200.f);
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
    if (const auto *GI = GetGameInstance<USSGameInstance>())
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
    RefreshPaint();
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
    // paint, the module presentation and the chase-framing test all still read it, and none of them has to
    // learn about a second kind of hull before the flight model itself moves.
    // Behind -SSPhoenix, the same idiom HullAssetPath already uses for -SSShipRefresh. The first version
    // switched hulls whenever the pack happened to be installed, which is not a decision a build should
    // make for itself: it hid the static hull, and USSShipPresentation hangs the exhausts, muzzle flashes
    // and fitted upgrade modules off that hull, so ShipPresentationSelection went red on the one machine
    // that owns the pack. Opt in explicitly and the shipped ship is untouched everywhere.
    if (const FSSHullDefinition Hull(ESSHullIdentity::StellarPhoenix);
        FParse::Param(FCommandLine::Get(), TEXT("SSPhoenix")) && Hull.Installed())
    {
        if (auto *HullSkeletal = LoadObject<USkeletalMesh>(nullptr, *Hull.MeshPath))
        {
            SkeletalHull->SetSkeletalMesh(HullSkeletal);
            // Authored along +Y, so it needs a quarter turn to point where the pawn calls forward.
            SkeletalHull->SetRelativeRotation(FRotator(0, Hull.MeshYaw, 0));
            SkeletalHull->SetRelativeScale3D(FVector(Hull.HullScale));
            SkeletalHull->SetVisibility(true);
            HullMesh->SetVisibility(false);
            // Gear up and ramp shut. The rest pose is the landing configuration, so a ship that never
            // played this would fly with its undercarriage down and its cargo ramp hanging open.
            if (auto *Stow = LoadObject<UAnimSequence>(nullptr, *Hull.LandingStowClipPath))
                SkeletalHull->PlayAnimation(Stow, false);
            // Found by flying it and looking, not derived. Three candidates were captured in Wave 10:
            // the full 5.15 length ratio put the camera inside an asteroid with the ship out of frame;
            // the square root, 2.27, was close enough that the hull filled the middle of the screen; and
            // 4.5 with the eye high and the tilt shallow is where both things the camera has to do are
            // actually done at once.
            //
            // Both things matter and they pull against each other. The hull has to READ - this ship's
            // character is its swept planform and that is invisible from directly astern - and the
            // CROSSHAIR has to be usable. The reticle is drawn at screen centre because aim is defined as
            // camera-forward, which was free when the hull was 4.82 m and the centre was empty space past
            // it. At 24.84 m the hull IS the centre, so a camera tilted down far enough to show the
            // planform puts the reticle on your own ship and you cannot see what you are shooting at.
            // High eye, shallow tilt: the ship settles into the lower third where its top is visible, and
            // the centre stays clear sky.
            HullChaseScale = 4.5f;
            // Lift and tilt the view. Dead astern is this hull's worst angle: from directly behind, a
            // 24.84 m ship is a slab and its swept wings are edge-on and invisible. Looking slightly down
            // on it shows the planform, which is where the wings actually read.
            CameraBoom->SocketOffset = FVector(0, 0, 3000.f);
            Camera->SetRelativeRotation(FRotator(-16.f, 0, 0));
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
            // The pack's own exhausts, on the pack's own engine bones. USSShipPresentation fits exhausts
            // to the static hull it was measured against and knows nothing about this mesh, so without
            // these the ship flies with no engine effect at all - which is exactly how the first capture
            // came out.
            if (auto *Exhaust = LoadObject<UNiagaraSystem>(
                    nullptr, TEXT("/Game/Stellar_Phoenix/Spaceship/VFX/VFX_Exhaust.VFX_Exhaust")))
            {
                // NOT the bones called Engine_*. Every one of those sits at [0, 0, 0] - they are
                // rotation-only control bones, exactly like the wing bones - so attaching to them put the
                // plumes inside the ship's belly. The bones that are actually AT the nozzles are the
                // Nozzle_Back_* set, measured in the hull's authored space where -Y is aft:
                //   Nozzle_Back_Up_Left/Right    at X +/-182, Y -627.5, Z 553.0
                //   Nozzle_Back_Down_Left/Right  at X +/-183, Y -851.9, Z 188.2
                // The two big side nacelles, which are what actually reads as "engines" on this ship, have
                // no bone of their own; their position comes from the separate engine meshes the pack
                // ships, whose origins are X +/-589.85, Y -636.6, Z 349.64.
                for (const TCHAR *Nozzle : {TEXT("Nozzle_Back_Up_Left_Mesh"), TEXT("Nozzle_Back_Up_Right_Mesh"),
                                            TEXT("Nozzle_Back_Down_Left_Mesh"), TEXT("Nozzle_Back_Down_Right_Mesh")})
                {
                    if (auto *Plume = UNiagaraFunctionLibrary::SpawnSystemAttached(
                            Exhaust, SkeletalHull, FName(Nozzle), FVector::ZeroVector, FRotator::ZeroRotator,
                            EAttachLocation::SnapToTarget, false))
                        HullExhausts.Add(Plume);
                }
                // Two more were tried at the big side nacelles, placed by hand at the engine meshes'
                // own origins, and they are deliberately not here. The pack's VFX_Exhaust does not emit
                // along the axis a component rotation would steer - the plumes fired out of the ship's
                // flanks like comet tails whichever way the component was turned - so they were guesses
                // dressed up as placement. The four above snap to real bones and inherit the rig's own
                // orientations, which is why they point aft. Bigger nacelle plumes need the system's own
                // emission settings read, not another transform invented for it.
            }
            UE_LOG(LogTemp, Display, TEXT("SSHull: flying '%s', %.0f cm, chase x%.2f"), *Hull.Id.ToString(),
                   Hull.ScaledLength(), HullChaseScale);
        }
    }
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
void ASSShip::SetDockingTarget(FVector Target, FRotator Rotation)
{
    DockTarget = Target;
    DockRotation = Rotation;
    Docking = true;
    HoldBody(true);
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
    Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Velocity = Forces = FVector::ZeroVector;
    HoldBody(true);
    // Down: gear out and the rear ramp open. One authored motion does both - Cargo_Door_Bone swings 83.7
    // degrees alongside Foot_Bone through 90.3 - so the ship a player walks back up to is already standing
    // on its legs with its door open, rather than resting its belly on the pad with everything stowed.
    // Played last, because SetActorTickEnabled(false) below stops this actor but not its animation.
    if (ShipCoreDriven && SkeletalHull && SkeletalHull->IsVisible())
        if (const FSSHullDefinition Hull(ESSHullIdentity::StellarPhoenix); !Hull.LandingDeployClipPath.IsEmpty())
            if (auto *Deploy = LoadObject<UAnimSequence>(nullptr, *Hull.LandingDeployClipPath))
                SkeletalHull->PlayAnimation(Deploy, false);
    SetActorTickEnabled(false);
}
void ASSShip::ApplyWorldOffset(const FVector &InOffset, bool bWorldShift)
{
    Super::ApplyWorldOffset(InOffset, bWorldShift);
    if (Docking)
        DockTarget += InOffset;
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
    if (Docking)
    {
        SetActorLocation(FMath::VInterpTo(GetActorLocation(), DockTarget, Dt, 2.f));
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), DockRotation, Dt, 2.f));
        Velocity = FVector::ZeroVector;
        DrivePresentationPower = .18f;
        DrivePresentationBoosting = DrivePresentationBraking = false;
        DrivePresentationDamage = float(S.run.damageFeedback);
        return;
    }
    if (!S.IsFlying())
    {
        Forces = FVector::ZeroVector;
        DrivePresentationPower = 0.f;
        DrivePresentationBoosting = DrivePresentationBraking = false;
        DrivePresentationDamage = float(S.run.damageFeedback);
        return;
    }
    S.TickFlight(Dt, BoostInput, BrakeInput);
    const auto Stats = S.Stats();
    const float BoostFactor = S.run.boosting ? Tuning->BoostMultiplier : 1.f;
    const float BrakeFactor = S.run.braking ? .47f : 1.f;
    const float Speed =
        FMath::Max(Tuning->MinimumSpeed, float(Stats.speed) * (1.f + .3f * ThrottleInput) * BoostFactor * BrakeFactor);
    DrivePresentationPower = FMath::Clamp(.42f + .28f * FMath::Max(0.f, ThrottleInput) +
                                              .3f * float(Velocity.Size() / FMath::Max(1.f, Tuning->CruiseSpeed)),
                                          .25f, 1.35f);
    DrivePresentationBoosting = S.run.boosting;
    DrivePresentationBraking = S.run.braking;
    DrivePresentationDamage = FMath::Clamp(float(S.run.damageFeedback), 0.f, 1.f);
    const float Authority = float(Stats.maneuver) / 1700.f;
    const float Interference = S.run.interferenceSeconds > 0 ? .7f : 1.f;
    if (ShipCoreDriven)
    {
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
    Camera->FieldOfView = FMath::FInterpTo(Camera->FieldOfView, S.run.boosting ? 86.f : 80.f, Dt, 3.f);
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
    const FVector Aim = AimDirection();
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
        GetWorld()->LineTraceSingleByChannel(Hit, GetActorLocation() + GetActorForwardVector() * 240.f,
                                             It->GetActorLocation(), ECC_Visibility, Params);
        if (!Hit.bBlockingHit || Hit.GetActor() == *It)
        {
            Best = Dot;
            SoftTarget = *It;
        }
    }
}
FVector ASSShip::AimDirection() const
{
    return Camera ? Camera->GetForwardVector() : GetActorForwardVector();
}
void ASSShip::RequestDodge()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (Moored || !GI || !GI->Session.Dodge())
        return;
    FVector2D Direction = StrafeInput.IsNearlyZero() ? Steer : StrafeInput;
    if (Direction.IsNearlyZero())
        Direction = FVector2D(1, 0);
    Direction.Normalize();
    Velocity += (GetActorRightVector() * Direction.X + GetActorUpVector() * Direction.Y) * Tuning->DodgeImpulse;
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
    Velocity += AwayFromContact.GetSafeNormal() * FMath::Min(1400.f, Amount * 20.f);
}
void ASSShip::Fire()
{
    auto *GI = GetGameInstance<USSGameInstance>();
    if (Moored || !GI || !GI->Session.IsFlying() || FireCooldown > 0)
        return;
    auto &S = GI->Session;
    const bool Cannon = S.run.weapon == SS::Weapon::HeavyCannon;
    FireCooldown = Cannon ? Tuning->CannonInterval : Tuning->LaserInterval;
    // Long enough to stay lit between rapid-laser shots, short enough that one cannon shot does
    // not hold the reticle open for most of a second.
    FireVisualSeconds = .16f;
    const FVector Start = GetActorLocation() + GetActorForwardVector() * 240.f;
    const FVector Sight = AimDirection();
    const FVector SightOrigin = Camera ? Camera->GetComponentLocation() : Start;
    FVector AimPoint = SightOrigin + Sight * Tuning->WeaponRange;
    FCollisionQueryParams SightQuery(SCENE_QUERY_STAT(SSManualAim), false, this);
    FHitResult SightHit;
    // Resolve the visible reticle point, then converge from the real muzzle.
    // Camera obstructions behind the muzzle must never reverse a shot.
    if (GetWorld()->LineTraceSingleByChannel(SightHit, SightOrigin, AimPoint, ECC_Visibility, SightQuery) &&
        FVector::DotProduct(SightHit.ImpactPoint - Start, Sight) > 1.f)
        AimPoint = SightHit.ImpactPoint;
    FVector Direction = (AimPoint - Start).GetSafeNormal();
    if (IsValid(SoftTarget) && !SoftTarget->IsActorBeingDestroyed())
    {
        const FVector TargetDelta = SoftTarget->GetActorLocation() - SightOrigin;
        const float Alignment = FVector::DotProduct(Sight, TargetDelta.GetSafeNormal());
        const float Weight = SoftAssistWeight(Alignment, Tuning->SoftAimDegrees, MaximumSoftAssist);
        // Recheck the current sightline at trigger time; a previous frame's target must not pull a turn.
        if (FVector::DistSquared(SoftTarget->GetActorLocation(), GetActorLocation()) <=
            FMath::Square(Tuning->WeaponRange))
            Direction = FMath::Lerp(Direction, (SoftTarget->GetActorLocation() - Start).GetSafeNormal(), Weight)
                            .GetSafeNormal();
    }
    // The existing muzzle trace/projectile sweep still handles nearby cover;
    // selecting a visible aim point never permits shooting through an obstacle.
    const float Damage = float(S.Stats().weaponDamage);
    if (Cannon)
    {
        auto *Shot = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Shot)
            Shot->Launch(Direction, 19000.f, Damage, true, this, Tuning->WeaponRange);
    }
    else
    {
        FHitResult Hit;
        FCollisionQueryParams Params;
        Params.AddIgnoredActor(this);
        GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Direction * Tuning->WeaponRange, ECC_Visibility,
                                             Params);
        if (Hit.bBlockingHit)
            if (auto *FX = GetWorld()->GetSubsystem<USSCombatVFXSubsystem>())
                FX->PlayImpact(Hit.ImpactPoint, Hit.ImpactNormal, true, false);
        if (auto *Body = Cast<ASSWorldBody>(Hit.GetActor()))
            Body->ReceiveWeaponHit(Damage);
        auto *Trace = GetWorld()->SpawnActor<ASSProjectile>(Start, Direction.Rotation());
        if (Trace)
            Trace->Launch(Direction, 55000.f, 0.f, true, this, Tuning->WeaponRange);
    }
    UGameplayStatics::PlaySoundAtLocation(this, SSAudio::PresentationSound(Cannon ? TEXT("Cannon") : TEXT("Laser")),
                                          Start, float(S.settings.masterVolume * S.settings.effectsVolume));
}
