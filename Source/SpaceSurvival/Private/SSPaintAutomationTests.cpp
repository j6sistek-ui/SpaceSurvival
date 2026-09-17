#include "Misc/AutomationTest.h"
#include "SSShipPaint.h"
#include "Domain/SurvivalCore.h"
#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPaintAccountPayload, "SpaceSurvival.Paint.AccountPayload",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPaintAccountPayload::RunTest(const FString &Parameters)
{
    SS::Account Painted;
    Painted.paint = {{3, -1, 9, 0}};
    std::string Error;
    SS::Account Decoded;
    TestTrue(TEXT("Painted account decodes"), SS::DecodeAccount(SS::EncodeAccount(Painted), Decoded, Error));
    TestTrue(TEXT("Paint survives the round trip"), Decoded.paint == Painted.paint);
    TestTrue(TEXT("Re-encoding is stable"), SS::EncodeAccount(Decoded) == SS::EncodeAccount(Painted));

    // A version 2 payload, written before the paint bay existed, still loads and means the factory finish.
    std::string Version2 = SS::EncodeAccount(SS::Account{});
    const std::string Marker = "SS ACCOUNT 3 ";
    TestTrue(TEXT("Fresh payload is version 3"), Version2.compare(0, Marker.size(), Marker) == 0);
    Version2.replace(0, Marker.size(), "SS ACCOUNT 2 ");
    for (int Trailing = 0; Trailing < SS::PaintSections; ++Trailing)
        Version2.erase(Version2.find_last_of(' '));
    SS::Account Legacy;
    Legacy.paint = {{5, 5, 5, 5}};
    TestTrue(TEXT("Version 2 payload decodes"), SS::DecodeAccount(Version2, Legacy, Error));
    TestTrue(TEXT("Version 2 payload means factory finish"), Legacy.paint == SS::Account{}.paint);

    // Out-of-range choices are refused rather than clamped: the file is wrong, not the pilot.
    std::string Version3 = SS::EncodeAccount(SS::Account{});
    Version3.replace(Version3.size() - 2, 2, "10");
    TestFalse(TEXT("Colour past the palette is rejected"), SS::DecodeAccount(Version3, Decoded, Error));
    Version3 = SS::EncodeAccount(SS::Account{});
    Version3.replace(Version3.size() - 2, 2, "-2");
    TestFalse(TEXT("Colour below the factory finish is rejected"), SS::DecodeAccount(Version3, Decoded, Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPaintSectionsAndPalette, "SpaceSurvival.Paint.SectionsAndPalette",
                                 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSSPaintSectionsAndPalette::RunTest(const FString &Parameters)
{
    // The starter hull's five slots and the Acorn's nine map to the four sections, and glass stays unpainted.
    TestEqual(TEXT("Spacecraft body"), SSPaint::SectionForMaterial(TEXT("MI_White_Spacecraft_02")),
              (int32)SSPaint::Body);
    TestEqual(TEXT("White wing"), SSPaint::SectionForMaterial(TEXT("MI_White_Wing")), (int32)SSPaint::Wings);
    TestEqual(TEXT("Blue wing"), SSPaint::SectionForMaterial(TEXT("MI_Blue_Wing")), (int32)SSPaint::Wings);
    TestEqual(TEXT("Engine"), SSPaint::SectionForMaterial(TEXT("MI_White_Engine")), (int32)SSPaint::Engines);
    TestEqual(TEXT("Weapon"), SSPaint::SectionForMaterial(TEXT("MI_Weapon")), (int32)SSPaint::Weapons);
    TestEqual(TEXT("Acorn panels"), SSPaint::SectionForMaterial(TEXT("M_AcornV2_IvoryPanels")), (int32)SSPaint::Body);
    TestEqual(TEXT("Windscreen is never painted"), SSPaint::SectionForMaterial(TEXT("M_AcornV2_Windscreen")),
              INDEX_NONE);
    TestEqual(TEXT("Nav lights are never painted"), SSPaint::SectionForMaterial(TEXT("M_AcornV2_IonAndNav")),
              INDEX_NONE);
    TestEqual(TEXT("Cockpit padding is never painted"), SSPaint::SectionForMaterial(TEXT("M_AcornV2_CockpitPadding")),
              INDEX_NONE);
    TSet<FString> Names;
    TSet<uint32> Colours;
    for (int32 Colour = 0; Colour < SS::PaintColours; ++Colour)
    {
        Names.Add(SSPaint::ColourName(Colour));
        Colours.Add(SSPaint::Colour(Colour).ToFColor(true).DWColor());
    }
    TestEqual(TEXT("Ten distinct colour names"), Names.Num(), SS::PaintColours);
    TestEqual(TEXT("Ten distinct colours"), Colours.Num(), SS::PaintColours);
    TestEqual(TEXT("Factory finish has a name"), FString(SSPaint::ColourName(-1)), FString(TEXT("Factory finish")));
    for (int32 Section = 0; Section < SS::PaintSections; ++Section)
        TestTrue(TEXT("Every section has a name"), FCString::Strlen(SSPaint::SectionName(Section)) > 0);
    return true;
}
#endif
