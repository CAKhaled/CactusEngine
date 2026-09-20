import re

with open('graphics.py', 'r', encoding='utf-8') as f:
    code = f.read()

replacement = """            # ==========================
            # رسم المجسمات
            # ==========================

            def render_obj(o):
                glPushMatrix()
                glTranslatef(o.الموقع.x, o.الموقع.y, o.الموقع.z)
                glRotatef(o.الدوران.x, 1, 0, 0)
                glRotatef(o.الدوران.y, 0, 1, 0)
                glRotatef(o.الدوران.z, 0, 0, 1)
                glScalef(o.المقياس.x, o.المقياس.y, o.المقياس.z)
                
                if isinstance(o, Cube): self.draw_cube(o)
                elif isinstance(o, Sphere): self.draw_sphere(o)
                elif isinstance(o, Plane): self.draw_plane(o)
                elif isinstance(o, Pyramid): self.draw_pyramid(o)
                elif isinstance(o, Cylinder): self.draw_cylinder(o)
                elif isinstance(o, Capsule): self.draw_capsule(o)
                elif isinstance(o, CustomModel): self.draw_custom(o)
                
                glPopMatrix()

            if getattr(self, "shadows", False) and self.light is not None:
                floors = [o for o in self.objects if isinstance(o, Plane)]
                others = [o for o in self.objects if not isinstance(o, Plane)]
                
                if floors:
                    # 1. رسم الأرضيات وكتابة 1 في الاستنسل
                    glEnable(GL_STENCIL_TEST)
                    glStencilFunc(GL_ALWAYS, 1, 0xFF)
                    glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
                    
                    for f in floors:
                        render_obj(f)
                        
                    # 2. رسم الظلال (فقط الأماكن التي فيها الأرضية)
                    glStencilFunc(GL_EQUAL, 1, 0xFF)
                    glStencilOp(GL_KEEP, GL_KEEP, GL_INCR)
                    
                    glDisable(GL_LIGHTING)
                    glDisable(GL_DEPTH_TEST)
                    glDisable(GL_TEXTURE_2D)
                    glEnable(GL_BLEND)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                    glColor4f(0.0, 0.0, 0.0, 0.6)
                    
                    self.is_rendering_shadow = True
                    
                    floor = floors[0]
                    l = self.light.الموقع
                    light_w = 0.0 if self.light.النوع == "ضوء_موجه" else 1.0
                    fy = floor.الموقع.y + 0.001
                    
                    dot_ln = l.y - light_w * fy
                    s_mat = [
                        dot_ln, 0, 0, 0,
                        -l.x, -light_w*fy, -l.z, -light_w,
                        0, 0, dot_ln, 0,
                        l.x*fy, l.y*fy, l.z*fy, l.y
                    ]
                    
                    glPushMatrix()
                    glMultMatrixf(s_mat)
                    
                    for obj in others:
                        render_obj(obj)
                        
                    glPopMatrix()
                    
                    self.is_rendering_shadow = False
                    
                    glEnable(GL_LIGHTING)
                    glEnable(GL_DEPTH_TEST)
                    glDisable(GL_BLEND)
                    glDisable(GL_STENCIL_TEST)
                    
                    # 3. رسم باقي المجسمات بشكل عادي
                    for obj in others:
                        render_obj(obj)
                else:
                    for obj in self.objects:
                        render_obj(obj)
            else:
                for obj in self.objects:
                    render_obj(obj)

            pygame.display.flip()"""

# The original block is from "# ==========================\n            # رسم المجسمات" up to "pygame.display.flip()"
pattern = r"            # ==========================\n            # رسم المجسمات\n            # ==========================\n.*?(?=            clock\.tick\(60\))"

code = re.sub(pattern, replacement + "\n\n", code, flags=re.DOTALL)

with open('graphics.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Patched rendering loop successfully!")
