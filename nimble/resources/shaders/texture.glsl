#version 430 core

#if defined VERTEX_SHADER

in vec2 in_position;
in vec2 in_texcoord_0;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(in_position.x, in_position.y, 0.0, 1.0); 
    TexCoords = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

in vec2 TexCoords;

layout (location=0) uniform sampler2D texture0;

out vec4 frag_color;

void main()
{
    frag_color = texture(texture0, TexCoords);
}  
#endif
