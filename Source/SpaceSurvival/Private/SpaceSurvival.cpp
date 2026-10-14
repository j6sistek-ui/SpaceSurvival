#include "Modules/ModuleManager.h"
#if WITH_EDITOR
#include "SSRenderedViewDiagnostic.h"
#endif

class FSpaceSurvivalModule final : public FDefaultGameModuleImpl
{
public:
    virtual void StartupModule() override
    {
        FDefaultGameModuleImpl::StartupModule();
#if WITH_EDITOR
        SSRenderedViewDiagnostic::Initialize();
#endif
    }

    virtual void ShutdownModule() override
    {
#if WITH_EDITOR
        SSRenderedViewDiagnostic::Shutdown();
#endif
        FDefaultGameModuleImpl::ShutdownModule();
    }
};

IMPLEMENT_PRIMARY_GAME_MODULE(FSpaceSurvivalModule, SpaceSurvival, "SpaceSurvival");
