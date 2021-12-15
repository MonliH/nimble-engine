#version 330 core

#if defined VERTEX_SHADER

in vec3 in_position;
uniform mat4 view;
uniform mat4 proj;

void main()
{
    gl_Position = proj * view * vec4(in_position, 1.0);
}

#elif defined FRAGMENT_SHADER

uniform vec3 color = vec3(0.0, 1.0, 0.0);
out vec4 frag_color;

void main()
{
    frag_color = vec4(color, 1.0);
} 

#endif
