import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Local review page; links original captures without editing their pixels."""
from pathlib import Path
from html import escape
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025'
def shot(path,label):
 assert path.is_file(),path
 return f'<figure><a href="{path.as_uri()}"><img src="{path.as_uri()}" alt="{escape(label)}"></a><figcaption>{escape(label)}</figcaption></figure>'
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Leg deformation review</title><style>body{max-width:1250px;margin:40px auto;padding:0 24px;background:#111820;color:#e8eff7;font:17px/1.5 system-ui}h1{font-size:34px}h2{margin-top:45px}.tag{color:#ffd187}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}figure{margin:0}img{width:100%;display:block}figcaption{padding:10px 0;color:#b9c7d7}video{width:min(100%,640px);max-height:80vh}a{color:#98d9ec}.note{border-left:3px solid #edb55d;padding-left:15px}</style><h1>Hip, thigh and knee review</h1><p class="tag">October 25 · Private candidate · Not adopted in game</p><p>The earlier curled hip silhouette is owner-approved. The open knee and thigh were rejected. This separate candidate aligns the native thigh/knee bend axes and rebuilds the hip correction for the changed pose.</p><p class="note">No claim of finished choreography or four-character acceptance. The original assets and approved hip proof remain unchanged.</p><h2>Open-knee comparison</h2><div class="grid">'''
intro='''<h2>Current target: Vexa</h2><p>Saved pink/purple-haired Eden is the sole active repair target. The other body proofs below are historical comparisons. All four characters share the body geometry, topology, weights, shape geometry and rest rig; outfits still need individual checks.</p><p class="note">Owner feedback: “much more normal.” Preserve this shoulder improvement as a baseline; this is not acceptance of the complete routine, knees, hands or native shading. These grey diagnostic views intentionally do not evaluate skin/hair materials.</p><div class="grid">'''
intro+=shot(R/'VexaFullShoulderReview/9.03333_front_source.png','Vexa before · full source assembly')
intro+=shot(R/'VexaFullShoulderReview/9.03333_front_supported.png','Vexa candidate · clavicle support and local shoulder volume')
intro+=shot(R/'VexaFullShoulderReview/9.03333_back_supported.png','Vexa candidate · opposite side')
intro+='</div><h2>Vexa through motion</h2><p>Saved candidate reopened and rendered through the whole 16-second Spiral. Temporary forearm markers remain. Hand positions change with the clavicle correction; this is not a fixed-pole contact solution.</p><video controls loop preload="metadata" src="Vexa_Shoulder_MotionReview.mp4"></video><h2>Earlier knee investigation — still unaccepted</h2>'
current='''<h2>Current Vexa: shoulder balance and nape</h2><p class="tag">Private proof 844aae5f · Original rig retained · Not adopted in Unreal</p><p>The owner liked the improved front angle and asked for consistent behavior on both sides. Matched-pose tests found asymmetric original weights. The better shoulder weights are transferred within a protected region; clavicles now follow the rewritten arm poses.</p><p>The sharp back-of-neck notch is reduced by smoothing only its weights across the paired head/body join. The front and distant shoulder regions are excluded from this new adjustment. This is a candidate, not final anatomy or animation acceptance.</p><h3>Same pose and lighting: nape before / after</h3><div class="grid">'''
current+=shot(R/'VexaNape/baseline_543_back.png','Before local nape weights · CPU render')
current+=shot(R/'VexaNape/weights_543_back.png','After local nape weights · CPU render')
current+='</div><h3>Saved candidate reopened</h3><div class="grid">'
current+=shot(R/'VexaNape/Reload/9.03333_front.png','Current front · improved shape retained')
current+=shot(R/'VexaNape/Reload/9.03333_back.png','Current back · inspect neck and both shoulders')
current+=shot(R/'VexaNape/Reload/4_back.png','Earlier overhead pose · opposing view')
current+=shot(R/'VexaNape/Reload/12.2_back.png','Later opening pose · opposing view')
current+='</div><h3>CPU motion preview</h3><p>12fps preview for low VRAM use; not a final pacing assessment. Hair is hidden and clay shading is diagnostic. No textures were changed in the original character.</p><video controls loop preload="metadata" src="Vexa_ShoulderBalanced_Back_CPU.mp4"></video><p><a href="Vexa_ShoulderBalanced_Proof.blend">Open the private Blender proof</a>. Lead checks still open: continuous shoulder/neck quality, garment contact, native influence budget and playback, remaining knees/thighs and pole grips. Work stays on Vexa before reuse on other dancers.</p>'
native='''<h3>Saved Unreal proof - October 25</h3><p>The same Blender candidate now reloads in the isolated native workbench. The sampled live surface differs by at most 0.303 mm; all 65 correction curves are present. Ten-weight regions remain present in the component mesh readback. This is bounded geometry evidence, not production or artistic acceptance.</p><div class="grid">'''
for name,label in [('9.033333_front.png','Unreal - body-relative front'),('9.033333_back.png','Unreal - opposing shoulder and nape'),('12.2_side.png','Unreal - later raised-arm side')]:
 native+=shot(R/'NativeVexaBalancedCleanViews'/name,label)
native+='</div><p>Hair is excluded only from this private diagnostic import. These views use a signed normal ramp; the earlier absolute-normal material created artificial dark bands and is not used for visual judgment.</p>'
if (D/'Vexa_ShoulderBalanced_Front.mp4').exists() and (D/'Vexa_ShoulderBalanced_Back.mp4').exists():
 native+='<h3>Current candidate at 24 fps - Blender</h3><div class="grid"><video controls loop preload="metadata" src="Vexa_ShoulderBalanced_Front.mp4"></video><video controls loop preload="metadata" src="Vexa_ShoulderBalanced_Back.mp4"></video></div><p>Same saved proof, 16-second motion, opposing cameras; this is source playback, not a captured game or final routine.</p>'
native+='<h3>Current candidate at 24 fps - Unreal</h3><div class="grid"><video controls loop preload="metadata" src="Vexa_ShoulderBalanced_Native_front.mp4"></video><video controls loop preload="metadata" src="Vexa_ShoulderBalanced_Native_back.mp4"></video></div><p>768 saved native frames, two 16-second views. Cameras follow the body; this is a deformation check, not a choreography or performance sign-off. The brightest frame changes were checked and follow camera rotation rather than a broken arm.</p>'
current=current.replace('Not adopted in Unreal','Private Unreal proof; not adopted in game').replace('native influence budget and playback','continuous native playback and garment appearance')+native
color='<h2 id="color">Does colour hide the remaining fold?</h2><p>Same unchanged shoulder proof, pose, camera and light positions. Existing packed character textures replace clay; pink/blue lighting is a separate control. The fold still catches a highlight: colour softens its appearance but does not repair it. Hair is hidden equally so it cannot cover the shoulder. Blender shaders approximate the imported Unreal materials; these are not final game lighting.</p>'
for sec in ('9.03333','4'):
 color+='<div class="grid">'
 for style,label in [('clay_neutral','Clay / neutral light'),('texture_neutral','Existing textures / neutral light'),('texture_bar','Existing textures / pink and blue light')]:
  color+=shot(R/'VexaColorComparison'/f'{sec}_{style}.png',label+' / '+sec+' seconds')
 color+='</div>'
color+='<h3>Separate local refinement — same textures and lighting</h3><p>The shoulder baseline above is unchanged. This additional candidate softens only the underarm region with baked corrections; the neck, bones and original weights are retained. Its transfer into the private Unreal workbench is verified; full-motion and game appearance acceptance remain open.</p><div class="grid">'
color+=shot(R/'VexaColorComparison/9.03333_texture_neutral.png','Preserved baseline / remaining sharp fold')
color+=shot(R/'VexaAxillaColor/9.03333_texture_neutral.png','Local refinement / same pose and neutral light')
color+=shot(R/'VexaAxillaColor/9.03333_texture_bar.png','Local refinement / pink and blue light')
color+='</div><p>Owner feedback: the shown side is acceptable and a massive improvement. This is narrow appearance approval; opposing and moving poses remain separate checks.</p>'
color+='<div class="grid"><video controls loop preload="metadata" src="Vexa_AxillaLocal_Front.mp4"></video><video controls loop preload="metadata" src="Vexa_AxillaLocal_Back.mp4"></video></div><p>Local correction candidate 1f677227: 24 fps Blender deformation previews, 16-second action plus endpoint. These are separate from the earlier native baseline videos below.</p>'
color+='<h3>Opposing views of the local candidate</h3><div class="grid">'
color+=shot(R/'VexaAxillaOpposing/9.03333_opposite.png','Opposite side / same local correction candidate')
color+=shot(R/'VexaAxillaOpposing/12.2_back.png','Back / unequal arm elevation and tilted head')
color+='</div><p>The owner noted back-view differences, then clarified that the unequal arm/head pose can account for some difference and that the sides are generally very close. No symmetry-driven reshaping was applied after that clarification.</p>'
color+='<h3>Local refinement in Unreal</h3><p>The same saved 1f677227 proof reloads with all 89 correction curves. Five sampled surfaces match Blender within 0.303 mm. The two videos below each contain 384 native frames at 24 fps. Diagnostic shading and body-following cameras do not establish final game presentation or choreography acceptance.</p><div class="grid"><video controls loop preload="metadata" src="Vexa_AxillaLocal_Native_front.mp4"></video><video controls loop preload="metadata" src="Vexa_AxillaLocal_Native_back.mp4"></video></div>'
color+='<h2 id="joints">Wrist and ankle inspection</h2><p>This shoulder-proof clip holds both wrists at their rest-relative orientation, so it does not demonstrate wrist flexion. The bent right ankle shows a visible contour/lighting discontinuity. Measured ankle and wrist join vertices remain together within 0.0013 mm at seven sampled poses; this is not a detached foot or hand. Averaging boundary normals did not repair the appearance. The thumb web also has visible spikes requiring further diagnosis.</p><div class="grid">'
color+=shot(R/'VexaEndJoints/foot_r_11.9667_front.png','Right ankle at strongest sampled rotation — unresolved visible join')
color+=shot(R/'VexaEndJoints/foot_l_4_front.png','Left ankle — comparison at 4 seconds')
color+=shot(R/'VexaEndJoints/hand_r_4_front.png','Right wrist and thumb web — not a wide-range wrist test')
color+='</div><p>Original assets and shoulder proof remain unchanged. Knees/thighs, fingers, garment contact and wider joint-range checks remain open.</p>'
color+='<h3>Dedicated range probes — not a gold-standard rig</h3><p>Twenty-four isolated cases produce 48 opposing views of wrist flexion/deviation, forearm twist and ankle pitch/roll. They expose remaining wrist/ankle contour defects. The angles below are diagnostic samples, not approved anatomical limits. A passing pose or this one clip cannot validate another character or a hand locked to a pole while the body rotates.</p><div class="grid">'
for name,label in [('hand_r_flex_+30_front.png','Wrist flexion probe — visible joint contour'),('hand_l_flex_-30_side.png','Opposite wrist flexion probe'),('foot_r_pitch_+30_side.png','Ankle pointing probe'),('foot_r_roll_+15_side.png','Ankle roll probe')]:
 color+=shot(R/'VexaJointStress'/name,label)
color+='</div><p>Remaining acceptance requires whole moving routines after retargeting, torso-relative arm limits, wrist/ankle and finger shape, grip changes and reachable pole contact on each distinct character. These probes do not alter or save the source proof.</p>'
latest='''<h2 id="distal-repair">Current Vexa: thumb, wrist and ankle repair</h2><p class="tag">Private mesh d70f17f7 · 95 original bones · Not adopted in game</p><p>Eight hand vertices incorrectly followed the pelvis. Removing that influence eliminates the sampled thumb spikes. The wrist and ankle boundary vertices were already attached; joining only the 40 wrist and 44 ankle pairs allows continuous surface normals. Originals remain hidden and intact in the editable proof. No broad geometry merge or new helper bones were adopted.</p><div class="grid">'''
latest+=shot(R/'VexaDistalRepair/thumb_r_before_front.png','Before: thumb web follows the pelvis')
latest+=shot(R/'VexaDistalRepair/thumb_r_after_front.png','After: only the contaminated hand weights changed')
latest+='</div><h3>Fresh native range checks</h3><p>24 diagnostic cases, 48 native views: bilateral wrist flexion/deviation, forearm twist and ankle pitch/roll. Sampled surface transfer matches Blender within 0.303 mm. These are bounded inspection angles, not anatomical certification. Feet, fingers, extreme ranges and whole routines remain under review.</p><div class="grid">'
for filename,label in [('6.5_hand_l_front.png','Wrist deviation'),('20.5_hand_l_side.png','Forearm twist and thumb'),('18.5_foot_l_side.png','Ankle roll — outside view'),('34.5_foot_r_side.png','Bent ankle — outside view')]:
 latest+=shot(R/'NativeVexaContinuousDistalFullRangeViews'/filename,label)
latest+='</div><h3>G/B wrist discontinuity repair</h3><p>A full 4,566-frame screen found near-80-degree wrist jumps in G1, G2 and B1. The candidate reduces wrist steps below 5 degrees per 60-fps frame; B2 needs no change. Other local joint keys remain unchanged. This does not resolve other rapid motion, pole grips or choreography. The original source and derivative libraries remain separate; Spiral-only shape curves are disabled when testing G/B clips.</p>'
videos=R/'VexaDistalRepair/NativeGBWristVideos.json'
if videos.is_file():
 import json
 receipt=json.loads(videos.read_text())
 latest+='<p>Matched native captures, same Vexa and camera. Each wrist excerpt lasts 1.6 seconds; it is not a loopable dance segment.</p><div class="grid">'
 for name,label in [('g1_978_before','G1 before — wrist discontinuity'),('g1_978_after','G1 after — continuous wrist track')]:
  latest+=f'<figure><video controls preload="metadata" src="Vexa_Wrist_{name}.mp4"></video><figcaption>{label}</figcaption></figure>'
 latest+='</div><h3>Complete G1 candidate in Unreal</h3><video controls preload="metadata" src="Vexa_Wrist_g1_whole_after.mp4"></video><p>This is the unconstrained source-derived motion on Vexa, without a pole. Remaining abrupt upper-arm/leg movement and imperfect skin contours are not hidden by the wrist repair. All character, contact and owner acceptance stays open.</p>'
intro=latest+'<details><summary>Earlier shoulder and distal diagnostics — retained history</summary>'+color+current+'</details>'+'<details><summary>Earlier shoulder controls — superseded, retained for comparison</summary>'+intro.replace('<h2>Current target: Vexa</h2>','<h2>Earlier Vexa baseline</h2>')+'</details>'
page=page.replace('<title>Leg deformation review</title>','<title>Vexa shoulder balance</title>').replace('<h1>Hip, thigh and knee review</h1>','<h1>Vexa deformation review</h1>')
page=page.replace('<p>The earlier curled hip silhouette is owner-approved. The open knee and thigh were rejected. This separate candidate aligns the native thigh/knee bend axes and rebuilds the hip correction for the changed pose.</p>','<p>The improved Vexa shoulder baseline is preserved. Current work fixes thumb contamination, wrist/ankle seams and discontinuous wrist motion before wider animation reuse.</p>')
page=page.replace('<h2>Open-knee comparison</h2><div class="grid">',intro+'<details><summary>Earlier knee investigation — still open</summary><div class="grid">')
page+=shot(R/'LegPlaneReview/9.03333_knee_outer_source.png','Before · approximately 60-degree bend')
page+=shot(R/'LegPlaneHipProof/9.03333_knee_outer.png','Candidate · same joint positions, corrected bend plane')
page+=shot(R/'LegPlaneHipProof/9.5_knee_inner.png','Candidate · opposing view at approximately 39 degrees')
page+='</div><h2>Whole-body context</h2><div class="grid">'
page+=shot(R/'LegPlaneHipProof/8_body_back.png','Candidate curl · rebuilt hip correction')
page+=shot(R/'LegPlaneHipProof/9.5_body_back.png','Candidate opening · hip-to-knee silhouette')
page+=shot(R/'LegPlaneHipProof/12.2_body_front.png','Candidate extension · both legs visible')
page+='</div><h2>Continuous motion</h2><p>16-second diagnostic with the camera following the pelvis. Forearm marks are temporary; production materials are not being judged here.</p><video controls loop preload="metadata" src="Roxie_LegPlane_MotionReview.mp4"></video><h2>Native Unreal readback</h2><p>Fresh isolated project load, neutral geometry shading, 65 morphs and curves. This compact proof intentionally contains only torso, bottom and legs; missing extremities are not a full-character result.</p><div class="grid">'
page+=shot(R/'NativeLegPlaneViews/8_back.png','Unreal · curled pose')
page+=shot(R/'NativeLegPlaneViews/9.033333_back.png','Unreal · opening pose')
page+='</div><p>Still open: remaining knee/thigh polish, continuous native geometry parity, all five segments, hands/pole contact, other dancers and owner motion acceptance.</p></details></html>'
(D/'Review.html').write_text(page,encoding='utf-8');print(D/'Review.html')
