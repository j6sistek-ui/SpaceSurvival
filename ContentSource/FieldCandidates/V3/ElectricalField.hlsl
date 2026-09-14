// FieldCandidate3: soft additive extent and stable ribbon coverage; no new flash clock.
float role = floor(UV.x * 0.25 + 0.00001);
float along = UV.x - role * 4.0;
float strand = floor(UV.y * 0.25 + 0.00001);
float across = (UV.y - strand * 4.0) * 2.0 - 1.0;
float footprint = max(fwidth(across), 0.001);
float facing = saturate(abs(dot(normalize(Normal), normalize(View))));
float e = clamp(Emission, 0.0, 4.0);
float3 hue = max(Tint * Color, 0.0);
if (role < 0.5)
{
    float rim = 1.0 - facing;
    rim *= rim; rim *= rim;
    return float4(lerp(float3(0.28,0.34,0.42), hue, 0.42) * (0.72 + 0.035 * e), 0.012 + 0.18 * rim);
}
// Filter the narrow core across the current pixel footprint; broad geometry supplies coverage.
float coreWidth = 0.12;
float filteredWidth = max(coreWidth, footprint * 0.60);
float core = exp2(-1.442695 * across * across / (filteredWidth * filteredWidth)) * coreWidth / filteredWidth;
float halo = exp2(-5.0 * across * across) * (1.0 - smoothstep(0.72,1.0,abs(across)));
float endFade = 0.4 + 0.6 * smoothstep(0.0,0.10,min(along,1.0-along));
float branch = role > 1.5 ? 0.68 : 1.0;
float grain = 0.96 + 0.04 * sin(along*39.0-Time*0.65+strand*2.39996);
// Charge tops out near2.1; only the actual supplied discharge value yields this white accent.
float discharge = smoothstep(2.10,2.75,e);
float3 plasma = lerp(hue,float3(0.94,0.98,1.0),discharge*0.90);
float opacity = saturate((0.42*core+0.16*halo)*endFade*branch*facing*facing*1.2);
return float4(plasma*(0.08+1.20*e+3.0*discharge)*grain,opacity);
