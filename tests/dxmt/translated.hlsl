// SPDX-License-Identifier: MIT
// Original Pear deterministic shaders; no game or vendor shader assets.
cbuffer Parameters : register(b0) { float4 color; float4 geometry; };
float4 vertex(uint id : SV_VertexID) : SV_Position {
    float2 p = id == 0 ? float2(-1,-1) : (id == 1 ? float2(-1,3) : float2(3,-1));
    return float4(p, geometry.z, 1);
}
float4 solid() : SV_Target { return color; }
Texture2D<float4> image : register(t0);
SamplerState point_sampler : register(s0);
float4 sample_image(float4 position : SV_Position) : SV_Target {
    return image.SampleLevel(point_sampler, position.xy / 8.0, 0);
}
StructuredBuffer<uint> input_values : register(t1);
RWStructuredBuffer<uint> output_values : register(u0);
[numthreads(16,1,1)]
void transform(uint3 id : SV_DispatchThreadID) {
    output_values[id.x] = input_values[id.x] * 3 + 7;
}
