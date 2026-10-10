#pragma once

#if WITH_EDITOR
// An isolated, opt-in observation tool. No render settings or gameplay state are changed.
namespace SSRenderedViewDiagnostic
{
void Initialize();
void Shutdown();
} // namespace SSRenderedViewDiagnostic
#endif
