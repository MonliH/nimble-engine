#version 410

#if defined VERTEX_SHADER

uniform mat4 mvp;
in vec4 in_position;

void main()
{    
    gl_Position = mvp * in_position;
}

#elif defined FRAGMENT_SHADER

uniform vec4 color;
out vec4 frag_color;

void main()
{
    frag_color = color;
}

#elif defined GEOMETRY_SHADER

uniform vec2 viewport;
uniform float line_width = 2.0;

layout (lines) in;
layout (triangle_strip, max_vertices = 4) out;

void main()
{
    vec3 ndc0 = gl_in[0].gl_Position.xyz / gl_in[0].gl_Position.w;
    vec3 ndc1 = gl_in[1].gl_Position.xyz / gl_in[1].gl_Position.w;

    vec2 lineScreenForward = normalize(ndc1.xy - ndc0.xy);
    vec2 lineScreenRight = vec2(-lineScreenForward.y, lineScreenForward.x);
    vec2 lineScreenOffset = (vec2(line_width) / viewport) * lineScreenRight;

    vec4 cpos = gl_in[0].gl_Position;
    gl_Position = vec4(cpos.xy + lineScreenOffset*cpos.w, cpos.z, cpos.w);
    EmitVertex();

    gl_Position = vec4(cpos.xy - lineScreenOffset*cpos.w, cpos.z, cpos.w);
    EmitVertex();

    cpos = gl_in[1].gl_Position;
    gl_Position = vec4(cpos.xy + lineScreenOffset*cpos.w, cpos.z, cpos.w);
    EmitVertex();

    gl_Position = vec4(cpos.xy - lineScreenOffset*cpos.w, cpos.z, cpos.w);
    EmitVertex();

    EndPrimitive();
}


#endif
