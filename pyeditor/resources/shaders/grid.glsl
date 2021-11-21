#version 330 core

#if defined VERTEX_SHADER
in vec3 vert;

uniform mat4 view;
uniform mat4 proj;
uniform mat4 model;

out vec2 frag_uv;

void main()
{
    vec4 p = model * vec4(vert.xyz, 1.0);
    gl_Position = proj * view * p;
    frag_uv = vert.xy;
}

#elif defined FRAGMENT_SHADER

in vec2 frag_uv;
out vec4 frag_color;

vec4 grid(vec2 uv_coord, float scale) {
    vec2 coord = uv_coord * scale;
    vec2 derivative = fwidth(coord);
    vec2 grid = abs(fract(coord - 0.5) - 0.5) / derivative;
    float line = min(grid.x, grid.y);
    float minimumz = min(derivative.y, 1);
    float minimumx = min(derivative.x, 1);
    vec4 color = vec4(0.2, 0.2, 0.2, 1.0 - min(line, 1.0));
    // z axis
    if(uv_coord.x > -0.1 * minimumx && uv_coord.x < 0.1 * minimumx)
        color.z = 1.0;
    // x axis
    if(uv_coord.y > -0.1 * minimumz && uv_coord.y < 0.1 * minimumz)
        color.x = 1.0;
    return color;

}

void main() {
    frag_color = grid(frag_uv, 10.0);
} 

#endif
