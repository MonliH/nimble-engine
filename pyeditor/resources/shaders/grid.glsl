#version 330 core

#if defined VERTEX_SHADER
in vec3 vert;

uniform mat4 view;
uniform mat4 proj;
uniform mat4 model;

out vec2 frag_uv;
out vec3 model_pos;

void main()
{
    vec4 p = model * vec4(vert.xyz, 1.0);
    gl_Position = proj * view * p;
    frag_uv = vert.xy;
    model_pos = p.xyz;
}

#elif defined FRAGMENT_SHADER

in vec2 frag_uv;
out vec4 frag_color;

uniform float zoom_level;

float roundUp(float numToRound, float multiple) {
    float remainder = mod(numToRound, multiple);
    if (remainder == 0.0) {
        return numToRound;
    }
    return numToRound + multiple - remainder;
}

vec4 grid(vec2 uv_coord, float scale) {
    vec2 coord = uv_coord * scale;
    vec2 derivative = fwidth(coord);
    vec2 grid = abs(fract(coord - 0.5) - 0.5) / derivative;
    float line = min(grid.x, grid.y);
    vec4 color = vec4(0.15, 0.15, 0.15, 1.0 - min(line, 1.0));
    return color;
}

float log10 = 1 / log(10);
float zoom_mag = log10*log(zoom_level);
float zoom_stage = ceil(zoom_mag);
float zoom_segment_percentage = fract(zoom_mag);
float grid_size = pow(10, 4-zoom_stage);

uniform vec3 camera_target;
in vec3 model_pos;

void main() {
    frag_color = grid(frag_uv, (grid_size * 2)) * 2 * (1 + zoom_segment_percentage / 4)
               + grid(frag_uv, (grid_size * 20)) * (1-zoom_segment_percentage);
    
    float fade_factor = length(camera_target - model_pos);
    fade_factor = clamp(1 - fade_factor / (zoom_level*5), 0.0, 1.0);
    frag_color.w *= fade_factor;
} 

#endif
