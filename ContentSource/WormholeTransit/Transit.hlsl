// Original cylindrical procedural vapor; TransitTime is passage time in seconds.
// TransitBlend dims emission. Opaque walls must be hidden by the runtime at exit.
struct TransitNoise
{
    float Hash(float3 p)
    {
        p = frac(p * 0.1031);
        p += dot(p, p.yzx + 33.33);
        return frac((p.x + p.y) * p.z);
    }
    float Value(float3 p)
    {
        float3 i = floor(p);
        float3 f = frac(p);
        f = f * f * (3.0 - 2.0 * f);
        float n00 = lerp(Hash(i), Hash(i + float3(1,0,0)), f.x);
        float n10 = lerp(Hash(i + float3(0,1,0)), Hash(i + float3(1,1,0)), f.x);
        float n01 = lerp(Hash(i + float3(0,0,1)), Hash(i + float3(1,0,1)), f.x);
        float n11 = lerp(Hash(i + float3(0,1,1)), Hash(i + float3(1,1,1)), f.x);
        return lerp(lerp(n00, n10, f.y), lerp(n01, n11, f.y), f.z);
    }
    float Cloud(float3 p)
    {
        return Value(p) * 0.58 + Value(p * 2.07 + float3(7.1,3.8,1.6)) * 0.28
             + Value(p * 4.19 + float3(1.3,8.4,5.2)) * 0.14;
    }
};
TransitNoise noise;
float isCap = step(1.5, UV.x);
float distanceAlong = lerp(saturate(UV.x), 1.0, isCap);
float radial = lerp(1.0, saturate(UV.x - 2.0), isCap);
float angle = UV.y * 6.28318530718 + distanceAlong * 15.0 + 0.5 * sin(distanceAlong * 11.0);
float clock = TransitTime * max(Speed, 0.0);
// Increasing clock carries recognizable wisps toward the near mouth.
float3 domain = float3(cos(angle) * radial * 3.4, sin(angle) * radial * 3.4,
                      distanceAlong * 35.0 + clock * 9.0);
float warpA = noise.Value(domain * 0.61 + float3(2.7,1.3,0.0));
float warpB = noise.Value(domain * 0.73 + float3(9.2,4.8,2.1));
float3 warped = domain + float3(warpA - 0.5, warpB - 0.5, warpA - warpB) * 1.65;
float vapor = noise.Cloud(warped);
float fold = smoothstep(0.30, 0.68, vapor);
float illuminated = smoothstep(0.46, 0.77, vapor);
float peach = smoothstep(0.58, 0.82, vapor + 0.11 * (warpB - 0.5));
float3 color = lerp(FoldColor, Lavender, fold);
color = lerp(color, Pink, illuminated * 0.80);
color = lerp(color, Peach, peach * 0.87);
color *= 0.46 + illuminated * 1.65;

// Thin axial filaments. Integer angular frequencies preserve the UV seam;
// there is no uniform longitudinal oscillation that could create ring bands.
float phase = angle * 23.0 + sin(angle * 5.0 + distanceAlong * 2.3) * 1.4
            + (warpA - 0.5) * 2.2 + distanceAlong * 1.7;
float filamentDistance = abs(sin(phase));
float filterWidth = max(fwidth(phase) * 0.8, 0.006);
float filament = 1.0 - smoothstep(0.012, 0.025 + filterWidth, filamentDistance);
float filamentEnvelope = smoothstep(0.60, 0.84,
    noise.Value(float3(domain.xy * 2.3, domain.z * 0.39 + 8.1)));
color += lerp(Lavender, Peach, warpB) * filament * filamentEnvelope * 0.25 * radial;

// Soft vanishing point; the cap boundary uses the same domain as the far wall.
float approach = smoothstep(0.68, 1.0, distanceAlong);
color = lerp(color, color * 0.65 + Peach * 0.92, approach * 0.62);
float core = max(exp(-radial * radial * 5.2) - exp(-5.2), 0.0) / (1.0 - exp(-5.2)) * isCap;
color = lerp(color, Peach * 2.5 + float3(0.45,0.32,0.22), core);
// A gradual warm wash, limited to 1.5x gain rather than an abrupt white flash.
float exitWash = smoothstep(0.0, 1.0, saturate(ExitFlash));
color = lerp(color, color * float3(1.03,0.97,0.90) + float3(0.30,0.20,0.14), exitWash * 0.55);
color *= lerp(0.55, 1.0, smoothstep(0.1, 0.9, distanceAlong));
return max(color, 0.0) * max(Glow, 0.0) * saturate(TransitBlend) * (1.0 + exitWash * 0.5);
