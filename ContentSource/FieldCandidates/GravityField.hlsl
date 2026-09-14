// FieldCandidate1: curved geometry conveys inward flow; no refraction or WPO.
// Activation intensity remains the existing Age/TelegraphSeconds Emission value.
float role = floor(UV.x * 0.25 + 0.00001);
float along = UV.x - role * 4.0;
float strand = floor(UV.y * 0.5);
float around = UV.y - strand * 2.0;
float e = clamp(Emission, 0.0, 4.0);
float3 hue = max(Tint * Color, 0.0);
if (role < 0.5)
    return lerp(float3(0.16,0.19,0.23), hue, 0.48) * (0.14 + 0.065 * e);
// Flow runs toward increasing U (outer -> inner), without a new activation clock.
float flow = 0.86 + 0.14 * sin(along * 18.849556 - Time * 0.72 + strand * 1.618034);
float core = 0.76 + 0.24 * pow(abs(cos(around * 6.2831853)), 4.0);
float taper = 0.72 + 0.28 * smoothstep(0.0,0.7,along);
return lerp(hue, float3(0.62,0.72,1.0), 0.18) * core * taper * (0.025 + 0.58 * e) * flow;
