#version 330 core

#if defined VERTEX_SHADER
in vec3 in_position;
in vec3 in_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

out vec3 pos;
out vec3 normal;

void main()
{
    mat4 world_coords = view * model;
    vec4 p = world_coords * vec4(in_position, 1.0);
    gl_Position = proj * p;
    mat3 m_normal = inverse(transpose(mat3(world_coords)));
    normal = m_normal * normalize(in_normal);
    pos = p.xyz;
}

#elif defined FRAGMENT_SHADER

in vec3 pos;
in vec3 normal;

uniform vec3 color;

out vec4 frag_color;

void main()
{
    float l = dot(normalize(-pos), normalize(normal));
    frag_color = vec4(color, 1.0) * (0.25 + abs(l) * 0.75);
} 

#endif
