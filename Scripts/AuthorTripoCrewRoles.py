"""Retarget each station role's clip set onto the crew members who play that role.

  UnrealEditor-Cmd.exe <project> -unattended -RenderOffscreen -stdout -FullStdOutLogOutput \
      -DisablePlugins=UAssetBrowser,NwiroIntegrationKit -ExecutePythonScript="<abs>/Scripts/AuthorTripoCrewRoles.py"

Batch retargeting needs a real RHI. Needs ImportTripoCrew.py + AuthorTripoCrew.py (crew meshes, IK_<Name> rigs,
RTG_<Name> from the UE4 mannequin) and ImportStationClipLibrary.py (OUT_LIB/<Library>/). Output per character:
TripoCrew/<Name>/Role/A_<Name>_<Clip>. SS_ROLES_ONLY=Merchant,Worker,... runs a subset.

Clip libraries come on three skeletons. UE4 mannequin (Merchant Vendor, MCO, Mobility) uses the crew's existing
RTG_<Name>. UE5 Manny (Paragon) and 3ds Max Biped (Bar Counter People) get a source IK rig here whose chains carry
the crew rigs' own chain names, so EXACT chain mapping works, and one RTG_<Name>_<Source> per crew member.

Casting is the owner's (2026-10-08): merchants and vendors at the main entrance and food stands; four-armed hauling
grunts who needle each other (not combat); bar-lounge dancers and flirts; a street performer; a bartender; desk
clerks at customer support and the main welcome desk; zero-G station maintenance; everyone else relaxed at the bar.
SS_ROLES_WHO=Dread,Silver limits a run to those cast members.
"""
import os

import unreal as u

CREW = "/Game/SpaceSurvival/Licensed/StationAssets/TripoCrew"
OUT_LIB = "/Game/SpaceSurvival/Licensed/StationAssets/ClipLibrary"
LIB = u.EditorAssetLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()


RIG_FOLDER = {"Kraken", "Abyss", "Ember", "Crest", "Olive", "Elf"}  # see ImportTripoCrew.py
EXTRA_MAP = {"Ember": {"LeftArmLower": "LeftArm", "RightArmLower": "RightArm"},  # four-armed: lower pair follows
             "Kraken": {"LeftArmTent": "LeftArm", "RightArmTent": "RightArm"}}  # her arms are tentacles


def mesh_path(who):
    return "%s/%s/%s/SK_%s" % (CREW, who, "Rig" if who in RIG_FOLDER else "Mesh", who)


def ue_chains(spine_end, neck_end):
    chains = {"Spine": ("spine_01", spine_end), "Neck": ("neck_01", neck_end), "Head": ("head", "head")}
    for side, word in (("l", "Left"), ("r", "Right")):
        chains[word + "Clavicle"] = ("clavicle_" + side, "clavicle_" + side)
        chains[word + "Arm"] = ("upperarm_" + side, "hand_" + side)
        chains[word + "Leg"] = ("thigh_" + side, "ball_" + side)
        for finger in ("thumb", "index", "middle", "ring", "pinky"):
            chains[word + finger.title()] = (finger + "_01_" + side, finger + "_03_" + side)
    return chains


def biped_chains(names):
    """Bip01 bones import as Bip01-L-UpperArm (dashes, not spaces); compare on letters and digits only."""
    import re
    key = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

    def find(want):
        hits = [n for n in names if key(n).endswith(key(want)) and key(n) == key(n)[:len(key(n))]]
        hits = [n for n in hits if key(n) == key(want)] or hits
        return hits[0] if len(hits) == 1 else None
    spine_end = find("Bip01 Spine3") or find("Bip01 Spine2")
    chains = {"Spine": (find("Bip01 Spine"), spine_end), "Neck": (find("Bip01 Neck"), find("Bip01 Neck")),
              "Head": (find("Bip01 Head"), find("Bip01 Head"))}
    for side, word in (("L", "Left"), ("R", "Right")):
        chains[word + "Clavicle"] = (find("Bip01 %s Clavicle" % side),) * 2
        chains[word + "Arm"] = (find("Bip01 %s UpperArm" % side), find("Bip01 %s Hand" % side))
        chains[word + "Leg"] = (find("Bip01 %s Thigh" % side), find("Bip01 %s Toe0" % side))
        for k, finger in enumerate(("Thumb", "Index", "Middle", "Ring", "Pinky")):
            chains[word + finger] = (find("Bip01 %s Finger%d" % (side, k)), find("Bip01 %s Finger%d2" % (side, k)))
    return {k: v for k, v in chains.items() if v[0] and v[1]}, find("Bip01 Pelvis"), find("Bip01")


SOURCES = {
    "UE4": {"mesh": "/Game/MCO_Mocap_Basics/Character/Mesh/SK_Mannequin", "rtg": "RTG_%s"},
    "Manny": {"mesh": "/Game/FreeAnimsMixPack/Demo/Mannequins/Meshes/SKM_Manny", "rtg": "RTG_%s_Manny",
              "rig": OUT_LIB + "/Rigs/IK_Source_Manny", "chains": lambda names: (ue_chains("spine_05", "neck_02"), "pelvis", "root")},
    "Biped": {"mesh": OUT_LIB + "/BarPeople/aa_bar_counter_people", "rtg": "RTG_%s_Biped",
              "rig": OUT_LIB + "/Rigs/IK_Source_Biped", "chains": biped_chains},
}

MERCHANT = ["AS_IdleBartering", "AS_PitchBarter_Lt", "AS_PitchBarter_Rt", "AS_ReactDeal",
            "AS_ShowBoothStart_Lt", "AS_ShowBoothLoop_Lt", "AS_ShowBoothStop_Lt", "AS_ShowBoothFull_Lt",
            "AS_ShowBoothStart_Rt", "AS_ShowBoothLoop_Rt", "AS_ShowBoothStop_Rt", "AS_ShowBoothFull_Rt",
            "AS_IdleFingerVarient_Lt", "AS_IdleFingerVarient_Rt", "AS_IdleBoredLean_Lt", "AS_IdleBoredLean_Rt",
            "AS_ActiveToBoredLean_Lt", "AS_ActiveToBoredLean_Rt", "AS_BoredToActive_LeanLt", "AS_BoredToActive_LeanRt",
            "AS_TalkStart", "AS_TalkLoop", "AS_TalkStop", "AS_TalkFull", "AS_TalkStartVarient2", "AS_TalkFullVarient2"]
MERCHANT_EMOTES = ["Emote_Browsing_M1", "Emote_Greeting", "Emote_FriendlyWave_M1", "Emote_IDK", "Emote_Waiting",
                   "Emote_Point", "Emote_Bow_M1", "Emote_GiveFlower_M1"]
WORKER_EMOTES = ["Emote_Taunt", "Emote_BringItOn", "Emote_ComeGetSome_T3", "Emote_TalkToHand", "Emote_ThrowDown",
                 "Emote_MonkeyTaunt", "Emote_Taunt_Shhh_T1", "Emote_Taunt_NoNoNo_T1", "Emote_Taunt_Nope",
                 "Emote_Taunt_WatchingYou_T1", "Emote_Laugh", "Emote_Taunt_BellyLaugh_T1", "Emote_Stomp_M2",
                 "Emote_Master_BackToWork_T3", "Emote_Spit", "Emote_Disappointed_Clap", "Emote_RaisedFist",
                 "Emote_Sleepy", "HitReact_Front", "HitReact_Front_A", "RMB_Push"]
# Flapper is out: the source floats tilted at both loop ends (found on Crystal, then on Silver)
DANCER_EMOTES = ["Emote_70sDance_Loop", "Emote_Dance_HulaHoop_T3", "Emote_Dance_Robot",
                 "Emote_Dance_SingleLadies_Loop", "Emote_Dance_SingleLadies_T1", "Emote_OooLaLa_T3",
                 "Emote_Taunt_FootSlide_T1", "Emote_Taunt_Curtsy_T1", "Emote_CantCatchMe_Loop", "Emote_WhoopWhoop_Loop",
                 "Emote_Celebration", "Emote_Bravo_Loop", "Emote_Indie", "Emote_Headphones", "Emote_GiveFlower_M1",
                 "Emote_Taunt_Shhh_T1", "Emote_Dab", "Emote_Taunt_PraiseMe_T1"]
LOUNGE_EMOTES = ["Emote_Laugh", "Emote_Laugh_T1", "Emote_BigClap", "Emote_Small_Clap_T1", "Emote_Bravo",
                 "Emote_ChillOut_T3", "Emote_Sleepy", "Emote_RoShamBo", "Emote_DeepBreath_Loop", "Emote_Sneeze",
                 "Emote_IDK", "Emote_Greeting", "Emote_FriendlyWave_M1", "Emote_WhoopWhoop", "Emote_Celebration",
                 "Emote_HooRah", "Emote_Waiting", "Emote_Meditate", "Emote_Guitar", "Emote_DrumSolo",
                 "Emote_EpicRiff_Loop", "Emote_Headphones"]
# Packs the owner added to the project on 2026-10-08 (all UE5 Manny, used in place: no import needed).
G = "/Game/"
WORKER_HAUL = [G + "Space_Crew_Animation/Animations/" + c for c in (
    "Cargo/AS_CarryBoxWalk_Medium", "Cargo/AS_CarryBoxRun_Medium", "Cargo/AS_PickItem_MidShelf_Medium",
    "Cargo/AS_PlaceBoxShelfMid_Medium", "Maintenance/AS_Carry_Toolbox", "Maintenance/Wrench/AS_Wrench_Start",
    "Maintenance/Wrench/AS_Wrench_Loop", "Computer/AS_Drag", "Computer/AS_Drag_Loop", "Zero-Gravity/AS_ZeroG_Carry_Object",
    "General_Worker/AS_Worker_Idle", "General_Worker/AS_Worker_Idle_Alert")]
# mild contact only, per the owner: "not a fighting game". The pack's choke, knockout and gun clips are left out.
WORKER_SCUFFLE = [G + "AbductionAnimPack/Animation/" + c for c in ("AS_Push", "AS_GrabandPull", "AS_ShoulderGrabfromBehind", "AS_BodyHaul")] +                  [G + "ExpressiveGestures/Animation/" + c for c in ("AS_Fuming", "AS_ShakeFist", "AS_FingerWag", "AS_Disapproval")]
MERCHANT_DEAL = [G + "ExpressiveGestures/Animation/" + c for c in (
    "AS_HandShake", "AS_SteeplingFingers", "AS_HandsRaisedRefusal", "AS_ThumbsUp", "AS_Yes", "AS_NoNoGesture",
    "AS_InstructionalPoint", "AS_ExcitedHello")]
DANCE_CLUB = [G + "VarietyDanceAnims/Animations/InPlace/" + c for c in (
    "AS_ClubDance", "AS_ClubDance2", "AS_PartyDance", "AS_PartyDance3", "AS_FunnyDance", "AS_SimpleDance", "AS_PJ_Dance")] +              [G + "RitualDanceAnims/Animations/" + c for c in ("AS_DancingWithTambourine", "AS_Drummer", "AS_Drummer2")] +              [G + "ExpressiveGestures/Animation/" + c for c in ("AS_FingerHeart", "AS_ExcitedHello")]
DANCE_SENSUAL = [G + "VarietyDanceAnims/Animations/InPlace/AS_StripDance" + k for k in ("", "2", "3", "4", "5")] +                 [G + "SensualMoves/Animation/AS_Dance%d" % k for k in range(1, 11)] +                 [G + "SensualMoves2/Animation/AS_Dance%d" % k for k in range(1, 11)]
LOUNGE_EXTRA = [G + "RitualDanceAnims/Animations/AS_SittingInTrance"] +                [G + "ExpressiveGestures/Animation/" + c for c in ("AS_ThumbsUp", "AS_Yes", "AS_FingerHeart", "AS_ExcitedHello")]
# Crystal is an artistic street performer, not a sensual or club dancer (owner, 2026-10-08). 37 passed a
# two-judge visual casting (third judge on splits) over 67 rendered candidates; rejected: club/party grooves,
# plain gestures, and three flagged flirty (Single Ladies, Ooo La La, Give Flower). A retarget QA pass then
# dropped six: Guitar, StaffSpin and MarchingBand mime a prop she does not hold (they read as stalking or
# clutching - revisit with a prop on the hand socket), InTrance is a near-still crouch, Flapper floats tilted at
# both loop ends, and ShamanCastsSpells2's head roll folds her heavy crown onto her shoulder like a broken neck.
PERFORMER_PARAGON = ["Emote_Backspin", "Emote_BowBalance_T1", "Emote_Bow_M1",
                     "Emote_Dance_HulaHoop_T3", "Emote_Dance_Robot", "Emote_DrumSolo", "Emote_EpicRiff_Loop",
                     "Emote_FlippingAround_T3", "Emote_Handstand_T3", "Emote_Ice_Sculpture",
                     "Emote_Ice_Sculpture_Pose", "Emote_JumpRope", "Emote_Master_Levitate_T3", "Emote_Meditate",
                     "Emote_Skywalk_Loop", "Emote_Steelamania", "Emote_SwordSwallow", "Emote_Taunt_Curtsy_T1"]
PERFORMER_PROJECT = [G + "RitualDanceAnims/Animations/" + c for c in (
    "AS_DanceInTrance", "AS_DancingWithTambourine", "AS_Drummer", "AS_Drummer2", "AS_RitualDance",
    "AS_RitualDance2", "AS_RitualDance3", "AS_RitualDance4", "AS_RitualDance5", "AS_ShamaWnithStaff",
    "AS_ShamanCastsSpells", "AS_ShamanDance")] +     [G + "VarietyDanceAnims/Animations/InPlace/AS_FunnyDance"]
# Dread runs the bar (owner: "social butterfly, cocktail master"). The pack's ten bartender takes are the same
# source the 2026-10-06 female-bartender trial in OutpostSandbox/StationRefinement retargeted (Type01-03); no pack
# here has a STANDING drink or toast, so "takes drinks with guests" has no clip yet.
BAR_BARTENDER = ["aa_bar_counter_people_Anim_AA_Bar_Counter_Bartender_Type%02d" % i for i in range(1, 11)]
BARTENDER_SOCIAL = ["Emote_Greeting", "Emote_FriendlyWave_M1", "Emote_Laugh", "Emote_Laugh_T1", "Emote_BigClap",
                    "Emote_Small_Clap_T1", "Emote_Bravo", "Emote_Celebration", "Emote_HooRah", "Emote_WhoopWhoop",
                    "Emote_IDK", "Emote_RoShamBo"]  # not ChillOut (lies on the floor) or Waiting (squat): she is behind a bar
BARTENDER_GESTURES = [G + "ExpressiveGestures/Animation/" + c for c in (
    "AS_ThumbsUp", "AS_Yes", "AS_FingerHeart", "AS_ExcitedHello", "AS_HandShake")]
# Seer and Tendril staff the customer-support desks and the main welcome desk: lean on the counter, talk a
# visitor through it, point the way, work the terminal, scan an ID.
DESK_TALK = ["AS_TalkStart", "AS_TalkLoop", "AS_TalkStop", "AS_TalkFull", "AS_TalkStartVarient2", "AS_TalkFullVarient2",
             "AS_IdleFingerVarient_Lt", "AS_IdleFingerVarient_Rt", "AS_IdleBoredLean_Lt", "AS_IdleBoredLean_Rt",
             "AS_ActiveToBoredLean_Lt", "AS_ActiveToBoredLean_Rt", "AS_BoredToActive_LeanLt", "AS_BoredToActive_LeanRt",
             "AS_ReactDeal", "AS_ShowBoothFull_Lt", "AS_ShowBoothFull_Rt"]
DESK_EMOTES = ["Emote_Greeting", "Emote_FriendlyWave_M1", "Emote_Bow_M1", "Emote_IDK", "Emote_Point"]  # no squat at a desk
DESK_WORK = [G + "Space_Crew_Animation/Animations/" + c for c in (
    "Computer/AS_Click", "Computer/AS_Click_Loop", "Computer/AS_PressKeys", "Computer/AS_PressKeys_Loop",
    "Computer/AS_PressKeys_Fast", "Computer/AS_PressKeys_OneHand_Loop", "Computer/AS_ReadCodes_Loop",
    "Computer/AS_Drag_Loop", "Maintenance/biometric_scanner/AS_Hand_Scanner_1_Loop",
    "Maintenance/keypad/AS_Keypad_Clicks")] + \
    [G + "ExpressiveGestures/Animation/" + c for c in (
        "AS_HandShake", "AS_InstructionalPoint", "AS_Yes", "AS_NoNoGesture", "AS_ThumbsUp", "AS_SteeplingFingers",
        "AS_ExcitedHello", "AS_HandsRaisedRefusal")]
# Warden is station maintenance (owner: a zero-G pack bought for the role - walk the deck, float out, repair).
# That pack is Space_Crew_Animation: its Zero-Gravity set plus the grounded Maintenance and Computer clips.
ZG = G + "Space_Crew_Animation/Animations/Zero-Gravity/"
MAINT_ZEROG = [ZG + c for c in (
    "AS_ZeroG_Float_Idle", "AS_ZeroG_Move_Forward", "AS_ZeroG_Push_Off_Wall", "AS_ZeroG_Grab_Railing",
    "AS_ZeroG_Release_Railing", "AS_ZeroG_Carry_Object", "AS_ZeroG_Catch_Object",
    "Maintainance/AS_ZeroG_Wrench_Start", "Maintainance/AS_ZeroG_Wrench_Loop", "Maintainance/AS_ZeroG_Wrench_End",
    "Maintainance/AS_ZeroG_Wrench_Start_2", "Maintainance/AS_ZeroG_Wrench_Loop_2", "Maintainance/AS_ZeroG_Wrench_End_2",
    "Maintainance/FuseBox/AS_FuseBox_Open", "Maintainance/FuseBox/AS_FuseBox_Swich_Off",
    "Maintainance/FuseBox/AS_FuseBox_Swich_On", "Maintainance/KeyPad/AS_KeyPad_Click",
    "Maintainance/KeyPad/AS_KeyPad_Click_Loop")]
MAINT_GROUND = [G + "Space_Crew_Animation/Animations/" + c for c in (
    "Maintenance/AS_Carry_Toolbox", "Maintenance/Box/AS_Box_Punch_Enter", "Maintenance/Box/AS_Box_Punch_Loop",
    "Maintenance/Box/AS_Box_Punch_Exit", "Maintenance/Wrench/AS_Wrench_Start", "Maintenance/Wrench/AS_Wrench_Loop",
    "Maintenance/biometric_scanner/AS_Hand_Scanner_1", "Maintenance/biometric_scanner/AS_Hand_Scanner_1_Loop",
    "Maintenance/biometric_scanner/AS_Hand_Scanner_2", "Maintenance/biometric_scanner/AS_Hand_Scanner_2_Loop",
    "Maintenance/keypad/AS_Keypad_Clicks", "Computer/AS_ReadCodes_Loop", "Computer/AS_PressKeys_Loop",
    "General_Worker/AS_Worker_Idle", "General_Worker/AS_Worker_Idle_Alert", "General_Worker/AS_Worker_Turn_Left",
    "General_Worker/AS_Worker_Turn_Right", "General_Worker/AS_Worker_Walk_Forward")]
# Olive is station security (owner): "not military style" - patrols, stands guard at the docks and landing pads,
# and hassles the scrapping four-armed workers back into line. So authority gestures, ID checks and a pull-apart,
# no salutes, weapons or takedowns. Walking the beat uses the base clips (Walk, WalkLookAround, LookL/R, Turn).
SECURITY_EMOTES = ["Emote_Point", "Emote_Master_BackToWork_T3", "Emote_TalkToHand", "Emote_Taunt_NoNoNo_T1",
                   "Emote_Taunt_Shhh_T1", "Emote_Taunt_WatchingYou_T1", "Emote_Disappointed_Clap", "Emote_ComeHere",
                   "Emote_Taunt_CrossTheLine_T2", "Emote_Greeting"]
SECURITY_PROJECT = [G + "ExpressiveGestures/Animation/" + c for c in (
    "AS_FingerWag", "AS_Disapproval", "AS_InstructionalPoint", "AS_HandsRaisedRefusal", "AS_NoNoGesture")] + \
    [G + "AbductionAnimPack/Animation/" + c for c in ("AS_GrabandPull", "AS_ShoulderGrabfromBehind")] + \
    [G + "Space_Crew_Animation/Animations/" + c for c in (
        "General_Worker/AS_Worker_Idle_Alert", "General_Worker/AS_Worker_Turn_Left", "General_Worker/AS_Worker_Turn_Right",
        "Maintenance/biometric_scanner/AS_Hand_Scanner_1_Loop", "Maintenance/biometric_scanner/AS_Hand_Scanner_2_Loop",
        "Computer/AS_ReadCodes_Loop")]
# Kraken waits tables and checks on guests (owner: one or two on the whole station at most). Only her humanoid
# upper body takes these; Scripts/AuthorTripoCrewTentacleBlend.py then puts her own tentacle crawl, turns and idle
# back under every clip, so she never walks on borrowed human legs.
WAITRESS_PROJECT = [G + "Space_Crew_Animation/Animations/" + c for c in (
    "Cargo/AS_CarryBoxWalk_Medium", "Cargo/AS_PickItem_MidShelf_Medium", "Cargo/AS_PlaceBoxShelfMid_Medium",
    "Maintenance/AS_Carry_Toolbox", "General_Worker/AS_Worker_Idle")] + \
    [G + "ExpressiveGestures/Animation/" + c for c in (
        "AS_Yes", "AS_ThumbsUp", "AS_ExcitedHello", "AS_InstructionalPoint", "AS_FingerHeart")]
WAITRESS_EMOTES = ["Emote_Greeting", "Emote_FriendlyWave_M1", "Emote_Waiting", "Emote_IDK", "Emote_Laugh",
                   "Emote_Small_Clap_T1", "Emote_Bow_M1"]
PACK_TAG = {"Space_Crew_Animation": "Crew", "AbductionAnimPack": "Scuffle", "VarietyDanceAnims": "Dance",
            "RitualDanceAnims": "Ritual", "ExpressiveGestures": "Gesture", "SensualMoves": "Sensual",
            "SensualMoves2": "Sensual2"}

BAR_CUSTOMERS = ["aa_bar_counter_people_Anim_AA_Bar_Counter_Customer_Type%02d" % i for i in range(1, 36)]

ROLES = {
    "Merchant": {"cast": ["Robe", "Glyph", "Tribal"],
                 "sets": [("UE4", "Merchant", MERCHANT), ("Manny", "Paragon", MERCHANT_EMOTES),
                          ("Manny", "Project", MERCHANT_DEAL)]},
    "Worker": {"cast": ["Ember", "Crest"], "sets": [("Manny", "Paragon", WORKER_EMOTES),
                                                    ("Manny", "Project", WORKER_HAUL + WORKER_SCUFFLE)]},
    "Dancer": {"cast": ["Violet", "Cyan", "Silver", "Elf", "Cyborg"], "sets": [("Manny", "Paragon", DANCER_EMOTES),
                                                               ("Manny", "Project", DANCE_CLUB)]},
    "Performer": {"cast": ["Crystal"], "sets": [("Manny", "Paragon", PERFORMER_PARAGON),
                                                ("Manny", "Project", PERFORMER_PROJECT)]},
    # the owner: Cyan "a bit more adult themed, more passionate like a stripper style" - bar lounge only.
    # Elf and Cyborg (2026-10-08) are multi-role base bodies built for dancing, incl. an adult-nightclub option;
    # dancing and entertainment only (owner), outfits come later as separate meshes on the same rig.
    "Flirt": {"cast": ["Cyan", "Elf", "Cyborg"], "sets": [("Manny", "Project", DANCE_SENSUAL)]},
    "Bartender": {"cast": ["Dread"], "sets": [("Biped", "BarPeople", BAR_BARTENDER), ("Manny", "Paragon", BARTENDER_SOCIAL),
                                              ("Manny", "Project", BARTENDER_GESTURES)]},
    "Desk": {"cast": ["Seer", "Tendril"], "sets": [("UE4", "Merchant", DESK_TALK), ("Manny", "Paragon", DESK_EMOTES),
                                                   ("Manny", "Project", DESK_WORK)]},
    "Maintenance": {"cast": ["Warden"], "sets": [("Manny", "Project", MAINT_ZEROG + MAINT_GROUND)]},
    "Waitress": {"cast": ["Kraken"], "sets": [("Manny", "Paragon", WAITRESS_EMOTES), ("Manny", "Project", WAITRESS_PROJECT)]},
    "Security": {"cast": ["Olive"], "sets": [("Manny", "Paragon", SECURITY_EMOTES), ("Manny", "Project", SECURITY_PROJECT)]},
    "Lounge": {"cast": ["Finhead", "Amethyst", "Elf", "Cyborg"],
               "sets": [("Manny", "Paragon", LOUNGE_EMOTES), ("Biped", "BarPeople", BAR_CUSTOMERS),
                        ("Manny", "Project", LOUNGE_EXTRA)]},
}


def out_name(path):
    """Full-path clips get their pack's short tag: SensualMoves and SensualMoves2 both ship AS_Dance1..10."""
    pack = path.split("/")[2] if path.startswith("/Game/") else None
    base = clean(path.rsplit("/", 1)[1])
    return "%s_%s" % (PACK_TAG[pack], base) if pack in PACK_TAG else base


def clean(name):
    """Output names: A_<Who>_IdleBartering, A_<Who>_Emote_Laugh, A_<Who>_BarCustomer_Type07."""
    return name.replace("aa_bar_counter_people_Anim_AA_Bar_Counter_", "Bar").replace("AS_", "", 1)         if name.startswith(("AS_", "aa_bar")) else name


def line(s):
    u.log_warning("ROLES| " + str(s))


def bone_names(mesh):
    mod = u.SkeletonModifier()
    mod.set_skeletal_mesh(mesh)
    return [str(n) for n in mod.get_all_bone_names()]


def source_rig(key, spec):
    path = spec["rig"]
    mesh = LIB.load_asset(spec["mesh"])
    if mesh is None:
        return None, None
    folder, name = path.rsplit("/", 1)
    if not LIB.does_directory_exist(folder):
        LIB.make_directory(folder)
    rig = LIB.load_asset(path) if LIB.does_asset_exist(path) else \
        TOOLS.create_asset(name, folder, u.IKRigDefinition, u.IKRigDefinitionFactory())
    c = u.IKRigController.get_controller(rig)
    c.set_skeletal_mesh(mesh)
    for chain in list(c.get_retarget_chains()):
        c.remove_retarget_chain(chain.get_editor_property("chain_name"))
    chains, root, motion = spec["chains"](bone_names(mesh))
    c.set_retarget_root(root)
    if motion:
        c.set_root_motion_bone(motion)
    for chain, (a, b) in chains.items():
        c.add_retarget_chain(chain, a, b, "None")
    LIB.save_loaded_asset(rig, only_if_is_dirty=False)
    line("source rig %s: %d chains, root %s" % (key, len(chains), root))
    return rig, mesh


def retargeter(who, key, src_rig, src_mesh, mesh):
    path = "%s/%s/%s" % (CREW, who, SOURCES[key]["rtg"] % who)
    if key == "UE4":
        return LIB.load_asset(path)
    rebuild = who in os.environ.get("SS_ROLES_REBUILD_RTG", "").split(",")
    if LIB.does_asset_exist(path) and not rebuild:
        return LIB.load_asset(path)
    if LIB.does_asset_exist(path):
        LIB.delete_asset(path)
    tgt_rig = LIB.load_asset("%s/%s/IK_%s" % (CREW, who, who))
    if tgt_rig is None:
        return None
    folder, name = path.rsplit("/", 1)
    rtg = TOOLS.create_asset(name, folder, u.IKRetargeter, u.IKRetargetFactory())
    c = u.IKRetargeterController.get_controller(rtg)
    src, tgt = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
    c.set_ik_rig(src, src_rig); c.set_preview_mesh(src, src_mesh)
    c.set_ik_rig(tgt, tgt_rig); c.set_preview_mesh(tgt, mesh)
    c.add_default_ops()
    c.assign_ik_rig_to_all_ops(src, src_rig)
    c.assign_ik_rig_to_all_ops(tgt, tgt_rig)
    c.auto_map_chains(u.AutoMapChainType.EXACT, True)
    for target_chain, source_chain in EXTRA_MAP.get(who, {}).items():
        c.set_source_chain(source_chain, target_chain)
    pose = c.create_retarget_pose(who + key + "Aligned", tgt)
    c.set_current_retarget_pose(pose, tgt)
    c.auto_align_all_bones(tgt, u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN)
    LIB.save_loaded_asset(rtg, only_if_is_dirty=False)
    return rtg


def main():
    only = os.environ.get("SS_ROLES_ONLY")
    only_source = os.environ.get("SS_ROLES_SOURCE")  # e.g. Biped: rerun just one source family
    only_library = os.environ.get("SS_ROLES_LIBRARY")  # e.g. Project: just the packs added in Content/
    who_only = [w for w in os.environ.get("SS_ROLES_WHO", "").split(",") if w]
    touched = set()
    registry = u.AssetRegistryHelpers.get_asset_registry()
    # SS_ROLES_PRUNE=Crystal: clear that character's Role/ first, so a recast leaves no clips from the old role
    for who in [w for w in os.environ.get("SS_ROLES_PRUNE", "").split(",") if w]:
        gone = sum(1 for p in LIB.list_assets("%s/%s/Role" % (CREW, who), recursive=False, include_folder=False)
                   if LIB.delete_asset(p.split(".")[0]))
        line("pruned %d old role clips from %s" % (gone, who))
    rigs = {"UE4": (None, LIB.load_asset(SOURCES["UE4"]["mesh"]))}
    for role, spec in ROLES.items():
        if only and role not in only.split(","):
            continue
        for key, library, clips in spec["sets"]:
            if only_source and key != only_source:
                continue
            if key not in rigs:
                rigs[key] = source_rig(key, SOURCES[key])
            src_rig, src_mesh = rigs[key]
            if src_mesh is None:
                line("%s: source %s not imported yet (%s) - skipped" % (role, key, SOURCES[key]["mesh"]))
                continue
            if only_library and library not in only_library.split(","):
                continue
            lib = "%s/%s" % (OUT_LIB, library) if library not in (None, "Project") else ""
            datas = []
            for clip in clips:
                path = clip if clip.startswith("/Game/") else "%s/%s" % (lib, clip)
                d = registry.get_asset_by_object_path("%s.%s" % (path, path.rsplit("/", 1)[1]))
                if d.is_valid():
                    datas.append((d, out_name(path)))
                else:
                    line("%s: missing %s/%s" % (role, library, clip))
            for who in spec["cast"]:
                if who_only and who not in who_only:
                    continue
                mesh = LIB.load_asset(mesh_path(who))
                rtg = retargeter(who, key, src_rig, src_mesh, mesh) if mesh else None
                if not (mesh and rtg):
                    line("%s: %s has no mesh or retargeter for %s" % (role, who, key))
                    continue
                dest = "%s/%s/Role" % (CREW, who)
                if not LIB.does_directory_exist(dest):
                    LIB.make_directory(dest)
                made = 0
                for d, name in datas:
                    inputs = u.IKRetargetBatchOperationInputs()
                    for prop, value in (("assets_to_retarget", [d]), ("source_mesh", src_mesh), ("target_mesh", mesh),
                                        ("ik_retarget_asset", rtg), ("search", str(d.asset_name)),
                                        ("replace", name), ("prefix", "A_%s_" % who), ("suffix", ""),
                                        ("target_path", dest), ("use_source_path", False),
                                        ("include_referenced_assets", False), ("overwrite_existing_files", True)):
                        inputs.set_editor_property(prop, value)
                    if u.IKRetargetBatchOperation.run_batch_retarget(inputs):
                        made += 1
                        touched.add(who)
                LIB.save_directory(dest, only_if_is_dirty=False, recursive=True)
                line("%-9s %-8s %-10s %2d / %2d clips" % (role, who, library or "project", made, len(datas)))
    if os.environ.get("SS_POST", "1") != "0" and touched:
        # tail / tentacle / hair bakes: a retarget writes those bones at rest and would silently undo them
        import runpy
        runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "AuthorTripoCrewPost.py"),
                       run_name="tripo_post")["run"](sorted(touched))
    line("DONE")


main()
