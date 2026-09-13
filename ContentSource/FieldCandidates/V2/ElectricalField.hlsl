// FieldCandidate2: one additive pass, clock-fed amplitude and view-angle softness.
// Never manufacture a separate timed discharge. UV role0 is the persistent boundary.
float role = floor(UV.x * 0.25 + 0.00001);
float along = UV.x - role * 4.0;
float strand = floor(UV.y * 0.5);
float e = clamp(Emission, 0.0, 4.0);
float facing = saturate(abs(dot(normalize(Normal), normalize(View))));
float edge = pow(facing, 1.4);
float3 hue = max(Tint * Color, 0.0);
if (role < 0.5)
    return float4(lerp(float3(0.16,0.19,0.23), hue, 0.35) * (0.045 + 0.012 * e), 0.16 + 0.10 * edge);
float grain = 0.95 + 0.05 * sin(along * 39.0 - Time * 0.65 + strand * 2.39996);
float branch = role > 1.5 ? 0.65 : 1.0;
float endFade = 0.45 + 0.55 * smoothstep(0.0, 0.10, min(along, 1.0-along));
float3 plasma = lerp(hue, float3(0.92,0.97,1.0), saturate((e-1.6)/1.2)*0.55);
float opacity = saturate((0.12 + 0.43 * edge) * endFade * branch);
return float4(plasma * (0.04 + 1.6 * e) * grain, opacity);
