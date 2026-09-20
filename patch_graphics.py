content = open('graphics.py', encoding='utf-8').read()

old_tex = '''                if getattr(obj, "الخامة", None) and getattr(obj, "texture_id", None) is None:
                    try:
                        import textures
                        obj.texture_id = textures.load_texture(obj.الخامة)
                    except:
                        obj.texture_id = -1'''

new_tex = '''                tex_path = getattr(obj, "filepath", getattr(obj, "الخامة", None))
                if not tex_path and hasattr(obj, "الصورة") and obj.الصورة:
                    tex_path = obj.الصورة
                if tex_path and getattr(obj, "texture_id", None) is None:
                    try:
                        import textures
                        obj.texture_id = textures.load_texture(tex_path)
                    except:
                        obj.texture_id = -1'''

content = content.replace(old_tex, new_tex)

old_circle = '''                    glBegin(GL_POLYGON)
                    for i in range(36):
                        theta = i * 10 * 3.14159 / 180
                        glVertex2f(x + r * math.cos(theta), y + r * math.sin(theta))
                    glEnd()'''

new_circle = '''                    glBegin(GL_POLYGON)
                    has_tex = getattr(obj, "texture_id", -1) != -1 and obj.texture_id is not None
                    for i in range(36):
                        theta = i * 10 * 3.14159 / 180
                        cx, cy = math.cos(theta), math.sin(theta)
                        if has_tex: glTexCoord2f(cx * 0.5 + 0.5, cy * 0.5 + 0.5)
                        glVertex2f(x + r * cx, y + r * cy)
                    glEnd()'''

content = content.replace(old_circle, new_circle)

old_tri = '''                    glBegin(GL_TRIANGLES)
                    glVertex2f(x, y - bh/2)
                    glVertex2f(x - bw/2, y + bh/2)
                    glVertex2f(x + bw/2, y + bh/2)
                    glEnd()'''

new_tri = '''                    glBegin(GL_TRIANGLES)
                    has_tex = getattr(obj, "texture_id", -1) != -1 and obj.texture_id is not None
                    if has_tex: glTexCoord2f(0.5, 0.0)
                    glVertex2f(x, y - bh/2)
                    if has_tex: glTexCoord2f(0.0, 1.0)
                    glVertex2f(x - bw/2, y + bh/2)
                    if has_tex: glTexCoord2f(1.0, 1.0)
                    glVertex2f(x + bw/2, y + bh/2)
                    glEnd()'''

content = content.replace(old_tri, new_tri)

open('graphics.py', 'w', encoding='utf-8').write(content)
print('Done patch')
