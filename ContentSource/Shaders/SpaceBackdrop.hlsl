// Original direction-space nebula. Four bounded octaves; no gameplay visibility fog.
float3 p = normalize(Direction) * 3.2;
float density = 0.0;
float amplitude = 0.5;
[unroll] for (int octave = 0; octave < 4; ++octave)
{
    float3 cell = floor(p);
    float3 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float seed = dot(cell, float3(1.0, 157.0, 113.0));
    float4 low = frac(sin(seed + float4(0.0, 1.0, 157.0, 158.0)) * 43758.5453);
    float4 high = frac(sin(seed + float4(113.0, 114.0, 270.0, 271.0)) * 43758.5453);
    float a = lerp(lerp(low.x, low.y, f.x), lerp(low.z, low.w, f.x), f.y);
    float b = lerp(lerp(high.x, high.y, f.x), lerp(high.z, high.w, f.x), f.y);
    density += amplitude * lerp(a, b, f.z);
    p = p * 2.03 + float3(7.1, 3.8, 1.7);
    amplitude *= 0.5;
}
float band = pow(saturate(1.0 - abs(dot(normalize(Direction), normalize(float3(0.15, 0.8, 0.45)))) * 1.8), 3.0);
float cloud = smoothstep(0.32, 0.78, density) * band;
float dust = smoothstep(0.54, 0.72, density) * band;
float3 gas = lerp(float3(0.04, 0.065, 0.12), float3(0.16, 0.055, 0.09), smoothstep(0.38, 0.66, density));
return float3(0.0015, 0.0025, 0.006) + gas * Tint * cloud * (1.0 - dust * 0.65);
