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

    // A version 2 payload, written before either the paint bay or the wardrobe existed, still loads
    // and means the factory finish and no chosen body.
    std::string Version2 = SS::EncodeAccount(SS::Account{});
    const std::string Marker = "SS ACCOUNT 4 ";
    TestTrue(TEXT("Fresh payload is version 4"), Version2.compare(0, Marker.size(), Marker) == 0);
    Version2.replace(0, Marker.size(), "SS ACCOUNT 2 ");
    // The four paint sections AND the wardrobe choice: version 2 predates both trailing fields.
    for (int Trailing = 0; Trailing < SS::PaintSections + 1; ++Trailing)
        Version2.erase(Version2.find_last_of(' '));
    SS::Account Legacy;
    Legacy.paint = {{5, 5, 5, 5}};
    Legacy.hero = 3;
    TestTrue(TEXT("Version 2 payload decodes"), SS::DecodeAccount(Version2, Legacy, Error));
    TestTrue(TEXT("Version 2 payload means factory finish"), Legacy.paint == SS::Account{}.paint);
    TestEqual(TEXT("Version 2 payload means no body was ever chosen"), Legacy.hero, -1);

    // A version 3 payload - written after the paint bay but before the wardrobe - keeps its paint and
    // simply has no choice recorded. This is the migration the wardrobe actually needs to survive.
    std::string Version3 = SS::EncodeAccount(Painted);
    Version3.replace(0, Marker.size(), "SS ACCOUNT 3 ");
    Version3.erase(Version3.find_last_of(' '));
    SS::Account Upgraded;
    Upgraded.hero = 5;
    TestTrue(TEXT("Version 3 payload decodes"), SS::DecodeAccount(Version3, Upgraded, Error));
    TestTrue(TEXT("Version 3 payload keeps its paint"), Upgraded.paint == Painted.paint);
    TestEqual(TEXT("Version 3 payload means no body was ever chosen"), Upgraded.hero, -1);

    // The wardrobe choice survives its own round trip.
    SS::Account Worn = SS::Account{};
    Worn.hero = 3;
    SS::Account WornBack;
    TestTrue(TEXT("A wardrobe choice round trips"), SS::DecodeAccount(SS::EncodeAccount(Worn), WornBack, Error));
    TestEqual(TEXT("The body chosen is the body restored"), WornBack.hero, 3);

    // Out-of-range choices are refused rather than clamped: the file is wrong, not the pilot. The
    // wardrobe choice is the last field now, so the paint colour is the one before it.
    std::string Bad = SS::EncodeAccount(SS::Account{});
    const std::size_t HeroStart = Bad.find_last_of(' ');
    const std::size_t PaintStart = Bad.find_last_of(' ', HeroStart - 1);
    Bad.replace(HeroStart + 1, std::string::npos, "999");
    TestFalse(TEXT("A body past the roster is rejected"), SS::DecodeAccount(Bad, Decoded, Error));
    Bad = SS::EncodeAccount(SS::Account{});
    Bad.replace(HeroStart + 1, std::string::npos, "-2");
    TestFalse(TEXT("A body below the default is rejected"), SS::DecodeAccount(Bad, Decoded, Error));
    Bad = SS::EncodeAccount(SS::Account{});
    Bad.replace(PaintStart + 1, HeroStart - PaintStart - 1, "10");
    TestFalse(TEXT("Colour past the palette is rejected"), SS::DecodeAccount(Bad, Decoded, Error));
    Bad = SS::EncodeAccount(SS::Account{});
    Bad.replace(PaintStart + 1, HeroStart - PaintStart - 1, "-2");
    TestFalse(TEXT("Colour below the factory finish is rejected"), SS::DecodeAccount(Bad, Decoded, Error));
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
