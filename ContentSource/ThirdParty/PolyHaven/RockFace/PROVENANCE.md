# Poly Haven Rock Face source provenance

Asset: https://polyhaven.com/a/rock_face
License: CC0-1.0, verified 2026-09-13 at https://polyhaven.com/license
Photography: Greg Zaal. Processing: Dario Barresi. Published source width: 2.4 metres.

The three original 2K PNG downloads are retained byte-for-byte. Their official API byte counts and MD5 checksums matched after download; manifest.json records exact URLs, SHA256, dates and dimensions. The diffuse image is color data; ARM packs ambient occlusion, roughness and metallic; nor_dx is the DirectX normal convention. No website example renders or branding are included.

The candidate /Game/SpaceSurvival/Materials/M_RockPhotographic uses signed object-local triplanar projection, so existing unwrapped/UV-less asteroid meshes need no geometry change. RepeatLocalCm is before actor scale; larger rocks have proportionally larger features. Desaturation, tint and normal strength are shader settings, not source image edits. It is isolated from M_Rock, M_Hazard and every mesh assignment until explicitly integrated by the lead.

Asset/license page statements above are paraphrased. The content is CC0; this record supplies provenance and does not change that license. See https://creativecommons.org/publicdomain/zero/1.0/ for the dedication.