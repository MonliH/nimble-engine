#version 330 core

#if defined VERTEX_SHADER
in vec3 vert;

uniform mat4 view;
uniform mat4 proj;

out vec3 far_point;
out vec3 near_point;
out mat4 frag_view;
out mat4 frag_proj;

vec3 UnprojectPoint(float x, float y, float z, mat4 local_view, mat4 local_proj) {
    mat4 viewInv = inverse(local_view);
    mat4 projInv = inverse(local_proj);
    vec4 unprojectedPoint =  viewInv * projInv * vec4(x, y, z, 1.0);
    return unprojectedPoint.xyz / unprojectedPoint.w;
}

void main()
{
    near_point = UnprojectPoint(vert.x, vert.y, 0.0, view, proj).xyz;
    far_point = UnprojectPoint(vert.x, vert.y, 1.0, view, proj).xyz;
    gl_Position = vec4(vert.xyz, 1.0);
    frag_view = view;
    frag_proj = proj;
}

#elif defined FRAGMENT_SHADER

in vec3 far_point;
in vec3 near_point;

in mat4 frag_view;
in mat4 frag_proj;

out vec4 frag_color;

vec4 grid(vec3 fragPos3D, float scale) {
    vec2 coord = fragPos3D.xz * scale; // use the scale variable to set the distance between the lines
    vec2 derivative = fwidth(coord);
    vec2 grid = abs(fract(coord - 0.5) - 0.5) / derivative;
    float line = min(grid.x, grid.y);
    float minimumz = min(derivative.y, 1);
    float minimumx = min(derivative.x, 1);
    if (line >= 1.0) {
        discard;
    }
    vec4 color = vec4(0.2, 0.2, 0.2, 1.0 - line);
    // z axis
    if(fragPos3D.x > -0.1 * minimumx && fragPos3D.x < 0.1 * minimumx) {
        color.z = 1.0;
    }
    // x axis
    if(fragPos3D.z > -0.1 * minimumz && fragPos3D.z < 0.1 * minimumz) {
        color.x = 1.0;
    }
    return color;
}

float computeDepth(vec3 pos) {
    vec4 clip_space_pos = frag_proj * frag_view * vec4(pos.xyz, 1.0);
    return (clip_space_pos.z / clip_space_pos.w);
}

float near = 0.1; 
float far  = 100.0; 
  
float LinearizeDepth(float depth) 
{
    float z = depth * 2.0 - 1.0; // back to NDC 
    return (2.0 * near * far) / (far + near - z * (far - near));	
}


void main() {
    float t = -near_point.y / (far_point.y - near_point.y);
    vec3 fragPos3D = near_point + t * (far_point - near_point);
    gl_FragDepth = computeDepth(fragPos3D);
    frag_color = grid(fragPos3D, 10) * float(t > 0);
} 

#endif
