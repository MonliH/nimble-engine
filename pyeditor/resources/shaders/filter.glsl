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

layout (location=0) uniform sampler2D depthTexture;
uniform float zoom_level;
uniform float kernel[9];

out vec4 FragColor;

float near=0.1;
float far=500.0;

float LinearizeDepth(float depth) 
{
    float z = depth * 2.0 - 1.0; // back to NDC 
    return (2.0 * near * far) / (far + near - z * (far - near));	
}

const float offset = 1.0 / 300.0;  

void main()
{
    vec2 offsets[9] = vec2[](
        vec2(-offset,  offset), // top-left
        vec2( 0.0f,    offset), // top-center
        vec2( offset,  offset), // top-right
        vec2(-offset,  0.0f),   // center-left
        vec2( 0.0f,    0.0f),   // center-center
        vec2( offset,  0.0f),   // center-right
        vec2(-offset, -offset), // bottom-left
        vec2( 0.0f,   -offset), // bottom-center
        vec2( offset, -offset)  // bottom-right    
    );

    vec4 sampleTex[9];
    for(int i = 0; i < 9; i++)
    {
        sampleTex[i] = texture(depthTexture, TexCoords.st + offsets[i]);
    }
    vec4 col = vec4(0);
    for(int i = 0; i < 9; i++)
        col += sampleTex[i] * kernel[i];

    if (col.w >= 0.1) {
        col.w = 1.0;
    }
    FragColor = vec4(1.0, 0.5, 0.4, col.w);
}  
#endif
