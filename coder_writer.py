import os
import stat

def write_scene_to_kh(scene_viewer, project_dir):
    open("writer_log.txt", "a", encoding="utf-8").write(f"write_scene_to_kh called with {len(scene_viewer.objects)} objects. project_dir: {project_dir}\n")
    if not project_dir:
        return
        
    scene_file = os.path.join(project_dir, "mainscene.khscene")
    if not os.path.exists(scene_file):
        pass

    try:
        # Unlock file for writing
        os.chmod(scene_file, stat.S_IWRITE)
    except Exception:
        pass

    try:
        with open(scene_file, 'w', encoding='utf-8') as f:
            lines = []
            
            # إعدادات الماوس الافتراضية
            lines.append("ماوس.معلق = مقفل")
            lines.append("")
            
            # Scene properties (sky)
            def convert_color(val):
                if val > 1.0: return round(val / 255.0, 3)
                return round(val, 3)

            if hasattr(scene_viewer, 'sky_color') and scene_viewer.sky_color:
                c = scene_viewer.sky_color
                if c[0] < 0.01 and c[1] < 0.01 and c[2] < 0.01:
                    c = [0.15, 0.15, 0.15]
                r, g, b = convert_color(c[0]), convert_color(c[1]), convert_color(c[2])
                lines.append(f"صنع_سماء(لون({r}, {g}, {b}))")
            else:
                lines.append(f"صنع_سماء(لون(0.15, 0.15, 0.15))")
            
            if hasattr(scene_viewer, 'sky_cubemap') and scene_viewer.sky_cubemap:
                c = scene_viewer.sky_cubemap
                # يدعم كلاً من dict و DummyCubemap object
                if isinstance(c, dict):
                    right = c.get("right", "")
                    left  = c.get("left", "")
                    top   = c.get("top", "")
                    bot   = c.get("bottom", "")
                    front = c.get("front", "")
                    back  = c.get("back", "")
                elif hasattr(c, 'right'):
                    right = getattr(c, 'right', '')
                    left  = getattr(c, 'left', '')
                    top   = getattr(c, 'top', '')
                    bot   = getattr(c, 'bottom', '')
                    front = getattr(c, 'front', '')
                    back  = getattr(c, 'back', '')
                else:
                    right = left = top = bot = front = back = ""
                lines.append(f'صنع_سماء_cubemap("{right}", "{left}", "{top}", "{bot}", "{front}", "{back}")')
                
            lines.append("")

            for obj in scene_viewer.objects:
                if obj.obj_type == "camera":
                    name = "الكاميرا"
                    px, py, pz = obj.pos
                    rx, ry, rz = obj.rot
                    lines.append(f"{name}.الموقع = متجه3({px}, {py}, {pz})")
                    lines.append(f"{name}.الدوران = متجه3({rx}, {ry}, {rz})")
                    if hasattr(obj, 'fov'):
                        lines.append(f"{name}.مجال_الرؤية = {obj.fov}")
                    if hasattr(obj, 'near_clip'):
                        lines.append(f"{name}.القطع_القريب = {obj.near_clip}")
                    if hasattr(obj, 'far_clip'):
                        lines.append(f"{name}.القطع_البعيد = {obj.far_clip}")
                    lines.append("")
                    continue

                if obj.obj_type == "المشهد":
                    continue
                    
                name = obj.name
                
                # Determine creation command
                if obj.obj_type == "Cube": cmd = "صنع_مكعب()"
                elif obj.obj_type == "Sphere": cmd = "صنع_كرة()"
                elif obj.obj_type == "Plane": cmd = "صنع_سطح()"
                elif obj.obj_type == "Terrain":
                    fp = getattr(obj, "filepath", "").replace('\\', '/')
                    cmd = f'صنع_تضاريس("{fp}")'
                elif obj.obj_type == "Pyramid": cmd = "صنع_هرم()"
                elif obj.obj_type == "Cylinder": cmd = "صنع_اسطوانة()"
                elif obj.obj_type == "Capsule": cmd = "صنع_كبسولة()"
                elif obj.obj_type == "Square2D": cmd = "صنع_مربع2D()"
                elif obj.obj_type == "Circle2D": cmd = "صنع_دائرة2D()"
                elif obj.obj_type == "Triangle2D": cmd = "صنع_مثلث2D()"
                elif obj.obj_type == "CustomModel": 
                    fp = getattr(obj, "filepath", "").replace('\\', '/')
                    cmd = f'صنع_مخصص("{fp}")'
                elif obj.obj_type == "Custom2D": 
                    fp = getattr(obj, "filepath", "").replace('\\', '/')
                    cmd = f'صنع_مخصص2D("{fp}")'
                elif obj.obj_type == "Sound": 
                    fp = getattr(obj, "filepath", "").replace('\\', '/')
                    cmd = f'صنع_صوت("{fp}")'
                elif obj.obj_type == "light":
                    cmd = "صنع_ضوء()"
                elif obj.obj_type == "Canvas":
                    cmd = "صنع_واجهة()"
                elif obj.obj_type in ("Button", "Text"):
                    utext = getattr(obj, "ui_text", "")
                    pname = getattr(obj, "parent_name", "")
                    if not pname:
                        for o in objects:
                            if o.obj_type == "Canvas":
                                pname = o.name
                                obj.parent_name = pname
                                break
                    if not pname:
                        pname = "واجهة_افتراضية"
                        
                    func = "اضافة_زر" if obj.obj_type == "Button" else "اضافة_نص"
                    cmd = f'{pname}.{func}("{utext}")'
                else:
                    cmd = "فارغ"
                    
                lines.append(f"ابغا {name} = {cmd}")
                if obj.obj_type in ("Square2D", "Circle2D", "Triangle2D", "Custom2D"):
                    lines.append(f"{name}.مساحة_الشاشة = مقفل")
                
                if obj.obj_type != "Sound":
                    # Basic Transform
                    px, py, pz = obj.pos
                    lines.append(f"{name}.الموقع = متجه3({px}, {py}, {pz})")
                    
                    if obj.obj_type != "light":
                        rx, ry, rz = obj.rot
                        sx, sy, sz = obj.scale
                        lines.append(f"{name}.الدوران = متجه3({rx}, {ry}, {rz})")
                        lines.append(f"{name}.المقياس = متجه3({sx}, {sy}, {sz})")
                    
                    # Colors
                    if hasattr(obj, 'color') and obj.color:
                        c = obj.color
                        r, g, b = convert_color(c[0]), convert_color(c[1]), convert_color(c[2])
                        lines.append(f"{name}.اللون = لون({r}, {g}, {b})")
                    
                    # Light-specific properties
                    if obj.obj_type == "light":
                        ltype = getattr(obj, 'light_type', 'ضوء_موجه')
                        lines.append(f'{name}.النوع = "{ltype}"')
                        intensity = getattr(obj, 'light_intensity', 1.0)
                        lines.append(f"{name}.الشدة = {round(intensity, 3)}")
                        
                        if ltype in ('ضوء_موجه', 'ضوء_بقعي'):
                            ldir = getattr(obj, 'light_direction', [0.0, -1.0, 0.0])
                            dx, dy, dz = round(ldir[0], 3), round(ldir[1], 3), round(ldir[2], 3)
                            lines.append(f"{name}.الاتجاه = متجه3({dx}, {dy}, {dz})")
                            
                        if ltype == 'ضوء_بقعي':
                            sang = getattr(obj, 'spot_angle', 30.0)
                            ssharp = getattr(obj, 'spot_sharpness', 64.0)
                            lines.append(f"{name}.زاوية_البقعة = {round(sang, 3)}")
                            lines.append(f"{name}.حدة_البقعة = {round(ssharp, 3)}")
                    
                    # خصائص واجهة المستخدم UI
                    if obj.obj_type in ("Canvas", "Button", "Text"):
                        
                        if obj.obj_type == "Canvas":
                            fs = getattr(obj, "ui_full_screen", False)
                            lines.append(f'{name}.كامل_الشاشة = {"مفعل" if fs else "مقفل"}')
                        
                        w = getattr(obj, "ui_width", 0)
                        h = getattr(obj, "ui_height", 0)
                        lines.append(f'{name}.المقياس = متجه2({round(w,2)}, {round(h,2)})')
                        
                        pos = getattr(obj, "pos", [0, 0, 0])
                        lines.append(f'{name}.الموقع = متجه2({round(pos[0],2)}, {round(pos[1],2)})')
                        
                        align_h = getattr(obj, "ui_align_h", "وسط")
                        lines.append(f'{name}.افقي = "{align_h}"')
                        
                        align_v = getattr(obj, "ui_align_v", "وسط")
                        lines.append(f'{name}.عمودي = "{align_v}"')
                        
                        if obj.obj_type != "Canvas":
                            offset = getattr(obj, "ui_offset", [0, 0])
                            lines.append(f"{name}.ازاحة = متجه2({offset[0]}, {offset[1]})")
                        
                        font_size = getattr(obj, "ui_font_size", 14)
                        lines.append(f"{name}.حجم_الخط = {font_size}")
                        
                        if obj.obj_type == "Button":
                            if hasattr(obj, 'material') and isinstance(obj.material, dict):
                                base_mat = obj.material.get("base", "")
                                if base_mat:
                                    lines.append(f'{name}.الخامة = "{base_mat.replace(chr(92), "/")}"')
                        
                        bg_c = getattr(obj, "ui_bg_color", [1,1,1,1])
                        txt_c = getattr(obj, "ui_text_color", [0,0,0,1])
                        lines.append(f"{name}.لون_الخلفية = لون({round(bg_c[0],2)}, {round(bg_c[1],2)}, {round(bg_c[2],2)})")
                        lines.append(f"{name}.شفافية_الخلفية = {round(bg_c[3],2)}")
                        lines.append(f"{name}.لون_النص = لون({round(txt_c[0],2)}, {round(txt_c[1],2)}, {round(txt_c[2],2)})")
                    
                    # صورة الأشكال 2D
                    if obj.obj_type in ("Square2D", "Circle2D", "Triangle2D"):
                        fp = getattr(obj, "filepath", "")
                        if fp:
                            fp = fp.replace('\\', '/')
                            lines.append(f'{name}.الصورة = تحميل_صورة("{fp}")')
                        
                    # Collision and physics
                    if obj.obj_type != "light":
                        if hasattr(obj, 'show_collision') and obj.show_collision:
                            lines.append(f"رؤية_صدام({name})")
                            
                        if hasattr(obj, 'gravity') and obj.gravity:
                            lines.append(f"{name}.جاذبية = مفعل")
                        if hasattr(obj, 'bounciness') and obj.bounciness:
                            lines.append(f"{name}.صدام = مفعل")
                    
                # Material
                if hasattr(obj, 'material') and isinstance(obj.material, dict):
                    if obj.material.get("base"):
                        fp = obj.material["base"].replace('\\', '/')
                        lines.append(f'{name}.الخامة.base = تحميل_خامة("{fp}")')
                    if obj.material.get("normal"):
                        fp = obj.material["normal"].replace('\\', '/')
                        lines.append(f'{name}.الخامة.normal = تحميل_خامة("{fp}")')
                    if obj.material.get("metallic") is not None and str(obj.material["metallic"]).strip() != "":
                        val = obj.material["metallic"]
                        try:
                            val = float(val)
                            lines.append(f'{name}.الخامة.metallic = {val}')
                        except:
                            fp = str(val).replace('\\', '/')
                            lines.append(f'{name}.الخامة.metallic = تحميل_خامة("{fp}")')
                    if obj.material.get("roughness") is not None and str(obj.material["roughness"]).strip() != "":
                        val = obj.material["roughness"]
                        try:
                            val = float(val)
                            lines.append(f'{name}.الخامة.roughness = {val}')
                        except:
                            fp = str(val).replace('\\', '/')
                            lines.append(f'{name}.الخامة.roughness = تحميل_خامة("{fp}")')
                    if obj.material.get("ac") is not None and str(obj.material["ac"]).strip() != "":
                        fp = str(obj.material["ac"]).replace('\\', '/')
                        lines.append(f'{name}.الخامة.ac = تحميل_خامة("{fp}")')
                    
                    for k in ["scale_x", "scale_y"]:
                        if obj.material.get(k) is not None and str(obj.material[k]).strip() != "":
                            prop_name = k.replace("_", ".") # scale_x -> scale.x
                            lines.append(f'{name}.الخامة.{prop_name} = {float(obj.material[k])}')
                        
                lines.append("")
                
            f.write("\n".join(lines))
    except Exception as e:
        import traceback
        open("writer_error.log", "w", encoding="utf-8").write(traceback.format_exc())
        print(f"Error writing to mainscene.khscene: {e}")

    try:
        # Lock file back
        os.chmod(scene_file, stat.S_IREAD)
    except Exception:
        pass
