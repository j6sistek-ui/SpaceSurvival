// FieldCandidate2: thin additive inward streamlines; no refraction, WPO or force clock.
float role = floor(UV.x * 0.25 + 0.00001);
float along = UV.x - role * 4.0;
float strand = floor(UV.y * 0.5);
float e = clamp(Emission, 0.0, 4.0);
float facing = saturate(abs(dot(normalize(Normal), normalize(View))));
float edge = pow(facing, 1.4);
float3 hue = max(Tint * Color, 0.0);
if (role < 0.5)
    return float4(lerp(float3(0.16,0.19,0.23), hue, 0.35) * (0.045 + 0.012 * e), 0.16 + 0.10 * edge);
// Decorative motion stays bounded and cannot create an activation/force pulse.
float flow = 0.90 + 0.10 * sin(along * 18.849556 - Time * 0.72 + strand * 1.618034);
float endFade = 0.40 + 0.60 * smoothstep(0.0, 0.12, min(along, 1.0-along));
float opacity = saturate((0.10 + 0.35 * edge) * endFade);
float3 plasma = lerp(hue, float3(0.62,0.72,1.0), 0.18);
return float4(plasma * (0.035 + 0.90 * e) * flow, opacity);
