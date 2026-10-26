import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
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
intro=current+'<details><summary>Earlier shoulder controls — superseded, retained for comparison</summary>'+intro.replace('<h2>Current target: Vexa</h2>','<h2>Earlier Vexa baseline</h2>')+'</details>'
page=page.replace('<title>Leg deformation review</title>','<title>Vexa shoulder balance</title>').replace('<h1>Hip, thigh and knee review</h1>','<h1>Vexa deformation review</h1>')
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
