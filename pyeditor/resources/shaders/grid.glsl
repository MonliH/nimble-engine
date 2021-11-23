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
float zoom_stage = clamp(ceil(zoom_mag), 2, 4);
float zoom_segment_percentage = fract(zoom_mag);
float grid_square_size = pow(10, 4-zoom_stage);

uniform float grid_radius;
uniform vec3 camera_target;
in vec3 model_pos;

float radius_to_original = grid_radius/500;

void main() {
    vec4 bigger_color = grid(frag_uv, grid_square_size * radius_to_original);
    // Make larger grid more bold based on zoomgrid
    bigger_color.w *= (1 + zoom_segment_percentage);

    vec4 smaller_color = grid(frag_uv, grid_square_size * 10 * radius_to_original);
    // Make smaller grid less bold based on zoom
    smaller_color.w *= 1-zoom_segment_percentage/(5-zoom_stage);

    frag_color = bigger_color + smaller_color;
    
    vec3 diff = camera_target - model_pos;
    float fade_factor = length(diff.xz);
    fade_factor = clamp(1 - fade_factor / grid_radius, 0.0, 0.5);
    frag_color.w *= fade_factor;

    // if (frag_uv.x > -0.0004 && frag_uv.x < 0.0004) {
    //     // X axis
    //     frag_color.z = 1.0;
    //     frag_color.w *= 2;
    // }
    // if (frag_uv.y > -0.0004 && frag_uv.y < 0.0004) {
    //     // Z axis
    //     frag_color.x = 1.0;
    //     frag_color.w *= 2;
    // }
} 

#endif
