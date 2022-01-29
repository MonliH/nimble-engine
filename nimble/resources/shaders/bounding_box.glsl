#version 330 core

#if defined VERTEX_SHADER

in vec3 model_position;
uniform mat4 vp;

void main()
{
    gl_Position = vp * vec4(model_position, 1.0);
}

#elif defined FRAGMENT_SHADER

uniform vec3 color;
out vec4 frag_color;

void main()
{
    // Give it a constant color
    frag_color = vec4(color, 1.0);
} 

#endif
