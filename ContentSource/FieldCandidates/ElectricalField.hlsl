// FieldCandidate1: UV0 encodes geometric role/strand; no texture, opacity or WPO.
// Emission comes from AdvanceElectricalPulse. Never manufacture a timed flash.
float role = floor(UV.x * 0.25 + 0.00001);
float along = UV.x - role * 4.0;
float strand = floor(UV.y * 0.5);
float around = UV.y - strand * 2.0;
float e = clamp(Emission, 0.0, 4.0);
float3 hue = max(Tint * Color, 0.0);
// Boundary is always visible and unaffected by decorative time variation.
if (role < 0.5)
    return lerp(float3(0.16,0.19,0.23), hue, 0.48) * (0.14 + 0.065 * e);
// Slow, low-contrast detail cannot imitate the authoritative discharge peak.
float grain = 0.92 + 0.08 * sin(along * 39.0 - Time * 0.65 + strand * 2.39996);
float core = 0.74 + 0.26 * pow(abs(cos(around * 6.2831853)), 4.0);
float branch = role > 1.5 ? 0.63 : 1.0;
float whiteCore = saturate((e - 1.6) / 1.2) * 0.38;
float3 plasma = lerp(hue, float3(0.88,0.94,1.0), whiteCore);
return plasma * branch * core * (0.025 + 0.66 * e) * grain;
