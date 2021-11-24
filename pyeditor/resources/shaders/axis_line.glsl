#version 330 core

#if defined VERTEX_SHADER

in vec3 vert;

uniform mat4 mvp;

void main() {
    gl_Position = mvp * vec4(ver, 1.0);
}

#elif defined FRAGMENT_SHADER

uniform vec4 color;
out vec4 frag_color;

void main() {
    frag_color = color;
}

#endif
