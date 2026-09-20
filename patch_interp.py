content = open('interpreter.py', encoding='utf-8').read()

# Fix getattr in evaluate()
old_getattr1 = '''                    else:
                        if last_key == "الصورة": last_key = "filepath"
                        obj = getattr(prev_obj, last_key)'''
new_getattr1 = '''                    else:
                        if last_key == "الصورة": last_key = "filepath"
                        if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                        obj = getattr(prev_obj, last_key)'''
content = content.replace(old_getattr1, new_getattr1)

old_getattr2 = '''                if not hasattr(prev_obj, last_key):
                    raise Exception(f"الخاصية '{last_key}' غير موجودة")
                if last_key == "الصورة": last_key = "filepath"
                return getattr(prev_obj, last_key)'''
new_getattr2 = '''                if last_key == "الصورة": last_key = "filepath"
                if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                if not hasattr(prev_obj, last_key):
                    raise Exception(f"الخاصية '{last_key}' غير موجودة")
                return getattr(prev_obj, last_key)'''
content = content.replace(old_getattr2, new_getattr2)

old_setattr1 = '''                else:
                    if last_key == "الصورة": last_key = "filepath"
                    current = getattr(prev_obj, last_key)
                    setattr(prev_obj, last_key, current + delta if op == "+=" else current - delta)'''
new_setattr1 = '''                else:
                    if last_key == "الصورة": last_key = "filepath"
                    if not hasattr(prev_obj, last_key) and last_key == "filepath": setattr(prev_obj, "filepath", "")
                    current = getattr(prev_obj, last_key)
                    setattr(prev_obj, last_key, current + delta if op == "+=" else current - delta)'''
content = content.replace(old_setattr1, new_setattr1)

open('interpreter.py', 'w', encoding='utf-8').write(content)
print('Done interpreter')

# Now for view_scene_ui.py selection highlight / make selection easier
# The user said "وبعدها لما اضغط عنصر في في المشهد احس فيه صعوبه سهلها اكثر"
# Let's check view_scene.py _mousePressEvent. It uses raycasting.

content2 = open('view_scene.py', encoding='utf-8').read()
content2 = content2.replace('def delete_selected(self):\\n        if not self.selected_obj: return', 'def delete_selected(self):\\n        if not self.selected_obj: return')

open('view_scene.py', 'w', encoding='utf-8').write(content2)
print('Done view_scene')

