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

layout (location=0) uniform sampler2DMS depthTexture;
uniform float kernel[9];
uniform vec3 outline_color = vec3(1.0, 0.5, 0.2);
uniform float width;
uniform float height;

out vec4 frag_color;

float offsetW = 2.0 / width;
float offsetH = 2.0 / height;

void main()
{
    vec2 offsets[9] = vec2[](
        vec2(-offsetW,  offsetH), // top-left
        vec2( 0.0f,    offsetH), // top-center
        vec2( offsetW,  offsetH), // top-right
        vec2(-offsetW,  0.0f),   // center-left
        vec2( 0.0f,    0.0f),   // center-center
        vec2( offsetW,  0.0f),   // center-right
        vec2(-offsetW, -offsetH), // bottom-left
        vec2( 0.0f,   -offsetH), // bottom-center
        vec2( offsetW, -offsetH)  // bottom-right    
    );

    vec4 sampleTex[9];
    for(int i = 0; i < 9; i++)
    {
        ivec2 vp_coords = ivec2(width, height);
        vp_coords.x = int(vp_coords.x * (TexCoords.x + offsets[i].x));
        vp_coords.y = int(vp_coords.y * (TexCoords.y + offsets[i].y));

        vec4 sum = vec4(0);
        for(int j = 0; j < 4; j++) {
            sum += texelFetch(depthTexture, vp_coords, j);
        }
        sum /= 4;
        sampleTex[i] = sum;
    }

    vec4 col = vec4(0);
    for(int i = 0; i < 9; i++)
        col += sampleTex[i] * kernel[i];

    frag_color = vec4(outline_color, col.w*10);
}  
#endif
