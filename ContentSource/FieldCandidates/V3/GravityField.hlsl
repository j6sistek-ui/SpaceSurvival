// FieldCandidate3: coherent additive extent plus smoothly curved flow ribbons.
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
float coreWidth = 0.13;
float filteredWidth = max(coreWidth,footprint*0.60);
float core = exp2(-1.442695*across*across/(filteredWidth*filteredWidth))*coreWidth/filteredWidth;
float halo = exp2(-4.0*across*across)*(1.0-smoothstep(0.72,1.0,abs(across)));
float endFade = 0.4+0.6*smoothstep(0.0,0.10,min(along,1.0-along));
// Motion is decorative and remains bounded; force/activation timing stays external.
float flow = 0.90+0.10*sin(along*18.849556-Time*0.72+strand*1.618034);
float opacity = saturate((0.34*core+0.17*halo)*endFade*facing*facing*1.2);
return float4(lerp(hue,float3(0.62,0.72,1.0),0.18)*(0.06+1.50*e)*flow,opacity);
