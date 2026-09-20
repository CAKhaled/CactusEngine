import os
import re

def read_scene_from_kh(scene_viewer, project_dir):
    if not project_dir:
        return
        
    scene_file = os.path.join(project_dir, "mainscene.khscene")
    if not os.path.exists(scene_file):
        return
        
    try:
        with open(scene_file, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Clear existing objects except camera
        new_objects = []
        camera_obj = None
        for obj in scene_viewer.objects:
            if obj.obj_type == "camera":
                camera_obj = obj
                break
        
        if not camera_obj:
            from view_scene import SceneObject
            camera_obj = SceneObject("الكاميرا", pos=[0.0, 3.0, 8.0], obj_type="camera")
            
        new_objects.append(camera_obj)
        
        from view_scene import SceneObject
        

        
        lines = code.splitlines()
        
        re_create = re.compile(r'ابغا\s+([^\s=]+)\s*=\s*([^\(]+)\((.*)\)')
        re_prop_vec3 = re.compile(r'([^\.]+)\.(الموقع|الدوران|المقياس)\s*=\s*متجه3\(([^,]+),\s*([^,]+),\s*([^\)]+)\)')
        re_prop_vec2 = re.compile(r'([^\.]+)\.(الموقع|المقياس)\s*=\s*متجه2\(([^,]+),\s*([^\)]+)\)')
        re_color = re.compile(r'([^\.]+)\.اللون\s*=\s*لون\(([^,]+),\s*([^,]+),\s*([^\)]+)\)')
        re_bool = re.compile(r'([^\.]+)\.(جاذبية|صدام|كامل_الشاشة)\s*=\s*(مفعل|مقفل)')
        re_show_col = re.compile(r'رؤية_صدام\((.+)\)')
        re_mat = re.compile(r'([^\.]+)\.الخامة\.([a-zA-Z_]+)\s*=\s*تحميل_خامة\("([^"]+)"\)')
        
        re_mat_vec = re.compile(r'([^\.]+)\.الخامة\.scale\.(x|y)\s*=\s*([-0-9.]+)')
        re_2d_image = re.compile(r'([^\.]+)\.الصورة\s*=\s*تحميل_صورة\("([^"]+)"\)')
        re_cam_num = re.compile(r'^الكاميرا\.(مجال_الرؤية|القطع_القريب|القطع_البعيد)\s*=\s*([0-9.-]+)$')
        re_sky_color = re.compile(r'صنع_سماء\(لون\(([^,]+),\s*([^,]+),\s*([^\)]+)\)\)')
        re_sky_cube = re.compile(r'صنع_سماء_cubemap\("([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"\)')
        re_light_type = re.compile(r'^([\w\[\]]+)\.النوع\s*=\s*["\'](ضوء_موجه|ضوء_نقطي|ضوء_بقعي)["\']$')
        re_light_dir = re.compile(r'^([\w\[\]]+)\.الاتجاه\s*=\s*متجه3\(([-0-9.]+),\s*([-0-9.]+),\s*([-0-9.]+)\)$')
        re_light_num = re.compile(r'^([\w\[\]]+)\.(الشدة|زاوية_البقعة|حدة_البقعة)\s*=\s*([-0-9.]+)$')
        
        re_ui_parent = re.compile(r'^([\w\[\]]+)\.الواجهة\s*=\s*([\w\[\]]+)$')
        re_ui_text = re.compile(r'^([\w\[\]]+)\.النص\s*=\s*["\'](.*)["\']$')
        re_ui_size = re.compile(r'^([\w\[\]]+)\.الحجم\s*=\s*العرض_والطول\(([-0-9.]+),\s*([-0-9.]+)\)$')
        re_ui_color = re.compile(r'^([\w\[\]]+)\.(لون_الخلفية|لون_النص)\s*=\s*لون\(([^,]+),\s*([^,]+),\s*([^\)]+)\)$')
        re_ui_alpha = re.compile(r'^([\w\[\]]+)\.شفافية_الخلفية\s*=\s*([-0-9.]+)$')
        
        obj_dict = {}
        for obj in new_objects:
            obj_dict[obj.name] = obj
            
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Match creations
            m = re_create.match(line)
            if m:
                name = m.group(1).strip()
                func = m.group(2).strip()
                args = m.group(3).strip().strip('"').strip("'")
                
                obj_type = "generic"
                if "صنع_مكعب" in func: obj_type = "Cube"
                elif "صنع_كرة" in func: obj_type = "Sphere"
                elif "صنع_سطح" in func: obj_type = "Plane"
                elif "صنع_تضاريس" in func: obj_type = "Terrain"
                elif "صنع_هرم" in func: obj_type = "Pyramid"
                elif "صنع_اسطوانة" in func: obj_type = "Cylinder"
                elif "صنع_كبسولة" in func: obj_type = "Capsule"
                elif "صنع_مربع2D" in func: obj_type = "Square2D"
                elif "صنع_دائرة2D" in func: obj_type = "Circle2D"
                elif "صنع_مثلث2D" in func: obj_type = "Triangle2D"
                elif "صنع_مخصص2D" in func: obj_type = "Custom2D"
                elif "صنع_مخصص" in func: obj_type = "CustomModel"
                elif "صنع_صوت" in func: obj_type = "Sound"
                elif "صنع_ضوء" in func: obj_type = "light"
                elif "صنع_واجهة" in func: obj_type = "Canvas"
                elif "اضافة_زر" in func or "صنع_زر" in func: obj_type = "Button"
                elif "اضافة_نص" in func or "صنع_نص" in func: obj_type = "Text"
                elif "صنع_fbx" in func.lower(): obj_type = "FBXModel"
                
                obj = SceneObject(name, obj_type=obj_type)
                obj.label = name
                
                if "." in func and obj_type in ("Button", "Text"):
                    parts = func.split(".")
                    obj.parent_name = parts[0].strip()
                    
                if args:
                    obj.filepath = args
                    
                if obj.obj_type == "Terrain" and obj.filepath:
                    try:
                        import terrain
                        full_path = os.path.join(project_dir, obj.filepath)
                        scale_x, scale_z, grid_size, heightmap = terrain.load_terrain_data(full_path)
                        obj.grid_size = grid_size
                        obj.heightmap = heightmap
                        # The scale will be overwritten by re_prop_vec3 if present in code,
                        # but we can set the default scale from the file just in case.
                        obj.scale = [scale_x, 1.0, scale_z]
                    except Exception as e:
                        print("Error loading terrain data in code_reader:", e)
                        
                new_objects.append(obj)
                obj_dict[name] = obj
                continue
                
            m = re_sky_color.match(line)
            if m:
                r, g, b = float(m.group(1)), float(m.group(2)), float(m.group(3))
                # القيم محفوظة بين 0.0-1.0 مباشرة، لا نقسم على 255
                if r > 1.0 or g > 1.0 or b > 1.0:
                    scene_viewer.sky_color = [r/255.0, g/255.0, b/255.0]
                else:
                    scene_viewer.sky_color = [r, g, b]
                continue
                
            m = re_sky_cube.match(line)
            if m:
                class DummyCubemap:
                    pass
                c = DummyCubemap()
                c.right = m.group(1)
                c.left = m.group(2)
                c.top = m.group(3)
                c.bottom = m.group(4)
                c.front = m.group(5)
                c.back = m.group(6)
                scene_viewer.sky_cubemap = c
                continue
                
            m = re_cam_num.match(line)
            if m:
                prop = m.group(1)
                val = float(m.group(2))
                if prop == "مجال_الرؤية": camera_obj.fov = val
                elif prop == "القطع_القريب": camera_obj.near_clip = val
                elif prop == "القطع_البعيد": camera_obj.far_clip = val
                continue
                
            m = re_ui_parent.match(line)
            if m:
                name = m.group(1).strip()
                pname = m.group(2).strip()
                if name in obj_dict:
                    obj_dict[name].parent_name = pname
                continue
                
            m = re_ui_text.match(line)
            if m:
                name = m.group(1).strip()
                val = m.group(2)
                if name in obj_dict:
                    obj_dict[name].ui_text = val
                continue
                
            m = re_ui_size.match(line)
            if m:
                name = m.group(1).strip()
                w = float(m.group(2))
                h = float(m.group(3))
                if name in obj_dict:
                    obj_dict[name].ui_width = w
                    obj_dict[name].ui_height = h
                continue
                
            m = re_ui_color.match(line)
            if m:
                name = m.group(1).strip()
                prop = m.group(2)
                r, g, b = float(m.group(3)), float(m.group(4)), float(m.group(5))
                if name in obj_dict:
                    if prop == "لون_الخلفية":
                        a = obj_dict[name].ui_bg_color[3] if hasattr(obj_dict[name], 'ui_bg_color') and len(obj_dict[name].ui_bg_color) > 3 else 1.0
                        obj_dict[name].ui_bg_color = [r, g, b, a]
                    elif prop == "لون_النص":
                        a = obj_dict[name].ui_text_color[3] if hasattr(obj_dict[name], 'ui_text_color') and len(obj_dict[name].ui_text_color) > 3 else 1.0
                        obj_dict[name].ui_text_color = [r, g, b, a]
                continue
                
            m = re_ui_alpha.match(line)
            if m:
                name = m.group(1).strip()
                val = float(m.group(2))
                if name in obj_dict:
                    c = getattr(obj_dict[name], 'ui_bg_color', [0,0,0,0])
                    obj_dict[name].ui_bg_color = [c[0], c[1], c[2], val]
                continue
                
            m = re_prop_vec3.search(line)
            if m:
                name = m.group(1).strip()
                prop = m.group(2)
                x, y, z = float(m.group(3)), float(m.group(4)), float(m.group(5))
                if name in obj_dict:
                    obj = obj_dict[name]
                    if prop == "الموقع": obj.pos = [x, y, z]
                    elif prop == "الدوران": obj.rot = [x, y, z]
                    elif prop == "المقياس": obj.scale = [x, y, z]
                continue
                
            m = re_prop_vec2.search(line)
            if m:
                name = m.group(1).strip()
                prop = m.group(2)
                x, y = float(m.group(3)), float(m.group(4))
                if name in obj_dict:
                    obj = obj_dict[name]
                    if prop == "الموقع": obj.pos = [x, y, getattr(obj, "pos", [0,0,0])[2]]
                    elif prop == "المقياس":
                        obj.ui_width = x
                        obj.ui_height = y
                continue

            m = re_light_dir.search(line)
            if m:
                name = m.group(1).strip()
                x, y, z = float(m.group(2)), float(m.group(3)), float(m.group(4))
                if name in obj_dict:
                    obj = obj_dict[name]
                    obj.light_direction = [x, y, z]
                continue

            m = re_light_type.search(line)
            if m:
                name = m.group(1).strip()
                ltype = m.group(2).strip()
                if name in obj_dict:
                    obj_dict[name].light_type = ltype
                continue

            m = re_light_num.search(line)
            if m:
                name = m.group(1).strip()
                prop = m.group(2)
                val = float(m.group(3))
                if name in obj_dict:
                    obj = obj_dict[name]
                    if prop == "الشدة": obj.light_intensity = val
                    elif prop == "زاوية_البقعة": obj.spot_angle = val
                    elif prop == "حدة_البقعة": obj.spot_sharpness = val
                continue
                
            m = re_color.search(line)
            if m:
                name = m.group(1).strip()
                r, g, b = float(m.group(2)), float(m.group(3)), float(m.group(4))
                if name in obj_dict:
                    obj = obj_dict[name]
                    # القيم في الملف بين 0.0-1.0 مباشرة
                    if r > 1.0 or g > 1.0 or b > 1.0:
                        obj.color = [r/255.0, g/255.0, b/255.0]
                    else:
                        obj.color = [r, g, b]
                continue
                
            m = re_show_col.search(line)
            if m:
                name = m.group(1).strip()
                if name in obj_dict:
                    obj = obj_dict[name]
                    obj.show_collision = True
                continue
                
            m = re_bool.search(line)
            if m:
                name = m.group(1).strip()
                prop = m.group(2)
                val = (m.group(3) == "مفعل")
                if name in obj_dict:
                    obj = obj_dict[name]
                    if prop == "جاذبية": obj.gravity = val
                    elif prop == "صدام": obj.bounciness = val
                    elif prop == "كامل_الشاشة": obj.ui_full_screen = val
                continue
                

                
            m = re_mat.search(line)
            if m:
                name = m.group(1).strip()
                key = m.group(2)
                path = m.group(3)
                if name in obj_dict:
                    obj = obj_dict[name]
                    if not isinstance(getattr(obj, 'material', None), dict):
                        obj.material = {}
                    obj.material[key] = path
                continue
            
            m = getattr(re, "compile", None) # dummy
            if False: pass # dummy to match structure just in case
            
            mat_vec_m = re_mat_vec.search(line)
            if mat_vec_m:
                obj_name, comp, val = mat_vec_m.groups()
                obj = obj_dict.get(obj_name.strip())
                if obj:
                    if not isinstance(getattr(obj, 'material', None), dict):
                        obj.material = {}
                    obj.material[f"scale_{comp}"] = float(val)
                continue
            
            m = re_2d_image.search(line)
            if m:
                name = m.group(1).strip()
                path = m.group(2)
                if name in obj_dict:
                    obj_dict[name].filepath = path
                continue
                
        scene_viewer.objects = new_objects
        scene_viewer.selected_obj = None
        
    except Exception as e:
        print(f"Error reading mainscene.khscene: {e}")
