content = open('view_scene.py', encoding='utf-8').read()

# 1. Reverse Z-axis dragging
content = content.replace('self.selected_obj.pos[2] = self._drag_obj_start_pos[2] + dx * sensitivity', 'self.selected_obj.pos[2] = self._drag_obj_start_pos[2] - dx * sensitivity')
content = content.replace('self.selected_obj.rot[2] = self._drag_obj_start_rot[2] - dx * rot_sens', 'self.selected_obj.rot[2] = self._drag_obj_start_rot[2] + dx * rot_sens')
content = content.replace('self.selected_obj.scale[2] = max(0.01, self._drag_obj_start_scale[2] + dx * scl_sens)', 'self.selected_obj.scale[2] = max(0.01, self._drag_obj_start_scale[2] - dx * scl_sens)')

# 2. Add Capsule drawing
capsule_func = '''    def _draw_capsule(self):
        quad = gluNewQuadric()
        gluQuadricDrawStyle(quad, GLU_FILL)
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        glPushMatrix()
        glTranslatef(0, -0.5, 0)
        glRotatef(-90, 1, 0, 0)
        gluSphere(quad, 0.5, 24, 24)
        gluCylinder(quad, 0.5, 0.5, 1.0, 24, 1)
        glTranslatef(0, 0, 1.0)
        gluSphere(quad, 0.5, 24, 24)
        glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_cylinder(self):'''

content = content.replace('    def _draw_cylinder(self):', capsule_func)

old_cylinder_call = '''        elif t in ("Cylinder", "Capsule"):
            self._draw_cylinder()'''
new_cylinder_call = '''        elif t == "Cylinder":
            self._draw_cylinder()
        elif t == "Capsule":
            self._draw_capsule()'''
content = content.replace(old_cylinder_call, new_cylinder_call)

# 3. Change wireframe placeholder to solid
old_placeholder = '''        glPushAttrib(GL_POLYGON_BIT | GL_ENABLE_BIT)
        glDisable(GL_TEXTURE_2D)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glBegin(GL_QUADS)'''
new_placeholder = '''        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)'''
content = content.replace(old_placeholder, new_placeholder)

# 4. Hide grid by default
content = content.replace('self.show_grid = True', 'self.show_grid = False')

open('view_scene.py', 'w', encoding='utf-8').write(content)
print('Done patch')
