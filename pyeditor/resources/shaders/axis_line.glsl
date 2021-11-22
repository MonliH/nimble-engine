#version 450 core

#if defined VERTEX_SHADER

in vec3 vert;

uniform float u_width;
uniform mat4 u_mvp;
uniform vec4 u_col;

out vec4 v_col;
out noperspective float v_line_width;

void main() {
    v_col = u_col;
    v_line_width = u_width;
    gl_Position = u_mvp * vec4(vert, 1.0);
}

#elif defined FRAGMENT_SHADER

uniform vec2 u_aa_radius;
      
in vec4 g_col;
in noperspective float g_u;
in noperspective float g_v;
in noperspective float g_line_width;
in noperspective float g_line_length;

out vec4 frag_color;
void main() {
    /* We render a quad that is fattened by r, giving total width of the line to be w+r. We want smoothing to happen
        around w, so that the edge is properly smoothed out. As such, in the smoothstep function we have:
        Far edge   : 1.0                                          = (w+r) / (w+r)
        Close edge : 1.0 - (2r / (w+r)) = (w+r)/(w+r) - 2r/(w+r)) = (w-r) / (w+r)
        This way the smoothing is centered around 'w'.
        */
    float au = 1.0 - smoothstep( 1.0 - ((2.0*u_aa_radius[0]) / g_line_width),  1.0, abs(g_u / g_line_width) );
    float av = 1.0 - smoothstep( 1.0 - ((2.0*u_aa_radius[1]) / g_line_length), 1.0, abs(g_v / g_line_length) );
    frag_color = g_col;
    frag_color.a *= min(av, au);
}

#elif defined GEOMETRY_SHADER

layout(lines) in;
layout(triangle_strip, max_vertices = 4) out;

uniform vec2 u_viewport_size;
uniform vec2 u_aa_radius;

in vec4 v_col[];
in noperspective float v_line_width[];

out vec4 g_col;
out noperspective float g_line_width;
out noperspective float g_line_length;
out noperspective float g_u;
out noperspective float g_v;

void main()
{
    float u_width        = u_viewport_size[0];
    float u_height       = u_viewport_size[1];
    float u_aspect_ratio = u_height / u_width;

    vec2 ndc_a = gl_in[0].gl_Position.xy / gl_in[0].gl_Position.w;
    vec2 ndc_b = gl_in[1].gl_Position.xy / gl_in[1].gl_Position.w;

    vec2 line_vector = ndc_b - ndc_a;
    vec2 viewport_line_vector = line_vector * u_viewport_size;
    vec2 dir = normalize(vec2( line_vector.x, line_vector.y * u_aspect_ratio ));

    float line_width_a     = max( 1.0, v_line_width[0] ) + u_aa_radius[0];
    float line_width_b     = max( 1.0, v_line_width[1] ) + u_aa_radius[0];
    float extension_length = u_aa_radius[1];
    float line_length      = length( viewport_line_vector ) + 2.0 * extension_length;

    vec2 normal    = vec2( -dir.y, dir.x );
    vec2 normal_a  = vec2( line_width_a/u_width, line_width_a/u_height ) * normal;
    vec2 normal_b  = vec2( line_width_b/u_width, line_width_b/u_height ) * normal;
    vec2 extension = vec2( extension_length / u_width, extension_length / u_height ) * dir;

    g_col = vec4( v_col[0].rgb, v_col[0].a * min( v_line_width[0], 1.0f ) );
    g_u = line_width_a;
    g_v = line_length * 0.5;
    g_line_width = line_width_a;
    g_line_length = line_length * 0.5;
    gl_Position = vec4( (ndc_a + normal_a - extension) * gl_in[0].gl_Position.w, gl_in[0].gl_Position.zw );
    EmitVertex();

    g_u = -line_width_a;
    g_v = line_length * 0.5;
    g_line_width = line_width_a;
    g_line_length = line_length * 0.5;
    gl_Position = vec4( (ndc_a - normal_a - extension) * gl_in[0].gl_Position.w, gl_in[0].gl_Position.zw );
    EmitVertex();

    g_col = vec4( v_col[0].rgb, v_col[0].a * min( v_line_width[0], 1.0f ) );
    g_u = line_width_b;
    g_v = -line_length * 0.5;
    g_line_width = line_width_b;
    g_line_length = line_length * 0.5;
    gl_Position = vec4( (ndc_b + normal_b + extension) * gl_in[1].gl_Position.w, gl_in[1].gl_Position.zw );
    EmitVertex();

    g_u = -line_width_b;
    g_v = -line_length * 0.5;
    g_line_width = line_width_b;
    g_line_length = line_length * 0.5;
    gl_Position = vec4( (ndc_b - normal_b + extension) * gl_in[1].gl_Position.w, gl_in[1].gl_Position.zw );
    EmitVertex();

    EndPrimitive();
}

#endif
