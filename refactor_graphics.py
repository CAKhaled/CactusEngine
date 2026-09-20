import sys

def refactor():
    with open("graphics.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if "if self.sky_color:" in line and start_idx == -1:
            start_idx = i
        if "dt_ms = clock.tick(60)" in line:
            end_idx = i
            
    if start_idx == -1 or end_idx == -1:
        print("Could not find block boundaries")
        return
        
    # The block to extract is from start_idx to end_idx-1
    # Actually, we need to extract from start_idx up to pygame.display.flip()
    # Let's find pygame.display.flip()
    flip_idx = -1
    for i in range(start_idx, end_idx):
        if "pygame.display.flip()" in lines[i]:
            flip_idx = i
            break
            
    if flip_idx == -1:
        print("Could not find pygame.display.flip()")
        return
        
    render_block = lines[start_idx:flip_idx+1]
    
    # We will replace the block with a call to self.render_scene()
    new_run = lines[:start_idx] + ["            self.render_scene()\n"] + lines[flip_idx+1:]
    
    # And we will append the new method render_scene to the end of the file (or end of GraphicsEngine class)
    # GraphicsEngine class ends at the end of the file
    
    # Fix indentation of render_block from 12 spaces to 8 spaces
    fixed_render_block = []
    for line in render_block:
        if line.startswith("            "):
            fixed_render_block.append(line[4:])
        elif line.strip() == "":
            fixed_render_block.append("\n")
        else:
            fixed_render_block.append(line) # Shouldn't happen unless multiline string
            
    method_def = [
        "\n",
        "    def render_scene(self):\n",
        "        from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_STENCIL_BUFFER_BIT, glMatrixMode, GL_MODELVIEW, glLoadIdentity, glPushMatrix, glPushAttrib, GL_ENABLE_BIT, glDisable, GL_DEPTH_TEST, GL_LIGHTING, glEnable, GL_TEXTURE_2D, glColor3f, glBindTexture, glRotatef, glPopMatrix, glPopAttrib, glLightfv, GL_LIGHT0, GL_POSITION, GL_DIFFUSE, GL_SPECULAR, GL_AMBIENT, GL_SPOT_CUTOFF, GL_SPOT_DIRECTION, GL_SPOT_EXPONENT, GL_CONSTANT_ATTENUATION, GL_LINEAR_ATTENUATION, GL_QUADRATIC_ATTENUATION, GL_LIGHT_MODEL_AMBIENT, glLightModelfv, glLightf, glScalef, glTranslatef, glBegin, glEnd, GL_QUADS, GL_POLYGON, GL_TRIANGLES, glVertex2f, glColor4f, glTexCoord2f, GL_PROJECTION, glOrtho, glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_STENCIL_TEST, glStencilFunc, GL_ALWAYS, glStencilOp, GL_KEEP, GL_REPLACE, GL_EQUAL, GL_INCR, glMultMatrixf, glDeleteTextures, glGenTextures, glTexParameteri, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, GL_UNSIGNED_BYTE, glTexImage2D, GL_TRUE\n",
        "        from OpenGL.GLU import gluLookAt, gluNewQuadric, gluQuadricNormals, GLU_SMOOTH, gluQuadricTexture, gluQuadricOrientation, GLU_INSIDE, gluSphere, gluDeleteQuadric\n",
        "        import pygame\n"
    ]
    
    new_lines = new_run + method_def + fixed_render_block
    
    with open("graphics.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Refactoring complete.")

refactor()
