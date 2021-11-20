#version 330 core

#if defined VERTEX_SHADER
in vec3 vert;

uniform mat4 view;
uniform mat4 proj;

out vec3 far_point;
out vec3 near_point;

vec3 UnprojectPoint(float x, float y, float z, mat4 view, mat4 projection) {
    mat4 view_inv = inverse(view);
    mat4 proj_inv = inverse(projection);
    vec4 unprojected_point =  view_inv * proj_inv * vec4(x, y, z, 1.0);
    return unprojected_point.xyz / unprojected_point.w;
}

void main()
{
    near_point = UnprojectPoint(vert.x, vert.y, 0.0, view, proj).xyz;
    far_point = UnprojectPoint(vert.x, vert.y, 1.0, view, proj).xyz;
    gl_Position = vec4(vert.xy, 0.0, 1.0);
}

#elif defined FRAGMENT_SHADER

in vec3 far_point;
in vec3 near_point;

out vec4 frag_color;

vec4 grid(vec3 fragPos3D, float scale) {
    vec2 coord = fragPos3D.xz * scale; // use the scale variable to set the distance between the lines
    vec2 derivative = fwidth(coord);
    vec2 grid = abs(fract(coord - 0.5) - 0.5) / derivative;
    float line = min(grid.x, grid.y);
    float minimumz = min(derivative.y, 1);
    float minimumx = min(derivative.x, 1);
    vec4 color = vec4(0.2, 0.2, 0.2, 1.0 - min(line, 1.0));
    // z axis
    if(fragPos3D.x > -0.1 * minimumx && fragPos3D.x < 0.1 * minimumx)
        color.z = 1.0;
    // x axis
    if(fragPos3D.z > -0.1 * minimumz && fragPos3D.z < 0.1 * minimumz)
        color.x = 1.0;
    return color;
}


void main() {
    float t = -near_point.y / (far_point.y - near_point.y);
    vec3 fragPos3D = near_point + t * (far_point - near_point);
    frag_color = grid(fragPos3D, 10) * float(t > 0);

} 

#endif
